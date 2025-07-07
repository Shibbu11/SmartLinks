"""
SmartLinks Enhanced Dashboard - Working Version
Professional analytics and management interface
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict, List

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="SmartLinks Dashboard",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .status-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .link-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .ai-badge {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .category-tag {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# Utility functions
@st.cache_data(ttl=30)  # Cache for 30 seconds
def make_api_request(endpoint: str, method: str = "GET", data: Dict = None):
    """Cached API request function"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)

        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_links():
    """Fetch all links"""
    result = make_api_request("/api/links")
    return result["data"] if result["success"] else []


def get_analytics():
    """Fetch analytics data"""
    result = make_api_request("/api/analytics/stats")
    return result["data"] if result["success"] else {}


def check_api_health():
    """Check API health"""
    result = make_api_request("/health")
    return result


def show_analytics_dashboard():
    """Enhanced analytics dashboard with beautiful charts"""
    st.header("📈 Analytics Dashboard")

    analytics = get_analytics()
    if not analytics:
        st.error("Unable to load analytics data")
        return

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{analytics.get('total_links', 0)}</div>
            <div class="metric-label">Total Links</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{analytics.get('total_clicks', 0)}</div>
            <div class="metric-label">Total Clicks</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_clicks = analytics.get('total_clicks', 0) / max(analytics.get('total_links', 1), 1)
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{avg_clicks:.1f}</div>
            <div class="metric-label">Avg Clicks/Link</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        categories_count = len(analytics.get('categories', []))
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{categories_count}</div>
            <div class="metric-label">Categories</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("🏆 Top Performing Links")
        top_links = analytics.get("top_links", [])

        if top_links:
            # Create horizontal bar chart
            df = pd.DataFrame(top_links)
            fig = px.bar(
                df.head(10),
                x="clicks",
                y="keyword",
                orientation="h",
                title="Most Popular Links (Last 30 Days)",
                labels={"clicks": "Number of Clicks", "keyword": "Link Keyword"},
                color="clicks",
                color_continuous_scale="viridis"
            )
            fig.update_layout(
                height=400,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No click data available yet. Create some links and start using them!")

    with col2:
        st.subheader("📋 Category Distribution")
        categories = analytics.get("categories", [])

        if categories:
            df = pd.DataFrame(categories)
            fig = px.pie(
                df,
                values="count",
                names="category",
                title="Links by Category",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No category data available")

    # Recent Activity
    st.subheader("🕒 Recent Activity")
    recent_clicks = analytics.get("recent_clicks", [])

    if recent_clicks:
        # Create a timeline chart
        df = pd.DataFrame(recent_clicks)
        df['clicked_at'] = pd.to_datetime(df['clicked_at'])

        fig = px.scatter(
            df.head(20),
            x='clicked_at',
            y='keyword',
            size=[10] * len(df.head(20)),  # Fixed size
            color='keyword',
            title="Recent Link Clicks Timeline",
            labels={'clicked_at': 'Time', 'keyword': 'Link'}
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Recent activity table
        st.subheader("📋 Detailed Recent Activity")
        display_df = df[['keyword', 'title', 'clicked_at', 'ip_address']].head(10)
        display_df['clicked_at'] = display_df['clicked_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("🔍 No recent activity. Start clicking some links!")


def show_ai_link_creator():
    """AI-powered link creation interface"""
    st.header("✨ AI Link Creator")
    st.markdown("Let AI analyze your URL and suggest the perfect link details!")

    # URL Analysis Section
    st.subheader("🔍 Step 1: Analyze URL")

    col1, col2 = st.columns([3, 1])
    with col1:
        url_input = st.text_input(
            "Enter URL to analyze",
            placeholder="https://github.com/your-repo",
            help="AI will analyze this URL and suggest title, description, category, and keywords"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🤖 Analyze with AI", type="primary")

    # AI Analysis Results
    if analyze_btn and url_input:
        if not url_input.startswith(('http://', 'https://')):
            st.error("❌ Please enter a valid URL starting with http:// or https://")
        else:
            with st.spinner("🤖 AI is analyzing your URL..."):
                # Call actual API or use mock data
                result = make_api_request("/api/ai/analyze-url", method="POST", data={"url": url_input})

                if result["success"]:
                    ai_result = result["data"]
                    st.success("✅ AI Analysis Complete!")

                    # Show AI results in nice cards
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"""
                        <div class="link-card">
                            <h4>📝 Suggested Title</h4>
                            <p>{ai_result.get('title', 'No title found')}</p>
                            <span class="ai-badge">AI Suggested</span>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class="link-card">
                            <h4>📝 Suggested Description</h4>
                            <p>{ai_result.get('description', 'No description found')}</p>
                            <span class="ai-badge">AI Suggested</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="link-card">
                            <h4>🏷️ Suggested Category</h4>
                            <p><span class="category-tag">{ai_result.get('category', 'General')}</span></p>
                            <span class="ai-badge">AI Suggested</span>
                        </div>
                        """, unsafe_allow_html=True)

                        keywords = ai_result.get('keywords', [])
                        st.markdown(f"""
                        <div class="link-card">
                            <h4>🎯 Suggested Keywords</h4>
                            <p>{', '.join(keywords) if keywords else 'No keywords suggested'}</p>
                            <span class="ai-badge">AI Suggested</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # Store AI results in session state for form
                    st.session_state['ai_analysis'] = ai_result
                    st.session_state['analyzed_url'] = url_input
                else:
                    st.error(f"❌ AI analysis failed: {result.get('error', 'Unknown error')}")

    # Link Creation Form
    st.subheader("📝 Step 2: Create Link")

    with st.form("ai_create_link_form"):
        col1, col2 = st.columns(2)

        # Pre-fill with AI data if available
        ai_data = st.session_state.get('ai_analysis', {})
        analyzed_url = st.session_state.get('analyzed_url', '')

        with col1:
            keyword = st.text_input(
                "Keyword *",
                placeholder="github",
                help="Choose from AI suggestions or create your own"
            )

            if ai_data.get('keywords'):
                st.write("💡 **AI Suggested Keywords:**")
                keyword_options = ai_data['keywords'][:5]  # Show max 5
                for i, kw in enumerate(keyword_options):
                    if st.button(f"`{kw}`", key=f"kw_{i}"):
                        keyword = kw
                        st.rerun()

            url = st.text_input(
                "URL *",
                value=analyzed_url,
                placeholder="https://example.com"
            )

        with col2:
            title = st.text_input(
                "Title",
                value=ai_data.get('title', ''),
                placeholder="GitHub Repository"
            )

            categories = ["General", "Development", "Productivity", "Communication", "HR", "Marketing", "Finance"]
            default_category = ai_data.get('category', 'General')
            category_index = categories.index(default_category) if default_category in categories else 0

            category = st.selectbox(
                "Category",
                categories,
                index=category_index
            )

        description = st.text_area(
            "Description",
            value=ai_data.get('description', ''),
            placeholder="Platform for version control and collaboration"
        )

        # Enhanced creation options
        col1, col2 = st.columns(2)
        with col1:
            use_ai_enhancement = st.checkbox("🤖 Use AI Enhancement", value=True,
                                             help="Automatically improve title/description if empty")

        submitted = st.form_submit_button("🚀 Create Smart Link", type="primary")

        if submitted:
            if not keyword or not url:
                st.error("❌ Keyword and URL are required")
            else:
                # Create the link
                link_data = {
                    "keyword": keyword.lower().strip(),
                    "url": url.strip(),
                    "title": title.strip() if title else None,
                    "description": description.strip() if description else None,
                    "category": category,
                    "use_ai": use_ai_enhancement
                }

                # Use enhanced endpoint if AI features are enabled
                endpoint = "/api/links/enhanced" if use_ai_enhancement else "/api/links"
                result = make_api_request(endpoint, method="POST", data=link_data)

                if result["success"]:
                    st.success(f"🎉 Successfully created go/{keyword}!")

                    # Show the new link
                    link = result["data"]
                    st.markdown(f"""
                    <div class="link-card">
                        <h3>🔗 Your New Link</h3>
                        <p><strong>Keyword:</strong> go/{link['keyword']}</p>
                        <p><strong>URL:</strong> {link['url']}</p>
                        <p><strong>Title:</strong> {link.get('title', 'N/A')}</p>
                        <p><strong>Category:</strong> <span class="category-tag">{link['category']}</span></p>
                        <p><strong>Test it:</strong> <a href="http://localhost:8000/go/{link['keyword']}" target="_blank">http://localhost:8000/go/{link['keyword']}</a></p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Clear session state
                    if 'ai_analysis' in st.session_state:
                        del st.session_state['ai_analysis']
                    if 'analyzed_url' in st.session_state:
                        del st.session_state['analyzed_url']
                else:
                    if "409" in str(result["error"]):
                        st.error(f"❌ Keyword '{keyword}' already exists. Please choose a different one.")

                        # Suggest alternatives
                        suggestions = [f"{keyword}2", f"{keyword}-new", f"my-{keyword}"]
                        st.info(f"💡 Try these alternatives: {', '.join(suggestions)}")
                    else:
                        st.error(f"❌ Failed to create link: {result['error']}")


def show_link_manager():
    """Enhanced link management interface"""
    st.header("🔧 Link Manager")

    # Search and filter controls
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search links", placeholder="Search keywords, titles, URLs...")

    with col2:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All Categories"] + ["General", "Development", "Productivity", "Communication", "HR", "Marketing",
                                  "Finance"]
        )

    with col3:
        sort_by = st.selectbox("Sort by", ["Created Date", "Clicks", "Keyword", "Category"])

    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    # Get and filter links
    links = get_links()

    if not links:
        st.info("📝 No links found. Create your first link using the AI Link Creator!")
        return

    # Apply filters
    filtered_links = links

    if search_term:
        filtered_links = [
            link for link in filtered_links
            if (search_term.lower() in link["keyword"].lower() or
                search_term.lower() in (link.get("title", "")).lower() or
                search_term.lower() in (link.get("description", "")).lower() or
                search_term.lower() in link["url"].lower())
        ]

    if category_filter != "All Categories":
        filtered_links = [link for link in filtered_links if link["category"] == category_filter]

    # Sort links
    if sort_by == "Clicks":
        filtered_links.sort(key=lambda x: x.get("click_count", 0), reverse=True)
    elif sort_by == "Keyword":
        filtered_links.sort(key=lambda x: x["keyword"])
    elif sort_by == "Category":
        filtered_links.sort(key=lambda x: x["category"])
    else:  # Created Date
        filtered_links.sort(key=lambda x: x["created_at"], reverse=True)

    # Results summary
    st.write(f"📊 Found **{len(filtered_links)}** links (of {len(links)} total)")

    # Links display
    for i, link in enumerate(filtered_links):
        with st.container():
            # Create expandable link card
            with st.expander(
                    f"🔗 go/{link['keyword']} - {link.get('title', 'No title')} ({link.get('click_count', 0)} clicks)"):

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**🔗 Keyword:** `go/{link['keyword']}`")
                    st.markdown(f"**🌐 URL:** {link['url']}")
                    if link.get('title'):
                        st.markdown(f"**📝 Title:** {link['title']}")

                with col2:
                    st.markdown(f"**🏷️ Category:** {link['category']}")
                    st.markdown(f"**📊 Clicks:** {link.get('click_count', 0)}")
                    st.markdown(f"**📅 Created:** {link['created_at'][:10]}")

                with col3:
                    # Action buttons
                    if st.button(f"🔗 Test", key=f"test_{link['keyword']}_{i}"):
                        st.markdown(f"**Test URL:** [go/{link['keyword']}](http://localhost:8000/go/{link['keyword']})")

                    if st.button(f"🗑️ Delete", key=f"delete_{link['keyword']}_{i}", type="secondary"):
                        if st.button(f"⚠️ Confirm Delete", key=f"confirm_{link['keyword']}_{i}"):
                            result = make_api_request(f"/api/links/{link['keyword']}", method="DELETE")
                            if result["success"]:
                                st.success(f"🗑️ Deleted go/{link['keyword']}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete: {result['error']}")

                # Description
                if link.get('description'):
                    st.markdown(f"**📄 Description:** {link['description']}")


def show_quick_actions():
    """Quick actions and utilities"""
    st.header("⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛠️ Development Tools")

        if st.button("📦 Create Sample Links", type="primary"):
            result = make_api_request("/api/dev/sample-links")
            if result["success"]:
                st.success("✅ Sample links created!")
                st.json(result["data"])
                st.cache_data.clear()
            else:
                st.error(f"❌ Error: {result['error']}")

        if st.button("🔍 Test API Connection"):
            health = check_api_health()
            if health["success"]:
                st.success("✅ API is healthy!")
                st.json(health["data"])
            else:
                st.error("❌ API connection failed")

        if st.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.success("✅ Cache cleared!")

    with col2:
        st.subheader("📈 Bulk Operations")

        # Bulk link creation
        st.markdown("**📄 Bulk Create Links**")
        csv_data = st.text_area(
            "CSV Data (keyword,url,title,category)",
            placeholder="github,https://github.com,GitHub,Development\ndocs,https://docs.google.com,Google Docs,Productivity",
            height=100
        )

        if st.button("📦 Create Bulk Links"):
            if csv_data:
                lines = csv_data.strip().split('\n')
                created = 0
                errors = 0

                for line in lines:
                    try:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 2:
                            link_data = {
                                "keyword": parts[0],
                                "url": parts[1],
                                "title": parts[2] if len(parts) > 2 else None,
                                "category": parts[3] if len(parts) > 3 else "General"
                            }

                            result = make_api_request("/api/links", method="POST", data=link_data)
                            if result["success"]:
                                created += 1
                            else:
                                errors += 1
                    except:
                        errors += 1

                st.success(f"✅ Created {created} links")
                if errors > 0:
                    st.warning(f"⚠️ {errors} errors occurred")

                st.cache_data.clear()
            else:
                st.error("❌ Please enter CSV data")


# Header
st.markdown('<h1 class="main-header">🔗 SmartLinks</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Enhanced Go Links Dashboard</p>', unsafe_allow_html=True)

# API Health Check
health = check_api_health()
if not health["success"]:
    st.error("🚨 API Connection Failed")
    st.error(f"Cannot connect to backend at {API_BASE_URL}")
    st.info("Make sure your FastAPI backend is running on port 8000")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("🎛️ Control Panel")

    # API Status
    if health["success"]:
        api_data = health["data"]
        st.markdown(f"""
        <div class="status-card">
            <h4>✅ API Status</h4>
            <p><strong>Status:</strong> {api_data.get('status', 'unknown')}</p>
            <p><strong>Database:</strong> {api_data.get('database', 'unknown')}</p>
            <p><strong>Links:</strong> {api_data.get('total_links', 0)}</p>
        </div>
        """, unsafe_allow_html=True)

    # Navigation
    st.markdown("### 📊 Navigation")
    page = st.selectbox(
        "",
        ["📈 Analytics Dashboard", "✨ AI Link Creator", "🔧 Link Manager", "⚡ Quick Actions"],
        label_visibility="collapsed"
    )

    # Quick stats
    analytics = get_analytics()
    if analytics:
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Links", analytics.get("total_links", 0))
        st.metric("Total Clicks", analytics.get("total_clicks", 0))

        if analytics.get("total_links", 0) > 0:
            avg_clicks = analytics.get("total_clicks", 0) / analytics.get("total_links", 1)
            st.metric("Avg Clicks/Link", f"{avg_clicks:.1f}")

# Main content routing
if page == "📈 Analytics Dashboard":
    show_analytics_dashboard()
elif page == "✨ AI Link Creator":
    show_ai_link_creator()
elif page == "🔧 Link Manager":
    show_link_manager()
elif page == "⚡ Quick Actions":
    show_quick_actions()