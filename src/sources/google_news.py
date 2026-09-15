"""Google News RSS feed integration for fetching news articles."""

import feedparser
from typing import List, Dict
from urllib.parse import quote
from datetime import datetime
import re


class GoogleNewsSource:
    """Wrapper for Google News RSS feed parsing."""
    
    BASE_URL = "https://news.google.com/rss"
    
    def __init__(self):
        """Initialize Google News source."""
        pass  # No API key needed for RSS feeds
    
    def search_news(
        self,
        topic: str,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Search for news articles on Google News based on a topic.
        
        Args:
            topic: Search query
            limit: Maximum number of articles to fetch
            
        Returns:
            List of dictionaries containing article information
        """
        try:
            # Construct search URL
            search_url = f"{self.BASE_URL}/search?q={quote(topic)}&hl=en-US&gl=US&ceid=US:en"
            
            # Parse the RSS feed
            feed = feedparser.parse(search_url)
            
            results = []
            for entry in feed.entries[:limit]:
                title = entry.get('title', '')
                description = entry.get('summary', '')
                published_str = entry.get('published', '')
                source = entry.get('source', {}).get('title', 'Unknown')
                
                # Parse publication date
                published_date = None
                recency_score = 0
                age_hours = None
                try:
                    if published_str:
                        # Use feedparser's date parsing
                        parsed_entry = feedparser.parse(f"<entry><published>{published_str}</published></entry>")
                        if parsed_entry.entries:
                            published_date = parsed_entry.entries[0].get('published_parsed')
                            if published_date:
                                # Convert struct_time to datetime
                                import time
                                timestamp = time.mktime(published_date)
                                age_hours = (datetime.now().timestamp() - timestamp) / 3600
                                recency_score = max(0, 100 - (age_hours / 24))
                except Exception:
                    pass
                
                text = f"{title} {description}".lower()
                keywords = []
                common_news_words = ['breaking', 'update', 'report', 'announce', 'reveal', 'confirm', 'deny']
                for word in common_news_words:
                    if word in text:
                        keywords.append(word)
                
                major_outlets = ['bbc', 'cnn', 'reuters', 'ap', 'the new york times', 'washington post', 
                               'the guardian', 'wall street journal', 'bloomberg', 'forbes']
                is_major_outlet = any(outlet in source.lower() for outlet in major_outlets)
                credibility_score = 1.0 if is_major_outlet else 0.5
                
                results.append({
                    "title": title,
                    "url": entry.get('link', ''),
                    "description": description,
                    "published": published_str,
                    "published_date": published_date.isoformat() if published_date else None,
                    "source": source,
                    "keywords": keywords,
                    "credibility_score": credibility_score,
                    "is_major_outlet": is_major_outlet,
                    "recency_score": round(recency_score, 2),
                    "age_hours": round(age_hours, 1) if age_hours else None,
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching Google News data: {str(e)}")
    
    def get_top_news(
        self,
        limit: int = 10,
        country: str = "US"
    ) -> List[Dict[str, any]]:
        """
        Get top/trending news articles from Google News.
        
        Args:
            limit: Maximum number of articles to fetch
            country: Country code (default: "US")
            
        Returns:
            List of dictionaries containing article information
        """
        try:
            # Construct top news URL
            top_news_url = f"{self.BASE_URL}?hl=en-{country}&gl={country}&ceid={country}:en"
            
            # Parse the RSS feed
            feed = feedparser.parse(top_news_url)
            
            results = []
            for entry in feed.entries[:limit]:
                results.append({
                    "title": entry.get('title', ''),
                    "url": entry.get('link', ''),
                    "description": entry.get('summary', ''),
                    "published": entry.get('published', ''),
                    "source": entry.get('source', {}).get('title', 'Unknown'),
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching Google News top stories: {str(e)}")
    
    def get_topic_news(
        self,
        topic: str,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get news articles for a specific Google News topic category.
        
        Available topics: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT,
                         SCIENCE, SPORTS, HEALTH
        
        Args:
            topic: Google News topic category (e.g., "TECHNOLOGY")
            limit: Maximum number of articles to fetch
            
        Returns:
            List of dictionaries containing article information
        """
        try:
            # Construct topic URL
            topic_url = f"{self.BASE_URL}/headlines/section/topic/{topic}?hl=en-US&gl=US&ceid=US:en"
            
            # Parse the RSS feed
            feed = feedparser.parse(topic_url)
            
            results = []
            for entry in feed.entries[:limit]:
                results.append({
                    "title": entry.get('title', ''),
                    "url": entry.get('link', ''),
                    "description": entry.get('summary', ''),
                    "published": entry.get('published', ''),
                    "source": entry.get('source', {}).get('title', 'Unknown'),
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching Google News topic '{topic}': {str(e)}")


# Module-level function for easy access
def get_news_ideas(
    topic: str,
    limit: int = 10
) -> List[Dict[str, any]]:
    """
    Convenience function to fetch Google News ideas.
    
    Args:
        topic: Search topic
        limit: Maximum results
        
    Returns:
        List of news articles
    """
    try:
        news_source = GoogleNewsSource()
        return news_source.search_news(topic, limit)
    except Exception as e:
        raise Exception(f"Google News error: {str(e)}")

