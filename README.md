# 🔗 SmartLinks

> AI-Enhanced Go Links for Your Team

SmartLinks is a modern URL shortener that creates memorable `go/keyword` links for your team, enhanced with AI-powered suggestions and beautiful analytics.

## ✨ Features

- 🔗 **Custom Go Links**: Create memorable `go/keyword` shortcuts
- 📊 **Beautiful Analytics**: Track clicks with interactive charts
- 🤖 **AI-Powered**: Smart keyword suggestions and URL analysis
- 🎨 **Modern Dashboard**: Professional Streamlit interface
- ⚡ **Fast & Reliable**: Built with FastAPI and SQLite/PostgreSQL
- 🚀 **Easy Deployment**: Ready for Railway and Streamlit Cloud

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartlinks.git
   cd smartlinks
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the backend**
   ```bash
   cd app
   python main.py
   ```

5. **Run the frontend** (in another terminal)
   ```bash
   cd frontend
   streamlit run enhanced_app_working.py
   ```

6. **Visit your app**
   - Backend API: http://localhost:8000
   - Frontend Dashboard: http://localhost:8501
   - Test a link: http://localhost:8000/go/github

## 🌐 Production Deployment

### Backend (Railway)

1. Push your code to GitHub
2. Connect your repo to [Railway](https://railway.app)
3. Set environment variables:
   ```
   ENVIRONMENT=production
   USE_MOCK_AI=True
   SECRET_KEY=your-secret-key
   ```
4. Deploy automatically!

### Frontend (Streamlit Cloud)

1. Connect your repo to [Streamlit Cloud](https://streamlit.io/cloud)
2. Set main file: `frontend/app.py`
3. Add environment variable: `API_BASE_URL=https://your-backend.railway.app`
4. Deploy!

## 📖 API Documentation

Visit `/docs` on your backend URL for interactive API documentation.

### Core Endpoints

- `GET /go/{keyword}` - Redirect to target URL
- `POST /api/links` - Create new link
- `GET /api/links` - List all links
- `GET /api/analytics/stats` - Get analytics data
- `POST /api/ai/analyze-url` - AI URL analysis

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **Frontend**: Streamlit, Plotly, Pandas
- **AI**: OpenAI API (with mock fallback)
- **Deployment**: Railway, Streamlit Cloud
- **Database**: SQLite (dev), PostgreSQL (prod)

## 📊 Usage Examples

```bash
# Create a link
curl -X POST "http://localhost:8000/api/links" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "github", "url": "https://github.com", "title": "GitHub"}'

# Use the link
curl "http://localhost:8000/go/github"
# Redirects to https://github.com

# Get analytics
curl "http://localhost:8000/api/analytics/stats"
```

## 🔧 Configuration

### Environment Variables

```bash
# App Settings
ENVIRONMENT=development  # development, production
DEBUG=True
USE_MOCK_AI=True  # Set to False to use real OpenAI API

# Database
DATABASE_URL=sqlite:///./smartlinks.db  # Auto-set by Railway in prod

# AI (Optional)
OPENAI_API_KEY=sk-...  # Only needed if USE_MOCK_AI=False

# Security (Production)
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.railway.app
CORS_ORIGINS=https://your-frontend.streamlit.app
```

## 📈 Analytics Features

- **Click Tracking**: Every go/link click is tracked
- **Top Links**: See your most popular links
- **Category Breakdown**: Organize links by department
- **Recent Activity**: Real-time click timeline
- **Usage Insights**: AI-powered usage recommendations

## 🤖 AI Features

- **Smart Keywords**: AI suggests memorable keywords from URLs
- **Auto-Categorization**: Automatically sorts links by department
- **URL Analysis**: Extracts titles and descriptions from web pages
- **Content Understanding**: Analyzes page content for better suggestions

## 🏗️ Project Structure

```
smartlinks/
├── app/                    # FastAPI backend
│   ├── main.py            # Development server
│   ├── main_production.py # Production server
│   ├── models.py          # Database models
│   ├── ai.py              # AI integration
│   └── mock_ai.py         # Mock AI for development
├── frontend/              # Streamlit frontend
│   ├── app.py             # Production frontend
│   ├── enhanced_app_working.py  # Development frontend
│   └── landing.html       # Static landing page
├── requirements.txt       # Python dependencies
├── railway.json          # Railway deployment config
└── .gitignore            # Git ignore rules
```

## 🔒 Security

- Rate limiting on API endpoints
- Input validation and sanitization
- CORS protection
- SQL injection prevention via SQLAlchemy ORM
- Environment-based configuration

## 🎯 Roadmap

- [ ] User authentication and teams
- [ ] Custom domains (yourcompany.co/keyword)
- [ ] Browser extension for quick link creation
- [ ] Slack/Teams integration
- [ ] Advanced analytics and reporting
- [ ] Link expiration and scheduling
- [ ] Bulk import/export tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test them
4. Commit: `git commit -m "Add feature-name"`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/smartlinks/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/smartlinks/discussions)

## 🙏 Acknowledgments

- Built with ❤️ using FastAPI and Streamlit
- Inspired by Google's internal go/links system
- UI design inspired by modern SaaS applications

---

**⭐ Star this repo if you found it helpful!**