"""
Database models for SmartLinks
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import os

# Database setup
DATABASE_URL = "sqlite:///./smartlinks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy Models (Database)
class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), unique=True, index=True, nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(200))
    description = Column(Text)
    category = Column(String(50), default="General")
    created_by = Column(String(100), default="anonymous")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationship to clicks
    clicks = relationship("Click", back_populates="link")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    clicked_at = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer = Column(Text)

    # Relationship to link
    link = relationship("Link", back_populates="clicks")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100))
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models (API)
class LinkBase(BaseModel):
    keyword: str
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "General"


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class LinkResponse(LinkBase):
    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    click_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ClickCreate(BaseModel):
    link_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None


class ClickResponse(BaseModel):
    id: int
    link_id: int
    clicked_at: datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    role: Optional[str] = "user"


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class LinkStats(BaseModel):
    total_links: int
    total_clicks: int
    top_links: List[dict]
    recent_clicks: List[dict]
    categories: List[dict]


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Initialize database with sample data
def init_db():
    create_tables()
    db = SessionLocal()

    # Check if we already have data
    existing_links = db.query(Link).count()
    if existing_links == 0:
        # Add sample links
        sample_links = [
            Link(
                keyword="github",
                url="https://github.com",
                title="GitHub",
                description="Code repository platform",
                category="Development"
            ),
            Link(
                keyword="docs",
                url="https://docs.google.com",
                title="Google Docs",
                description="Document creation and collaboration",
                category="Productivity"
            ),
            Link(
                keyword="slack",
                url="https://slack.com",
                title="Slack",
                description="Team communication platform",
                category="Communication"
            )
        ]

        for link in sample_links:
            db.add(link)

        db.commit()
        print("✅ Database initialized with sample data")

    db.close()