"""
AI Module for SmartLinks
Handles URL analysis, keyword suggestions, and content extraction
"""
import os
import re
import httpx
from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AIAnalyzer:
    """AI-powered URL analysis and keyword generation"""

    def __init__(self):
        self.max_content_length = 5000  # Limit content to avoid token limits
        self.timeout = 10  # HTTP request timeout

    async def analyze_url(self, url: str) -> Dict:
        """
        Main function to analyze a URL and return AI insights
        Returns: {
            'title': str,
            'description': str,
            'category': str,
            'keywords': List[str],
            'content_type': str
        }
        """
        try:
            # Extract content from URL
            content_data = await self._extract_url_content(url)

            # Get AI analysis
            ai_analysis = await self._get_ai_analysis(url, content_data)

            return {
                'success': True,
                'title': ai_analysis.get('title', ''),
                'description': ai_analysis.get('description', ''),
                'category': ai_analysis.get('category', 'General'),
                'keywords': ai_analysis.get('keywords', []),
                'content_type': content_data.get('content_type', 'unknown'),
                'extracted_title': content_data.get('title', ''),
                'extracted_description': content_data.get('description', '')
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
        """Extract title, description, and content from URL"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                # Parse HTML content
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

                # Extract main content (first few paragraphs)
                content_text = ''
                paragraphs = soup.find_all('p')
                for p in paragraphs[:3]:  # First 3 paragraphs
                    content_text += p.get_text().strip() + ' '

                # Clean and limit content
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

    async def _get_ai_analysis(self, url: str, content_data: Dict) -> Dict:
        """Get AI analysis of the URL content"""
        try:
            # Prepare prompt for AI
            prompt = self._create_analysis_prompt(url, content_data)

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing web content and creating memorable, concise keywords for internal company links. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=500
            )

            # Parse AI response
            ai_text = response.choices[0].message.content.strip()

            # Clean JSON response (remove markdown formatting if present)
            if ai_text.startswith('```json'):
                ai_text = ai_text.replace('```json', '').replace('```', '').strip()

            ai_result = json.loads(ai_text)

            return ai_result

        except Exception as e:
            # Fallback analysis if AI fails
            return self._fallback_analysis(url, content_data)

    def _create_analysis_prompt(self, url: str, content_data: Dict) -> str:
        """Create prompt for AI analysis"""
        return f"""
Analyze this URL and content to create internal company link suggestions:

URL: {url}
Title: {content_data.get('title', 'N/A')}
Description: {content_data.get('description', 'N/A')}
Content: {content_data.get('content', 'N/A')[:1000]}

Please provide a JSON response with:
1. A clean, professional title (max 60 chars)
2. A helpful description (max 150 chars) 
3. The most appropriate category from: [Development, Productivity, Communication, HR, Marketing, Finance, General]
4. 3-5 suggested keywords that are:
   - Short (2-15 characters)
   - Memorable and intuitive
   - Lowercase with hyphens/underscores only
   - Would make sense in a "go/keyword" format

Example format:
{{
    "title": "GitHub Repository Platform",
    "description": "Code hosting and collaboration for software development teams",
    "category": "Development", 
    "keywords": ["github", "code", "repo", "git", "dev-tools"]
}}

Focus on what this link would be useful for in a company context.
"""

    def _fallback_analysis(self, url: str, content_data: Dict) -> Dict:
        """Fallback analysis when AI is unavailable"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')

        # Simple keyword generation based on domain
        base_keyword = domain.split('.')[0].lower()

        # Category mapping for common domains
        category_map = {
            'github.com': 'Development',
            'docs.google.com': 'Productivity',
            'drive.google.com': 'Productivity',
            'slack.com': 'Communication',
            'zoom.us': 'Communication',
            'figma.com': 'Development',
            'notion.so': 'Productivity',
            'calendar.google.com': 'Productivity'
        }

        category = category_map.get(domain, 'General')

        return {
            'title': content_data.get('title', domain.replace('.com', '').title()),
            'description': content_data.get('description', f"Link to {domain}"),
            'category': category,
            'keywords': [base_keyword, domain.split('.')[0], 'link']
        }

    def suggest_keywords_for_text(self, text: str, existing_keywords: List[str] = None) -> List[str]:
        """Generate keyword suggestions from text input"""
        if existing_keywords is None:
            existing_keywords = []

        try:
            prompt = f"""
Generate 5 short, memorable keywords for this text that would work well in a "go/keyword" format:

Text: "{text}"

Existing keywords to avoid: {existing_keywords}

Requirements:
- 2-15 characters each
- Lowercase with hyphens/underscores only  
- Intuitive and easy to remember
- Suitable for internal company links

Return as JSON array: ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "You are an expert at creating short, memorable keywords. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=100
            )

            ai_text = response.choices[0].message.content.strip()
            if ai_text.startswith('```json'):
                ai_text = ai_text.replace('```json', '').replace('```', '').strip()

            keywords = json.loads(ai_text)
            return keywords if isinstance(keywords, list) else []

        except Exception as e:
            # Fallback keyword generation
            words = re.findall(r'\b\w+\b', text.lower())
            return [word for word in words if 2 <= len(word) <= 15][:5]


# Singleton instance
ai_analyzer = AIAnalyzer()


# Convenience functions for use in FastAPI endpoints
async def analyze_url(url: str) -> Dict:
    """Analyze URL and return AI insights"""
    return await ai_analyzer.analyze_url(url)


def suggest_keywords(text: str, existing_keywords: List[str] = None) -> List[str]:
    """Generate keyword suggestions from text"""
    return ai_analyzer.suggest_keywords_for_text(text, existing_keywords)


def test_ai_connection() -> Dict:
    """Test OpenAI API connection"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'AI connection successful'"}],
            max_tokens=10
        )
        return {
            "success": True,
            "message": response.choices[0].message.content,
            "model": "gpt-4o-mini"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }