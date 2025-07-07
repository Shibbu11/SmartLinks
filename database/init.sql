-- SmartLinks Database Schema
-- SQLite database for MVP, can migrate to PostgreSQL later

-- Links table - core functionality
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword VARCHAR(100) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    description TEXT,
    category VARCHAR(50) DEFAULT 'General',
    created_by VARCHAR(100) DEFAULT 'anonymous',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Click tracking for analytics
CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referrer TEXT,
    FOREIGN KEY (link_id) REFERENCES links (id)
);

-- Users table (simple for MVP)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some sample data for testing
INSERT OR IGNORE INTO links (keyword, url, title, description, category) VALUES
('github', 'https://github.com', 'GitHub', 'Code repository platform', 'Development'),
('docs', 'https://docs.google.com', 'Google Docs', 'Document creation and collaboration', 'Productivity'),
('slack', 'https://slack.com', 'Slack', 'Team communication platform', 'Communication');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_links_keyword ON links(keyword);
CREATE INDEX IF NOT EXISTS idx_clicks_link_id ON clicks(link_id);
CREATE INDEX IF NOT EXISTS idx_clicks_date ON clicks(clicked_at);