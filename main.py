"""
SmartLinks FastAPI Backend - Production Version
AI-Enhanced Go Links Tool
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from contextlib import asynccontextmanager
import validators
import re
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from models import (
    get_db, Link, Click, User,
    LinkCreate, LinkUpdate, LinkResponse,
    ClickCreate, ClickResponse, LinkStats,
    init_db
)

# Load environment variables
load_dotenv()

# Determine which AI module to use
USE_MOCK_AI = os.getenv("USE_MOCK_AI", "True").lower() == "true"
if USE_MOCK_AI:
    from mock_ai import analyze_url, suggest_keywords, test_ai_connection
else:
    from ai import analyze_url, suggest_keywords, test_ai_connection

# Production configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("🚀 SmartLinks API started successfully!")
    print(f"🌍 Environment: {ENVIRONMENT}")
    print(f"🤖 AI Mode: {'Mock' if USE_MOCK_AI else 'OpenAI'}")
    yield
    # Shutdown
    print("👋 SmartLinks API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="SmartLinks API",
    description="AI-Enhanced Go Links Tool for Teams",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,  # Hide docs in production
    redoc_url="/redoc" if DEBUG else None
)

# Security middleware
if ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility functions
def is_valid_keyword(keyword: str) -> bool:
    """Validate keyword format - alphanumeric, hyphens, underscores only"""
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, keyword)) and len(keyword) >= 2 and len(keyword) <= 50


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


# Health check endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "SmartLinks API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "ai_mode": "Mock" if USE_MOCK_AI else "OpenAI",
        "status": "running"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring"""
    try:
        link_count = db.query(Link).count()
        return {
            "status": "healthy",
            "database": "connected",
            "total_links": link_count,
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "environment": ENVIRONMENT
            }
        )


# Core URL Shortening Functionality
@app.post("/api/links", response_model=LinkResponse)
async def create_link(
        link_data: LinkCreate,
        request: Request,
        db: Session = Depends(get_db)
):
    """Create a new go link"""

    # Validate keyword format
    if not is_valid_keyword(link_data.keyword):
        raise HTTPException(
            status_code=400,
            detail="Keyword must be 2-50 characters, alphanumeric, hyphens and underscores only"
        )

    # Check if keyword already exists
    existing_link = db.query(Link).filter(Link.keyword == link_data.keyword).first()
    if existing_link:
        raise HTTPException(
            status_code=409,
            detail=f"Keyword '{link_data.keyword}' already exists"
        )

    # Validate URL
    url_str = str(link_data.url)
    if not validators.url(url_str):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL format"
        )

    # Create new link
    db_link = Link(
        keyword=link_data.keyword,
        url=url_str,
        title=link_data.title,
        description=link_data.description,
        category=link_data.category,
        created_by=get_client_ip(request)
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    response_link = LinkResponse.model_validate(db_link)
    response_link.click_count = 0

    return response_link


@app.get("/go/{keyword}")
async def redirect_link(
        keyword: str,
        request: Request,
        db: Session = Depends(get_db)
):
    """Redirect go/keyword to target URL and track click"""

    link = db.query(Link).filter(
        Link.keyword == keyword,
        Link.is_active == True
    ).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Link 'go/{keyword}' not found"
        )

    # Track the click
    click = Click(
        link_id=link.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        referrer=request.headers.get("referer", "")
    )

    db.add(click)
    db.commit()

    return RedirectResponse(url=link.url, status_code=302)


@app.get("/api/links", response_model=List[LinkResponse])
async def get_links(
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Get all links with optional filtering"""

    query = db.query(Link).filter(Link.is_active == True)

    if category:
        query = query.filter(Link.category == category)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Link.keyword.like(search_term)) |
            (Link.title.like(search_term)) |
            (Link.description.like(search_term))
        )

    links = query.limit(limit).all()

    response_links = []
    for link in links:
        click_count = db.query(Click).filter(Click.link_id == link.id).count()
        response_link = LinkResponse.model_validate(link)
        response_link.click_count = click_count
        response_links.append(response_link)

    return response_links


@app.get("/api/analytics/stats", response_model=LinkStats)
async def get_analytics_stats(db: Session = Depends(get_db)):
    """Get analytics overview"""

    total_links = db.query(Link).filter(Link.is_active == True).count()
    total_clicks = db.query(Click).count()

    # Top links by clicks (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    top_links_query = db.query(
        Link.keyword,
        Link.title,
        func.count(Click.id).label("click_count")
    ).join(Click).filter(
        Link.is_active == True,
        Click.clicked_at >= thirty_days_ago
    ).group_by(Link.id).order_by(desc("click_count")).limit(10)

    top_links = [
        {
            "keyword": row.keyword,
            "title": row.title or row.keyword,
            "clicks": row.click_count
        }
        for row in top_links_query.all()
    ]

    # Recent clicks (last 10)
    recent_clicks_query = db.query(Click, Link).join(Link).filter(
        Link.is_active == True
    ).order_by(desc(Click.clicked_at)).limit(10)

    recent_clicks = [
        {
            "keyword": row.Link.keyword,
            "title": row.Link.title or row.Link.keyword,
            "clicked_at": row.Click.clicked_at.isoformat(),
            "ip_address": row.Click.ip_address
        }
        for row in recent_clicks_query.all()
    ]

    # Categories breakdown
    categories_query = db.query(
        Link.category,
        func.count(Link.id).label("count")
    ).filter(Link.is_active == True).group_by(Link.category)

    categories = [
        {
            "category": row.category,
            "count": row.count
        }
        for row in categories_query.all()
    ]

    return LinkStats(
        total_links=total_links,
        total_clicks=total_clicks,
        top_links=top_links,
        recent_clicks=recent_clicks,
        categories=categories
    )


# AI Endpoints (if enabled)
@app.post("/api/ai/analyze-url")
async def ai_analyze_url(request: dict):
    """Analyze URL with AI to get suggestions"""
    url = request.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    try:
        analysis = await analyze_url(url)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/ai/test")
async def test_ai():
    """Test AI connectivity"""
    result = test_ai_connection()

    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {result['error']}")


# Development endpoints (only in development)
if DEBUG:
    @app.get("/api/dev/sample-links")
    async def create_sample_links(db: Session = Depends(get_db)):
        """Create sample links for testing"""

        sample_links = [
            {
                "keyword": "meet",
                "url": "https://meet.google.com",
                "title": "Google Meet",
                "description": "Video conferencing",
                "category": "Communication"
            },
            {
                "keyword": "drive",
                "url": "https://drive.google.com",
                "title": "Google Drive",
                "description": "Cloud storage",
                "category": "Productivity"
            },
            {
                "keyword": "calendar",
                "url": "https://calendar.google.com",
                "title": "Google Calendar",
                "description": "Calendar and scheduling",
                "category": "Productivity"
            }
        ]

        created_links = []
        for link_data in sample_links:
            existing = db.query(Link).filter(Link.keyword == link_data["keyword"]).first()
            if not existing:
                db_link = Link(**link_data)
                db.add(db_link)
                created_links.append(link_data["keyword"])

        db.commit()

        return {
            "message": f"Created {len(created_links)} sample links",
            "created": created_links
        }


# Production error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"message": "Resource not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "environment": ENVIRONMENT}
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_production:app", host="0.0.0.0", port=port, reload=DEBUG)