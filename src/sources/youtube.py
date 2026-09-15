"""YouTube Data API integration for fetching trending videos."""

from googleapiclient.discovery import build
from typing import List, Dict, Optional
from ..config import config


class YouTubeSource:
    """Wrapper for YouTube Data API v3 interactions."""
    
    def __init__(self):
        """Initialize YouTube API client."""
        if not config.validate_youtube_config():
            raise ValueError(
                "YouTube API key not configured. "
                "Please set YOUTUBE_API_KEY."
            )
        
        self.youtube = build('youtube', 'v3', developerKey=config.youtube_api_key)
    
    def search_videos(
        self,
        topic: str,
        limit: int = 10,
        order: str = "viewCount"
    ) -> List[Dict[str, any]]:
        """
        Search for videos on YouTube based on a topic.
        
        Args:
            topic: Search query
            limit: Maximum number of videos to fetch (default: 10)
            order: Sort order - "viewCount", "relevance", "date", "rating"
            
        Returns:
            List of dictionaries containing video information
        """
        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=topic,
                part='id,snippet',
                maxResults=min(limit, 50),  # API max is 50
                order=order,
                type='video'
            ).execute()
            
            results = []
            video_ids = []
            
            for item in search_response.get('items', []):
                video_ids.append(item['id']['videoId'])
            
            if video_ids:
                videos_response = self.youtube.videos().list(
                    part='statistics,contentDetails,snippet',
                    id=','.join(video_ids)
                ).execute()
                
                stats_map = {}
                for video in videos_response.get('items', []):
                    stats = video.get('statistics', {})
                    snippet = video.get('snippet', {})
                    content_details = video.get('contentDetails', {})
                    
                    view_count = int(stats.get('viewCount', 0))
                    like_count = int(stats.get('likeCount', 0))
                    comment_count = int(stats.get('commentCount', 0))
                    
                    engagement_ratio = 0
                    if view_count > 0:
                        engagement_ratio = ((like_count + comment_count) / view_count) * 100
                    
                    description = snippet.get('description', '')[:300]
                    tags = snippet.get('tags', [])[:10]
                    channel_title = snippet.get('channelTitle', '')
                    channel_id = snippet.get('channelId', '')
                    
                    # Parse duration (ISO 8601 format like PT5M30S)
                    duration_str = content_details.get('duration', '')
                    
                    stats_map[video['id']] = {
                        'view_count': view_count,
                        'like_count': like_count,
                        'comment_count': comment_count,
                        'duration': duration_str,
                        'description': description,
                        'tags': tags,
                        'channel_title': channel_title,
                        'channel_id': channel_id,
                        'engagement_ratio': round(engagement_ratio, 4),
                        'published_at': snippet.get('publishedAt', ''),
                    }
            
            # Combine search results with statistics
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                stats = stats_map.get(video_id, {})
                
                results.append({
                    "title": snippet.get('title', ''),
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "description": stats.get('description', ''),
                    "channel_title": stats.get('channel_title', ''),
                    "channel_id": stats.get('channel_id', ''),
                    "published_at": stats.get('published_at', ''),
                    "thumbnail_url": snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    "view_count": stats.get('view_count', 0),
                    "like_count": stats.get('like_count', 0),
                    "comment_count": stats.get('comment_count', 0),
                    "duration": stats.get('duration', ''),
                    "tags": stats.get('tags', []),
                    "engagement_ratio": stats.get('engagement_ratio', 0),
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching YouTube data: {str(e)}")
    
    def get_trending_videos(
        self,
        region_code: str = "US",
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get trending videos from YouTube.
        
        Args:
            region_code: ISO 3166-1 alpha-2 country code (default: "US")
            limit: Maximum number of videos to fetch
            
        Returns:
            List of dictionaries containing video information
        """
        try:
            # Get trending videos
            trending_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=min(limit, 50)
            ).execute()
            
            results = []
            for item in trending_response.get('items', []):
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                
                view_count = int(statistics.get('viewCount', 0))
                like_count = int(statistics.get('likeCount', 0))
                comment_count = int(statistics.get('commentCount', 0))
                
                # Calculate engagement ratio
                engagement_ratio = 0
                if view_count > 0:
                    engagement_ratio = ((like_count + comment_count) / view_count) * 100
                
                results.append({
                    "title": snippet.get('title', ''),
                    "video_id": item['id'],
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "description": snippet.get('description', '')[:300],
                    "channel_title": snippet.get('channelTitle', ''),
                    "channel_id": snippet.get('channelId', ''),
                    "published_at": snippet.get('publishedAt', ''),
                    "thumbnail_url": snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    "view_count": view_count,
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "duration": item['contentDetails'].get('duration', ''),
                    "tags": snippet.get('tags', [])[:10],
                    "engagement_ratio": round(engagement_ratio, 4),
                })
            
            return results
        
        except Exception as e:
            raise Exception(f"Error fetching YouTube trending videos: {str(e)}")


# Module-level function for easy access
def get_youtube_ideas(
    topic: str,
    limit: int = 10,
    order: str = "viewCount"
) -> List[Dict[str, any]]:
    """
    Convenience function to fetch YouTube video ideas.
    
    Args:
        topic: Search topic
        limit: Maximum results
        order: Sort order
        
    Returns:
        List of trending videos
    """
    try:
        youtube_source = YouTubeSource()
        return youtube_source.search_videos(topic, limit, order)
    except ValueError:
        # Return empty list if not configured
        return []
    except Exception as e:
        raise Exception(f"YouTube API error: {str(e)}")

