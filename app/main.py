"""
SmartLinks FastAPI Backend
AI-Enhanced Go Links Tool
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from contextlib import asynccontextmanager
import validators
import re
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from models import (
    get_db, Link, Click, User,
    LinkCreate, LinkUpdate, LinkResponse,
    ClickCreate, ClickResponse, LinkStats,
    init_db
)
# Switch to mock AI for development (no API costs!)
from mock_ai import analyze_url, suggest_keywords, test_ai_connection

# Load environment variables
load_dotenv()

# Lifespan event handler (modern FastAPI approach)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("🚀 SmartLinks API started successfully!")
    yield
    # Shutdown (add cleanup code here if needed)
    print("👋 SmartLinks API shutting down...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="SmartLinks API",
    description="AI-Enhanced Go Links Tool for Teams",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
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

# API Routes

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "SmartLinks API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Simple DB connectivity test
        link_count = db.query(Link).count()
        return {
            "status": "healthy",
            "database": "connected",
            "total_links": link_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
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
        created_by=get_client_ip(request)  # Simple user tracking for MVP
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    # Add click count for response
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

    # Find the link
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

    # Redirect to target URL
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

    # Filter by category
    if category:
        query = query.filter(Link.category == category)

    # Search in keyword, title, description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Link.keyword.like(search_term)) |
            (Link.title.like(search_term)) |
            (Link.description.like(search_term))
        )

    # Get links with click counts
    links = query.limit(limit).all()

    # Add click counts
    response_links = []
    for link in links:
        click_count = db.query(Click).filter(Click.link_id == link.id).count()
        response_link = LinkResponse.model_validate(link)
        response_link.click_count = click_count
        response_links.append(response_link)

    return response_links

@app.get("/api/links/{keyword}", response_model=LinkResponse)
async def get_link(keyword: str, db: Session = Depends(get_db)):
    """Get specific link by keyword"""

    link = db.query(Link).filter(
        Link.keyword == keyword,
        Link.is_active == True
    ).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Link '{keyword}' not found"
        )

    # Add click count
    click_count = db.query(Click).filter(Click.link_id == link.id).count()
    response_link = LinkResponse.model_validate(link)
    response_link.click_count = click_count

    return response_link

@app.put("/api/links/{keyword}", response_model=LinkResponse)
async def update_link(
    keyword: str,
    link_update: LinkUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing link"""

    link = db.query(Link).filter(
        Link.keyword == keyword,
        Link.is_active == True
    ).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Link '{keyword}' not found"
        )

    # Update fields
    if link_update.url:
        url_str = str(link_update.url)
        if not validators.url(url_str):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        link.url = url_str

    if link_update.title is not None:
        link.title = link_update.title

    if link_update.description is not None:
        link.description = link_update.description

    if link_update.category is not None:
        link.category = link_update.category

    link.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(link)

    # Add click count
    click_count = db.query(Click).filter(Click.link_id == link.id).count()
    response_link = LinkResponse.model_validate(link)
    response_link.click_count = click_count

    return response_link

@app.delete("/api/links/{keyword}")
async def delete_link(keyword: str, db: Session = Depends(get_db)):
    """Soft delete a link (mark as inactive)"""

    link = db.query(Link).filter(
        Link.keyword == keyword,
        Link.is_active == True
    ).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Link '{keyword}' not found"
        )

    link.is_active = False
    link.updated_at = datetime.utcnow()

    db.commit()

    return {"message": f"Link '{keyword}' deleted successfully"}

# Analytics Endpoints

@app.get("/api/analytics/stats", response_model=LinkStats)
async def get_analytics_stats(db: Session = Depends(get_db)):
    """Get analytics overview"""

    # Basic stats
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

@app.get("/api/links/{keyword}/analytics")
async def get_link_analytics(keyword: str, db: Session = Depends(get_db)):
    """Get detailed analytics for a specific link"""

    link = db.query(Link).filter(
        Link.keyword == keyword,
        Link.is_active == True
    ).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Link '{keyword}' not found"
        )

    # Click analytics
    total_clicks = db.query(Click).filter(Click.link_id == link.id).count()

    # Clicks over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    clicks_over_time = db.query(
        func.date(Click.clicked_at).label("date"),
        func.count(Click.id).label("clicks")
    ).filter(
        Click.link_id == link.id,
        Click.clicked_at >= thirty_days_ago
    ).group_by(func.date(Click.clicked_at)).all()

    return {
        "keyword": keyword,
        "total_clicks": total_clicks,
        "created_at": link.created_at.isoformat(),
        "clicks_over_time": [
            {
                "date": row.date.isoformat(),
                "clicks": row.clicks
            }
            for row in clicks_over_time
        ]
    }

# AI-Powered Endpoints

@app.post("/api/ai/analyze-url")
async def ai_analyze_url(request: dict):
    """Analyze URL with AI to get title, description, category and keyword suggestions"""
    url = request.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    # Get AI analysis
    analysis = await analyze_url(url)

    return analysis

@app.post("/api/ai/suggest-keywords")
async def ai_suggest_keywords(request: dict, db: Session = Depends(get_db)):
    """Generate keyword suggestions from text"""
    text = request.get("text", "")

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    # Get existing keywords to avoid duplicates
    existing_keywords = [link.keyword for link in db.query(Link).all()]

    # Get AI suggestions
    suggestions = suggest_keywords(text, existing_keywords)

    return {
        "suggestions": suggestions,
        "text_analyzed": text,
        "existing_keywords_avoided": len(existing_keywords)
    }

@app.post("/api/ai/smart-create")
async def ai_smart_create_link(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a link with AI assistance - analyzes URL and suggests everything"""
    url = request.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    # Get AI analysis
    analysis = await analyze_url(url)

    if not analysis.get("success"):
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {analysis.get('error')}")

    # Suggest a keyword from the AI keywords
    suggested_keywords = analysis.get("keywords", [])
    existing_keywords = [link.keyword for link in db.query(Link).all()]

    # Find first available keyword
    available_keyword = None
    for keyword in suggested_keywords:
        if keyword not in existing_keywords:
            available_keyword = keyword
            break

    if not available_keyword and suggested_keywords:
        # If all AI keywords are taken, try variations
        base_keyword = suggested_keywords[0]
        for i in range(2, 10):
            variant = f"{base_keyword}{i}"
            if variant not in existing_keywords:
                available_keyword = variant
                break

    return {
        "ai_analysis": analysis,
        "suggested_link": {
            "keyword": available_keyword,
            "url": url,
            "title": analysis.get("title"),
            "description": analysis.get("description"),
            "category": analysis.get("category")
        },
        "all_keyword_suggestions": suggested_keywords,
        "keyword_available": available_keyword is not None
    }

@app.get("/api/ai/test")
async def test_ai():
    """Test AI connectivity"""
    result = test_ai_connection()

    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {result['error']}")

# Enhanced link creation with optional AI
@app.post("/api/links/enhanced", response_model=LinkResponse)
async def create_enhanced_link(
    request: dict,
    db: Session = Depends(get_db)
):
    """Create link with optional AI enhancement"""

    # Required fields
    keyword = request.get("keyword")
    url = request.get("url")

    # Optional AI enhancement
    use_ai = request.get("use_ai", False)

    if not keyword or not url:
        raise HTTPException(status_code=400, detail="Keyword and URL are required")

    # Validate keyword format
    if not is_valid_keyword(keyword):
        raise HTTPException(
            status_code=400,
            detail="Keyword must be 2-50 characters, alphanumeric, hyphens and underscores only"
        )

    # Check if keyword already exists
    existing_link = db.query(Link).filter(Link.keyword == keyword).first()
    if existing_link:
        raise HTTPException(
            status_code=409,
            detail=f"Keyword '{keyword}' already exists"
        )

    # Validate URL
    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    # Prepare link data
    link_data = {
        "keyword": keyword,
        "url": url,
        "title": request.get("title"),
        "description": request.get("description"),
        "category": request.get("category", "General")
    }

    # AI enhancement if requested
    if use_ai:
        try:
            analysis = await analyze_url(url)
            if analysis.get("success"):
                # Use AI data if user didn't provide their own
                if not link_data["title"]:
                    link_data["title"] = analysis.get("title")
                if not link_data["description"]:
                    link_data["description"] = analysis.get("description")
                if link_data["category"] == "General":
                    link_data["category"] = analysis.get("category", "General")
        except Exception as e:
            # Continue without AI if it fails
            pass

    # Create link
    db_link = Link(
        keyword=link_data["keyword"],
        url=link_data["url"],
        title=link_data["title"],
        description=link_data["description"],
        category=link_data["category"],
        created_by="api_user"  # TODO: Add proper user management
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    # Prepare response
    response_link = LinkResponse.model_validate(db_link)
    response_link.click_count = 0

    return response_link

@app.get("/api/analytics/trends")
async def get_analytics_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get click trends over time"""

    # Get clicks for the last N days
    start_date = datetime.utcnow() - timedelta(days=days)

    clicks_query = db.query(
        func.date(Click.clicked_at).label("date"),
        func.count(Click.id).label("clicks"),
        func.count(func.distinct(Click.link_id)).label("unique_links")
    ).filter(
        Click.clicked_at >= start_date
    ).group_by(func.date(Click.clicked_at)).order_by("date")

    daily_data = [
        {
            "date": row.date.isoformat(),
            "clicks": row.clicks,
            "unique_links": row.unique_links
        }
        for row in clicks_query.all()
    ]

    # Get hourly breakdown for today
    today = datetime.utcnow().date()
    hourly_query = db.query(
        func.extract('hour', Click.clicked_at).label("hour"),
        func.count(Click.id).label("clicks")
    ).filter(
        func.date(Click.clicked_at) == today
    ).group_by(func.extract('hour', Click.clicked_at))

    hourly_data = [
        {
            "hour": int(row.hour),
            "clicks": row.clicks
        }
        for row in hourly_query.all()
    ]

    return {
        "daily_trends": daily_data,
        "hourly_trends": hourly_data,
        "period_days": days,
        "total_period_clicks": sum(d["clicks"] for d in daily_data)
    }

@app.get("/api/analytics/performance")
async def get_performance_analytics(db: Session = Depends(get_db)):
    """Get detailed performance analytics"""

    # Top performers this week vs last week
    week_ago = datetime.utcnow() - timedelta(days=7)
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)

    # This week's performance
    this_week = db.query(
        Link.keyword,
        Link.title,
        func.count(Click.id).label("clicks")
    ).join(Click).filter(
        Click.clicked_at >= week_ago,
        Link.is_active == True
    ).group_by(Link.id).order_by(desc("clicks")).limit(10)

    # Last week's performance
    last_week = db.query(
        Link.keyword,
        Link.title,
        func.count(Click.id).label("clicks")
    ).join(Click).filter(
        Click.clicked_at >= two_weeks_ago,
        Click.clicked_at < week_ago,
        Link.is_active == True
    ).group_by(Link.id).order_by(desc("clicks")).limit(10)

    # Category performance
    category_performance = db.query(
        Link.category,
        func.count(func.distinct(Link.id)).label("total_links"),
        func.count(Click.id).label("total_clicks"),
        func.avg(func.count(Click.id)).label("avg_clicks_per_link")
    ).outerjoin(Click).filter(
        Link.is_active == True
    ).group_by(Link.category)

    return {
        "this_week_top": [
            {
                "keyword": row.keyword,
                "title": row.title,
                "clicks": row.clicks
            }
            for row in this_week.all()
        ],
        "last_week_top": [
            {
                "keyword": row.keyword,
                "title": row.title,
                "clicks": row.clicks
            }
            for row in last_week.all()
        ],
        "category_performance": [
            {
                "category": row.category,
                "total_links": row.total_links,
                "total_clicks": row.total_clicks or 0,
                "avg_clicks_per_link": float(row.avg_clicks_per_link or 0)
            }
            for row in category_performance.all()
        ]
    }

@app.get("/api/analytics/insights")
async def get_ai_insights(db: Session = Depends(get_db)):
    """Get AI-powered insights about link usage"""

    # Get basic stats
    total_links = db.query(Link).filter(Link.is_active == True).count()
    total_clicks = db.query(Click).count()

    # Get most active day
    most_active_day = db.query(
        func.date(Click.clicked_at).label("date"),
        func.count(Click.id).label("clicks")
    ).group_by(func.date(Click.clicked_at)).order_by(desc("clicks")).first()

    # Get most popular hour
    most_popular_hour = db.query(
        func.extract('hour', Click.clicked_at).label("hour"),
        func.count(Click.id).label("clicks")
    ).group_by(func.extract('hour', Click.clicked_at)).order_by(desc("clicks")).first()

    # Unused links (no clicks)
    unused_links = db.query(Link).outerjoin(Click).filter(
        Link.is_active == True,
        Click.id == None
    ).count()

    # Generate insights
    insights = []

    if total_clicks > 0:
        avg_clicks = total_clicks / total_links
        if avg_clicks > 5:
            insights.append({
                "type": "positive",
                "icon": "🎉",
                "title": "Great Engagement!",
                "message": f"Your links average {avg_clicks:.1f} clicks each - that's excellent adoption!"
            })
        elif avg_clicks < 1:
            insights.append({
                "type": "suggestion",
                "icon": "💡",
                "title": "Boost Usage",
                "message": "Consider promoting your go links in team channels or adding them to documentation."
            })

    if unused_links > 0:
        insights.append({
            "type": "warning",
            "icon": "⚠️",
            "title": "Unused Links",
            "message": f"You have {unused_links} links with no clicks. Consider removing or promoting them."
        })

    if most_popular_hour:
        hour = int(most_popular_hour.hour)
        if 9 <= hour <= 17:
            insights.append({
                "type": "info",
                "icon": "⏰",
                "title": "Peak Usage",
                "message": f"Most clicks happen at {hour}:00 - prime work hours!"
            })
        else:
            insights.append({
                "type": "info",
                "icon": "🌙",
                "title": "After Hours Activity",
                "message": f"Peak usage at {hour}:00 suggests flexible work schedules."
            })

    return {
        "insights": insights,
        "stats": {
            "total_links": total_links,
            "total_clicks": total_clicks,
            "avg_clicks_per_link": total_clicks / total_links if total_links > 0 else 0,
            "unused_links": unused_links,
            "most_active_day": most_active_day.date.isoformat() if most_active_day else None,
            "most_popular_hour": int(most_popular_hour.hour) if most_popular_hour else None
        }
    }

# Development helper endpoints
@app.get("/api/dev/sample-links")
async def create_sample_links(db: Session = Depends(get_db)):
    """Create sample links for testing (development only)"""

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
        # Check if already exists
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)