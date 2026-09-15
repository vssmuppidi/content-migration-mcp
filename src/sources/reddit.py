"""Reddit API integration for fetching trending content."""

import praw
from typing import List, Dict, Optional
from datetime import datetime
from ..config import config


class RedditSource:
    """Wrapper for Reddit API interactions."""
    
    def __init__(self):
        """Initialize Reddit API client."""
        if not config.validate_reddit_config():
            raise ValueError(
                "Reddit API credentials not configured. "
                "Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
            )
        
        self.reddit = praw.Reddit(
            client_id=config.reddit_client_id,
            client_secret=config.reddit_client_secret,
            user_agent=config.reddit_user_agent
        )
    
    def get_trending_posts(
        self,
        topic: str,
        subreddit: Optional[str] = "all",
        limit: int = 10,
        sort: str = "hot"
    ) -> List[Dict[str, any]]:
        """
        Fetch trending posts from Reddit based on a topic.
        
        Args:
            topic: Search query or topic
            subreddit: Target subreddit (default: "all")
            limit: Maximum number of posts to fetch
            sort: Sort method - "hot", "top", "new", "relevance"
            
        Returns:
            List of dictionaries containing post information
        """
        try:
            results = []
            sub = self.reddit.subreddit(subreddit)
            
            for post in sub.search(topic, sort=sort, limit=limit):
                selftext = post.selftext[:500] if post.selftext else ""
                
                top_comments = []
                try:
                    post.comments.replace_more(limit=0)
                    comments = sorted(
                        post.comments.list(),
                        key=lambda c: c.score,
                        reverse=True
                    )[:3]
                    for comment in comments:
                        if hasattr(comment, 'body') and comment.body:
                            top_comments.append({
                                "text": comment.body[:200],
                                "score": comment.score,
                                "author": str(comment.author) if comment.author else "[deleted]"
                            })
                except Exception:
                    pass
                
                engagement_score = (post.score * 0.4) + (post.num_comments * 0.6)
                
                from datetime import datetime
                age_hours = (datetime.now().timestamp() - post.created_utc) / 3600
                recency_score = max(0, 100 - (age_hours / 24))
                
                results.append({
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "subreddit": str(post.subreddit),
                    "author": str(post.author),
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "selftext": selftext,
                    "upvote_ratio": post.upvote_ratio,
                    "top_comments": top_comments,
                    "engagement_score": round(engagement_score, 2),
                    "recency_score": round(recency_score, 2),
                    "age_hours": round(age_hours, 1),
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching Reddit data: {str(e)}")
    
    def get_hot_posts(
        self,
        subreddit: str = "all",
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Fetch hot posts from a subreddit.
        
        Args:
            subreddit: Target subreddit
            limit: Maximum number of posts to fetch
            
        Returns:
            List of dictionaries containing post information
        """
        try:
            results = []
            sub = self.reddit.subreddit(subreddit)
            
            for post in sub.hot(limit=limit):
                # Extract selftext (full content, truncated to 500 chars)
                selftext = post.selftext[:500] if post.selftext else ""
                
                # Get top 3 comments
                top_comments = []
                try:
                    post.comments.replace_more(limit=0)
                    comments = sorted(
                        post.comments.list(),
                        key=lambda c: c.score,
                        reverse=True
                    )[:3]
                    for comment in comments:
                        if hasattr(comment, 'body') and comment.body:
                            top_comments.append({
                                "text": comment.body[:200],
                                "score": comment.score,
                                "author": str(comment.author) if comment.author else "[deleted]"
                            })
                except Exception:
                    pass
                
                # Calculate engagement score
                engagement_score = (post.score * 0.4) + (post.num_comments * 0.6)
                
                # Calculate recency score
                from datetime import datetime
                age_hours = (datetime.now().timestamp() - post.created_utc) / 3600
                recency_score = max(0, 100 - (age_hours / 24))
                
                results.append({
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "subreddit": str(post.subreddit),
                    "author": str(post.author),
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "selftext": selftext,
                    "upvote_ratio": post.upvote_ratio,
                    "top_comments": top_comments,
                    "engagement_score": round(engagement_score, 2),
                    "recency_score": round(recency_score, 2),
                    "age_hours": round(age_hours, 1),
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching Reddit hot posts: {str(e)}")


# Module-level function for easy access
def get_reddit_ideas(
    topic: str,
    subreddit: Optional[str] = "all",
    limit: int = 10
) -> List[Dict[str, any]]:
    """
    Convenience function to fetch Reddit ideas.
    
    Args:
        topic: Search topic
        subreddit: Target subreddit
        limit: Maximum results
        
    Returns:
        List of trending posts
    """
    try:
        reddit_source = RedditSource()
        return reddit_source.get_trending_posts(topic, subreddit, limit)
    except ValueError:
        # Return empty list if not configured
        return []
    except Exception as e:
        raise Exception(f"Reddit API error: {str(e)}")

