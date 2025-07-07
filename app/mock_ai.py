"""
Mock AI Module for SmartLinks
Simulates AI functionality without API calls - perfect for development and demos!
"""
import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urlparse
import random


class MockAIAnalyzer:
    """Mock AI analyzer that provides realistic responses without API calls"""

    def __init__(self):
        self.max_content_length = 5000
        self.timeout = 10

        # Pre-defined responses for common domains
        self.domain_responses = {
            'github.com': {
                'title': 'GitHub - Code Repository Platform',
                'description': 'Platform for version control and collaborative software development',
                'category': 'Development',
                'keywords': ['github', 'code', 'repo', 'git', 'dev-tools']
            },
            'docs.google.com': {
                'title': 'Google Docs - Document Collaboration',
                'description': 'Create and edit documents online with real-time collaboration',
                'category': 'Productivity',
                'keywords': ['docs', 'google-docs', 'document', 'collaborate', 'write']
            },
            'drive.google.com': {
                'title': 'Google Drive - Cloud Storage',
                'description': 'Store, sync, and share files across all your devices',
                'category': 'Productivity',
                'keywords': ['drive', 'storage', 'files', 'cloud', 'sync']
            },
            'slack.com': {
                'title': 'Slack - Team Communication',
                'description': 'Messaging platform for teams and workplace collaboration',
                'category': 'Communication',
                'keywords': ['slack', 'chat', 'team', 'message', 'communicate']
            },
            'zoom.us': {
                'title': 'Zoom - Video Conferencing',
                'description': 'Video meetings and webinars for remote collaboration',
                'category': 'Communication',
                'keywords': ['zoom', 'video', 'meeting', 'call', 'conference']
            },
            'notion.so': {
                'title': 'Notion - All-in-One Workspace',
                'description': 'Notes, docs, tasks, and databases in one collaborative workspace',
                'category': 'Productivity',
                'keywords': ['notion', 'notes', 'workspace', 'organize', 'docs']
            },
            'figma.com': {
                'title': 'Figma - Design Platform',
                'description': 'Collaborative interface design and prototyping tool',
                'category': 'Development',
                'keywords': ['figma', 'design', 'ui', 'prototype', 'collaborate']
            },
            'calendar.google.com': {
                'title': 'Google Calendar - Schedule Management',
                'description': 'Organize your schedule and share events with others',
                'category': 'Productivity',
                'keywords': ['calendar', 'schedule', 'meeting', 'event', 'plan']
            },
            'trello.com': {
                'title': 'Trello - Project Management',
                'description': 'Organize projects with boards, lists, and cards',
                'category': 'Productivity',
                'keywords': ['trello', 'project', 'board', 'organize', 'task']
            },
            'linkedin.com': {
                'title': 'LinkedIn - Professional Network',
                'description': 'Professional networking and career development platform',
                'category': 'HR',
                'keywords': ['linkedin', 'network', 'career', 'professional', 'jobs']
            }
        }

        # Category mapping for unknown domains
        self.category_keywords = {
            'Development': ['code', 'dev', 'git', 'api', 'programming', 'software', 'tech'],
            'Productivity': ['doc', 'file', 'note', 'organize', 'plan', 'manage', 'tool'],
            'Communication': ['chat', 'message', 'mail', 'talk', 'meet', 'call', 'social'],
            'HR': ['hire', 'job', 'career', 'employee', 'work', 'recruit', 'people'],
            'Marketing': ['market', 'campaign', 'brand', 'promo', 'ads', 'analytics', 'social'],
            'Finance': ['money', 'pay', 'bank', 'finance', 'budget', 'invoice', 'expense']
        }

    async def analyze_url(self, url: str) -> Dict:
        """Mock URL analysis that returns realistic AI-like responses"""
        try:
            # Extract content from URL (real)
            content_data = await self._extract_url_content(url)

            # Get mock AI analysis (simulated)
            ai_analysis = self._get_mock_analysis(url, content_data)

            return {
                'success': True,
                'title': ai_analysis.get('title', ''),
                'description': ai_analysis.get('description', ''),
                'category': ai_analysis.get('category', 'General'),
                'keywords': ai_analysis.get('keywords', []),
                'content_type': content_data.get('content_type', 'webpage'),
                'extracted_title': content_data.get('title', ''),
                'extracted_description': content_data.get('description', ''),
                'ai_confidence': 0.95,  # Mock confidence score
                'processing_time': f"{random.uniform(0.5, 2.0):.1f}s"  # Mock processing time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'title': '',
                'description': '',
                'category': 'General',
                'keywords': [],
                'content_type': 'unknown'
            }

    async def _extract_url_content(self, url: str) -> Dict:
        """Extract real content from URL (same as real AI module)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract title
                title = ''
                if soup.title:
                    title = soup.title.string.strip()

                # Extract meta description
                description = ''
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    description = meta_desc.get('content', '').strip()

                # Extract main content
                content_text = ''
                paragraphs = soup.find_all('p')
                for p in paragraphs[:3]:
                    content_text += p.get_text().strip() + ' '

                content_text = re.sub(r'\s+', ' ', content_text).strip()
                if len(content_text) > self.max_content_length:
                    content_text = content_text[:self.max_content_length] + '...'

                return {
                    'title': title,
                    'description': description,
                    'content': content_text,
                    'content_type': 'webpage',
                    'url': url
                }

        except Exception as e:
            # Fallback for URLs we can't scrape
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')

            return {
                'title': domain.replace('.com', '').replace('.', ' ').title(),
                'description': f"Link to {domain}",
                'content': f"External link to {domain}",
                'content_type': 'external',
                'url': url,
                'error': str(e)
            }

    def _get_mock_analysis(self, url: str, content_data: Dict) -> Dict:
        """Generate mock AI analysis that looks realistic"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')

        # Check if we have a pre-defined response for this domain
        if domain in self.domain_responses:
            response = self.domain_responses[domain].copy()

            # Enhance with extracted content if available
            if content_data.get('title') and len(content_data['title']) > len(response['title']):
                response['title'] = content_data['title']

            if content_data.get('description') and len(content_data['description']) > len(response['description']):
                response['description'] = content_data['description']

            return response

        # Generate analysis for unknown domains
        title = content_data.get('title', '') or self._generate_title_from_domain(domain)
        description = content_data.get('description', '') or self._generate_description_from_content(content_data)
        category = self._predict_category(url, content_data)
        keywords = self._generate_keywords(domain, title, content_data)

        return {
            'title': title[:60],  # Limit title length
            'description': description[:150],  # Limit description length
            'category': category,
            'keywords': keywords
        }

    def _generate_title_from_domain(self, domain: str) -> str:
        """Generate a title from domain name"""
        base_name = domain.split('.')[0]

        # Clean up common patterns
        base_name = base_name.replace('-', ' ').replace('_', ' ')

        # Capitalize properly
        title = base_name.title()

        # Add descriptive suffix based on domain patterns
        if 'app' in domain:
            title += ' - Web Application'
        elif 'docs' in domain:
            title += ' - Documentation'
        elif 'api' in domain:
            title += ' - API Service'
        elif 'blog' in domain:
            title += ' - Blog'
        else:
            title += ' - Website'

        return title

    def _generate_description_from_content(self, content_data: Dict) -> str:
        """Generate description from content"""
        content = content_data.get('content', '')

        if content and len(content) > 50:
            # Take first sentence or first 100 characters
            first_sentence = content.split('.')[0]
            if len(first_sentence) < 150:
                return first_sentence.strip() + '.'
            else:
                return content[:100].strip() + '...'

        # Fallback
        domain = urlparse(content_data.get('url', '')).netloc.replace('www.', '')
        return f"Web resource hosted on {domain}"

    def _predict_category(self, url: str, content_data: Dict) -> str:
        """Predict category based on URL and content"""
        text_to_analyze = f"{url} {content_data.get('title', '')} {content_data.get('description', '')} {content_data.get('content', '')}"
        text_to_analyze = text_to_analyze.lower()

        # Score each category
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                score += text_to_analyze.count(keyword)
            category_scores[category] = score

        # Return category with highest score, or General if no clear winner
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return 'General'

    def _generate_keywords(self, domain: str, title: str, content_data: Dict) -> List[str]:
        """Generate keyword suggestions"""
        keywords = []

        # Domain-based keyword
        base_domain = domain.split('.')[0].lower()
        if base_domain and len(base_domain) >= 2:
            keywords.append(base_domain)

        # Title-based keywords
        if title:
            title_words = re.findall(r'\b\w+\b', title.lower())
            for word in title_words:
                if 2 <= len(word) <= 12 and word not in keywords:
                    keywords.append(word)
                if len(keywords) >= 5:
                    break

        # Content-based keywords
        content = content_data.get('content', '')
        if content and len(keywords) < 5:
            content_words = re.findall(r'\b\w+\b', content.lower())
            # Filter common words
            common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an',
                            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                            'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}

            for word in content_words:
                if (2 <= len(word) <= 12 and
                        word not in keywords and
                        word not in common_words and
                        word.isalpha()):
                    keywords.append(word)
                    if len(keywords) >= 5:
                        break

        # Generate variations if we need more
        while len(keywords) < 3:
            if base_domain:
                keywords.append(f"{base_domain}{len(keywords)}")
            else:
                keywords.append(f"link{len(keywords)}")

        return keywords[:5]  # Return max 5 keywords

    def suggest_keywords_for_text(self, text: str, existing_keywords: List[str] = None) -> List[str]:
        """Generate keyword suggestions from text input"""
        if existing_keywords is None:
            existing_keywords = []

        # Extract words from text
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter and process words
        keywords = []
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is',
                        'are', 'this', 'that'}

        for word in words:
            if (2 <= len(word) <= 15 and
                    word not in common_words and
                    word not in existing_keywords and
                    word not in keywords and
                    word.isalpha()):
                keywords.append(word)
                if len(keywords) >= 5:
                    break

        # Generate variations if needed
        if len(keywords) < 5:
            base_words = keywords[:2] if keywords else ['link']
            for base in base_words:
                for i in range(2, 10):
                    variant = f"{base}{i}"
                    if variant not in existing_keywords and variant not in keywords:
                        keywords.append(variant)
                        if len(keywords) >= 5:
                            break

        return keywords[:5]


# Mock singleton instance
mock_ai_analyzer = MockAIAnalyzer()


# Mock convenience functions
async def analyze_url(url: str) -> Dict:
    """Mock analyze URL function"""
    return await mock_ai_analyzer.analyze_url(url)


def suggest_keywords(text: str, existing_keywords: List[str] = None) -> List[str]:
    """Mock suggest keywords function"""
    return mock_ai_analyzer.suggest_keywords_for_text(text, existing_keywords)


def test_ai_connection() -> Dict:
    """Mock AI connection test - always succeeds"""
    return {
        "success": True,
        "message": "Mock AI connection successful! (No API costs)",
        "model": "mock-ai-v1.0",
        "status": "Ready for development and demos"
    }