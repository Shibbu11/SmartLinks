"""
SmartLinks Streamlit Frontend - Fixed Version
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="SmartLinks",
    page_icon="🔗",
    layout="wide"
)

# Utility functions
def make_api_request(endpoint: str, method: str = "GET", data: Dict = None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)

        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_links():
    """Fetch all links from API"""
    result = make_api_request("/api/links")
    return result["data"] if result["success"] else []

def get_analytics():
    """Fetch analytics data from API"""
    result = make_api_request("/api/analytics/stats")
    return result["data"] if result["success"] else {}

# Main app
st.title("🔗 SmartLinks")
st.markdown("AI-Enhanced Go Links for Your Team")

# Check API connection
health_result = make_api_request("/health")
if not health_result["success"]:
    st.error("⚠️ Cannot connect to SmartLinks API. Make sure the backend is running on http://localhost:8000")
    st.stop()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page",
    ["Dashboard", "Create Link", "Manage Links", "Analytics"]
)

# Dashboard Page
if page == "Dashboard":
    st.header("📊 Dashboard")

    analytics = get_analytics()

    if analytics:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Links", analytics.get("total_links", 0))

        with col2:
            st.metric("Total Clicks", analytics.get("total_clicks", 0))

        with col3:
            avg_clicks = analytics.get("total_clicks", 0) / max(analytics.get("total_links", 1), 1)
            st.metric("Avg Clicks/Link", f"{avg_clicks:.1f}")

        with col4:
            categories_count = len(analytics.get("categories", []))
            st.metric("Categories", categories_count)

        # Recent activity and top links
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔥 Top Links (Last 30 Days)")
            top_links = analytics.get("top_links", [])
            if top_links:
                for link in top_links[:5]:
                    st.write(f"**go/{link['keyword']}** - {link.get('title', link['keyword'])} ({link['clicks']} clicks)")
            else:
                st.info("No click data available yet")

        with col2:
            st.subheader("⏰ Recent Activity")
            recent_clicks = analytics.get("recent_clicks", [])
            if recent_clicks:
                for click in recent_clicks[:5]:
                    st.write(f"**go/{click['keyword']}** - {click.get('title', click['keyword'])}")
            else:
                st.info("No recent activity")

# Create Link Page
elif page == "Create Link":
    st.header("✨ Create New Link")

    with st.form("create_link_form"):
        col1, col2 = st.columns(2)

        with col1:
            keyword = st.text_input("Keyword *", placeholder="e.g., github, docs, meeting")
            url = st.text_input("Target URL *", placeholder="https://example.com")

        with col2:
            title = st.text_input("Title", placeholder="GitHub Repository")
            category = st.selectbox("Category",
                ["General", "Development", "Productivity", "Communication", "HR", "Marketing", "Finance"])

        description = st.text_area("Description", placeholder="Optional description")

        submitted = st.form_submit_button("Create Link", type="primary")

        if submitted:
            if not keyword or not url:
                st.error("❌ Keyword and URL are required")
            else:
                link_data = {
                    "keyword": keyword.lower().strip(),
                    "url": url.strip(),
                    "title": title.strip() if title else None,
                    "description": description.strip() if description else None,
                    "category": category
                }

                result = make_api_request("/api/links", method="POST", data=link_data)

                if result["success"]:
                    st.success(f"✅ Successfully created go/{keyword}!")
                    st.info(f"🔗 Test your link: http://localhost:8000/go/{keyword}")
                else:
                    if "409" in str(result["error"]):
                        st.error(f"❌ Keyword '{keyword}' already exists. Please choose a different one.")
                    else:
                        st.error(f"❌ Failed to create link: {result['error']}")

# Manage Links Page
elif page == "Manage Links":
    st.header("🔧 Manage Links")

    # Search controls
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Search keywords, titles...")
    with col2:
        st.write("")  # Spacer
        if st.button("🔄 Refresh"):
            st.rerun()

    # Get and display links
    links = get_links()

    if not links:
        st.info("No links found. Create your first link!")
    else:
        # Filter links if search term provided
        if search_term:
            links = [
                link for link in links
                if search_term.lower() in link["keyword"].lower() or
                   search_term.lower() in (link.get("title", "")).lower()
            ]

        st.write(f"Found {len(links)} links")

        # Display links in a table format
        for link in links:
            with st.container():
                col1, col2, col3 = st.columns([4, 2, 1])

                with col1:
                    st.markdown(f"### go/{link['keyword']}")
                    st.write(f"**URL:** {link['url']}")
                    if link.get('title'):
                        st.write(f"**Title:** {link['title']}")
                    st.write(f"**Category:** {link['category']} | **Clicks:** {link.get('click_count', 0)}")

                with col2:
                    st.write(f"Created: {link['created_at'][:10]}")
                    if st.button(f"🔗 Test Link", key=f"test_{link['keyword']}"):
                        st.write(f"http://localhost:8000/go/{link['keyword']}")

                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{link['keyword']}", type="secondary"):
                        result = make_api_request(f"/api/links/{link['keyword']}", method="DELETE")
                        if result["success"]:
                            st.success(f"Deleted go/{link['keyword']}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete: {result['error']}")

                st.divider()

# Analytics Page
elif page == "Analytics":
    st.header("📊 Analytics Dashboard")

    analytics = get_analytics()

    if analytics:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Links", analytics.get("total_links", 0))
        with col2:
            st.metric("Total Clicks", analytics.get("total_clicks", 0))
        with col3:
            avg_clicks = analytics.get("total_clicks", 0) / max(analytics.get("total_links", 1), 1)
            st.metric("Avg Clicks/Link", f"{avg_clicks:.1f}")
        with col4:
            categories_count = len(analytics.get("categories", []))
            st.metric("Categories", categories_count)

        # Top performing links
        st.subheader("🏆 Top Performing Links")
        top_links = analytics.get("top_links", [])
        if top_links:
            df = pd.DataFrame(top_links)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No click data available")

        # Category breakdown
        st.subheader("📋 Category Breakdown")
        categories = analytics.get("categories", [])
        if categories:
            df = pd.DataFrame(categories)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No category data available")

        # Recent activity
        st.subheader("🕒 Recent Activity")
        recent_clicks = analytics.get("recent_clicks", [])
        if recent_clicks:
            df = pd.DataFrame(recent_clicks)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent activity")
    else:
        st.error("Unable to load analytics data")

# Development tools in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Development Tools")

if st.sidebar.button("Create Sample Links"):
    result = make_api_request("/api/dev/sample-links")
    if result["success"]:
        st.sidebar.success("✅ Sample links created!")
    else:
        st.sidebar.error(f"❌ Error: {result['error']}")

if st.sidebar.button("Test API Connection"):
    health = make_api_request("/health")
    if health["success"]:
        st.sidebar.success("✅ API is healthy!")
        st.sidebar.json(health["data"])
    else:
        st.sidebar.error("❌ API connection failed")