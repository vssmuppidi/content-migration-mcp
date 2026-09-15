"""Main MCP server for Content Creation tools."""

import asyncio
import json
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor
from mcp.server import Server
from mcp.types import Tool, TextContent, Prompt, PromptArgument, Resource, PromptMessage, TextResourceContents, GetPromptResult
from mcp.server.stdio import stdio_server

from .tools.ideas import (
    generate_ideas,
    generate_reddit_ideas,
    generate_youtube_ideas,
    generate_news_ideas
)
from .tools.script import generate_script, generate_script_from_ideas, generate_complete_script
from .tools.voice import (
    generate_complete_content,
    generate_script_with_audio,
    generate_audio_from_script,
    list_all_voices,
    find_voice_by_name
)
from .tools.video import (
    generate_video_from_image_audio,
    generate_video_from_video,
    generate_complete_video
)
from .utils.query_analyzer import analyze_query_intent
from .services.context_enricher import enrich_query_with_context, fetch_relevant_context
from .services.context_cache import get_cache
from .middleware.context_middleware import get_middleware
from .config import config


# Initialize the MCP server
app = Server("content-mcp-server")

# Thread pool executor for running synchronous blocking operations (like PRAW)
# This prevents blocking the async event loop and eliminates PRAW warnings
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp-worker")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="generate_ideas",
            description=(
                "Generate content ideas by aggregating trending topics from multiple sources "
                "(Reddit, YouTube, and Google News). Returns structured data with trending topics "
                "and metadata from all sources. "
                "NOTE: For automatic context injection, use the 'trending_analysis' prompt or "
                "read from 'trending://topics/{topic}' resource instead of calling this tool directly."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic or event to search for (e.g., 'AI', 'Trump', 'climate change')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results per source (default: 10)",
                        "default": 10
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="generate_reddit_ideas",
            description=(
                "Generate content ideas from Reddit only. Search for trending posts "
                "in specific subreddits or across all of Reddit."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search for"
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Target subreddit (default: 'all')",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="generate_youtube_ideas",
            description=(
                "Generate content ideas from YouTube only. Search for trending videos "
                "related to a topic with various sort options."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search for"
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order: 'viewCount', 'relevance', 'date', or 'rating' (default: 'viewCount')",
                        "enum": ["viewCount", "relevance", "date", "rating"],
                        "default": "viewCount"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="generate_news_ideas",
            description=(
                "Generate content ideas from Google News only. Search for recent news articles "
                "related to a topic using RSS feeds."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="generate_script",
            description=(
                "Generate a monologue script based on a topic using OpenRouter or Groq. "
                "The script will be tailored to the specified duration and style. "
                "Automatically falls back to alternative provider if primary fails."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The main topic or subject for the script"
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Target duration of the script in seconds"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: from config based on provider)",
                        "default": None
                    },
                    "style": {
                        "type": "string",
                        "description": "Style/tone of the script (default: 'informative and engaging')",
                        "default": "informative and engaging"
                    },
                    "trending_info": {
                        "type": "string",
                        "description": "Optional context from trending data to incorporate",
                        "default": None
                    },
                    "provider": {
                        "type": "string",
                        "description": f"Inference provider: 'openrouter' or 'groq' (default: {config.inference_provider})",
                        "enum": ["openrouter", "groq"],
                        "default": None
                    }
                },
                "required": ["topic", "duration_seconds"]
            }
        ),
        Tool(
            name="generate_script_from_ideas",
            description=(
                "Generate a script based on aggregated ideas data from generate_ideas(). "
                "This tool automatically incorporates trending information from multiple sources. "
                "Uses OpenRouter or Groq with automatic fallback."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ideas_data": {
                        "type": "object",
                        "description": "Output from generate_ideas() function"
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Target duration of the script in seconds"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: from config based on provider)",
                        "default": None
                    },
                    "style": {
                        "type": "string",
                        "description": "Style/tone of the script (default: 'informative and engaging')",
                        "default": "informative and engaging"
                    },
                    "provider": {
                        "type": "string",
                        "description": f"Inference provider: 'openrouter' or 'groq' (default: {config.inference_provider})",
                        "enum": ["openrouter", "groq"],
                        "default": None
                    }
                },
                "required": ["ideas_data", "duration_seconds"]
            }
        ),
        Tool(
            name="generate_complete_script",
            description=(
                "Generate a complete script in one step: automatically fetches trending topics "
                "from Reddit, YouTube, and Google News, then generates a script incorporating that information. "
                "Perfect for agents - no need to orchestrate multiple tool calls. "
                "This is the recommended tool for generating scripts from a topic."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to research and create a script about (e.g., 'AI', 'climate change')"
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Target duration of the script in seconds"
                    },
                    "provider": {
                        "type": "string",
                        "description": f"Inference provider: 'openrouter' or 'groq' (default: {config.inference_provider})",
                        "enum": ["openrouter", "groq"],
                        "default": None
                    },
                    "style": {
                        "type": "string",
                        "description": "Style/tone of the script (default: 'informative and engaging')",
                        "default": "informative and engaging"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of items to fetch per source (default: 3)",
                        "default": 3
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: from config based on provider)",
                        "default": None
                    }
                },
            "required": ["topic", "duration_seconds"]
        }
    ),
    
    # Voice Generation Tools
        Tool(
            name="generate_complete_content",
            description=(
                "Complete end-to-end workflow: Generate ideas, script, and audio with voice cloning/reuse. "
                "AUTOMATIC CONTEXT FETCHING: This tool automatically fetches trending topics from Reddit, "
                "YouTube, and News - no separate tool calls needed. Then generates a script incorporating "
                "those trends, and generates audio. Can clone a new voice from video OR reuse an existing "
                "voice by ID or name. Perfect for complete content creation in ONE CALL - everything happens "
                "automatically internally. NO TOOL CHAINING NEEDED."
            ),
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to research and create content about"
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Target duration of the script in seconds"
                },
                "video_path": {
                    "type": "string",
                    "description": "Path to video file for voice cloning (optional if voice_id or voice_name provided)"
                },
                "provider": {
                    "type": "string",
                    "description": f"Inference provider: 'openrouter' or 'groq' (default: {config.inference_provider})",
                    "enum": ["openrouter", "groq"]
                },
                "style": {
                    "type": "string",
                    "description": "Style/tone of the script (default: 'informative and engaging')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of items to fetch per source (default: 3)"
                },
                "model": {
                    "type": "string",
                    "description": "Model to use (default: from config based on provider)"
                },
                "output_audio_path": {
                    "type": "string",
                    "description": "Optional path for output audio file (default: temp file)"
                },
                "voice_id": {
                    "type": "string",
                    "description": "Optional: existing ElevenLabs voice ID to reuse (skips cloning)"
                },
                "voice_name": {
                    "type": "string",
                    "description": "Optional: name of existing voice to search for and reuse (skips cloning if found)"
                }
            },
            "required": ["topic", "duration_seconds"]
        }
    ),
    Tool(
        name="generate_script_with_audio",
        description=(
            "Generate script from trending data and create audio with voice cloning/reuse. "
            "Takes trending topics data, generates a script, and generates audio. "
            "Can clone a new voice from video OR reuse an existing voice by ID or name. "
            "Use when you already have trending topics."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "ideas_data": {
                    "type": "object",
                    "description": "Output from generate_ideas() function"
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Target duration of the script in seconds"
                },
                "video_path": {
                    "type": "string",
                    "description": "Path to video file for voice cloning (optional if voice_id or voice_name provided)"
                },
                "provider": {
                    "type": "string",
                    "description": f"Inference provider: 'openrouter' or 'groq' (default: {config.inference_provider})",
                    "enum": ["openrouter", "groq"]
                },
                "style": {
                    "type": "string",
                    "description": "Style/tone of the script (default: 'informative and engaging')"
                },
                "model": {
                    "type": "string",
                    "description": "Model to use (default: from config based on provider)"
                },
                "output_audio_path": {
                    "type": "string",
                    "description": "Optional path for output audio file (default: temp file)"
                },
                "voice_id": {
                    "type": "string",
                    "description": "Optional: existing ElevenLabs voice ID to reuse (skips cloning)"
                },
                "voice_name": {
                    "type": "string",
                    "description": "Optional: name of existing voice to search for and reuse (skips cloning if found)"
                }
            },
            "required": ["ideas_data", "duration_seconds"]
        }
    ),
    Tool(
        name="generate_audio_from_script",
        description=(
            "Generate audio from a script using voice cloning/reuse. "
            "Simplest tool - takes a script and generates audio. "
            "Can clone a new voice from video OR reuse an existing voice by ID or name. "
            "Use when you already have a script ready."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The script text to convert to audio"
                },
                "video_path": {
                    "type": "string",
                    "description": "Path to video file for voice cloning (optional if voice_id or voice_name provided)"
                },
                "output_audio_path": {
                    "type": "string",
                    "description": "Optional path for output audio file (default: temp file)"
                },
                "voice_id": {
                    "type": "string",
                    "description": "Optional: existing ElevenLabs voice ID to reuse (skips cloning)"
                },
                "voice_name": {
                    "type": "string",
                    "description": "Optional: name of existing voice to search for and reuse (skips cloning if found)"
                }
            },
            "required": ["script"]
        }
    ),
    
    # Voice Management Tools
    Tool(
        name="list_all_voices",
        description=(
            "List all voices in the ElevenLabs account. "
            "Returns voice IDs, names, categories, and descriptions. "
            "Useful for discovering available voices to reuse."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="find_voice_by_name",
        description=(
            "Find a voice by name in the ElevenLabs account. "
            "Returns the voice ID and full details if found. "
            "Useful for getting the ID of a specific voice to reuse."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "voice_name": {
                    "type": "string",
                    "description": "Name of the voice to search for"
                }
            },
            "required": ["voice_name"]
        }
    ),
    Tool(
        name="generate_video_from_image_audio",
        description=(
            "Generate a talking head video from an image and audio file using D-ID. "
            "This is the basic video generation tool - provide existing image and audio files. "
            "Perfect for when you already have prepared assets."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file (jpg/png)"
                },
                "audio_path": {
                    "type": "string",
                    "description": "Path to the audio file (mp3/wav)"
                },
                "output_video_path": {
                    "type": "string",
                    "description": "Optional output path for the video (default: output/video/)"
                }
            },
            "required": ["image_path", "audio_path"]
        }
    ),
    Tool(
        name="generate_video_from_video",
        description=(
            "Generate a talking head video by extracting a frame and audio from a source video. "
            "Automatically extracts a frame (at 2 seconds) to use as the image, "
            "and can use either the video's audio or a provided audio file. "
            "Useful for creating videos from existing video samples."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the source video file"
                },
                "audio_path": {
                    "type": "string",
                    "description": "Optional audio file path. If not provided, extracts audio from the video."
                },
                "output_video_path": {
                    "type": "string",
                    "description": "Optional output path for the video (default: output/video/)"
                },
                "frame_timestamp": {
                    "type": "number",
                    "description": "Timestamp in seconds to extract the frame (default: 2.0)"
                }
            },
            "required": ["video_path"]
        }
    ),
        Tool(
            name="generate_complete_video",
            description=(
                "Complete end-to-end content video generation workflow. "
                "AUTOMATIC CONTEXT FETCHING: This tool automatically does everything in ONE CALL: "
                "1. Automatically fetches trending topics from Reddit, YouTube, and Google News "
                "2. Automatically generates a script based on the trends "
                "3. Automatically clones voice from video (or reuses existing voice) "
                "4. Automatically generates audio from script "
                "5. Automatically extracts a frame from video "
                "6. Automatically creates talking head video with D-ID. "
                "Perfect for agents - complete content creation from topic to video in ONE CALL. "
                "NO TOOL CHAINING NEEDED - all context fetching happens automatically internally."
            ),
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to research and create content about"
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Target duration of the script/video in seconds"
                },
                "video_path": {
                    "type": "string",
                    "description": "Source video for voice cloning and face extraction"
                },
                "provider": {
                    "type": "string",
                    "description": "Inference provider: 'groq' or 'openrouter' (default: from config)"
                },
                "style": {
                    "type": "string",
                    "description": "Script style/tone (default: 'informative and engaging')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of items to fetch per source (default: 3)"
                },
                "model": {
                    "type": "string",
                    "description": "Model to use (default: from config based on provider)"
                },
                "voice_name": {
                    "type": "string",
                    "description": "Optional voice name to search for and reuse"
                },
                "voice_id": {
                    "type": "string",
                    "description": "Optional existing voice ID to reuse (skips cloning)"
                },
                "output_video_path": {
                    "type": "string",
                    "description": "Optional output path for the video (default: output/video/)"
                },
                "frame_timestamp": {
                    "type": "number",
                    "description": "Timestamp to extract frame from video (default: 2.0s)"
                }
            },
            "required": ["topic", "duration_seconds", "video_path"]
        }
    ),
    Tool(
        name="analyze_query",
        description=(
            "Analyze a user query to understand intent, topics, and context needs. "
            "Returns structured analysis with recommended actions. "
            "This tool helps understand what context might be needed for a query."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's query to analyze"
                }
            },
            "required": ["query"]
        }
    )
    ]


# ============================================================================
# MCP PROMPT HANDLERS - Automatic Context Injection
# ============================================================================

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompt templates with automatic context injection."""
    return [
        Prompt(
            name="trending_analysis",
            description=(
                "Analyze trending topics with automatic context injection. "
                "When used, automatically fetches latest trending data from Reddit, YouTube, and News, "
                "then enriches the prompt with context. NO TOOL CALLS NEEDED - context is automatically included."
            ),
            arguments=[
                PromptArgument(
                    name="topic",
                    description="The topic to analyze trends for (e.g., 'AI', 'climate change')",
                    required=True
                ),
                PromptArgument(
                    name="query",
                    description="Optional specific query about the topic",
                    required=False
                )
            ]
        ),
        Prompt(
            name="script_generation",
            description=(
                "Generate a script with automatic context injection. "
                "When used, automatically fetches trending data first, then provides enriched prompt for script generation. "
                "NO TOOL CALLS NEEDED - context is automatically included."
            ),
            arguments=[
                PromptArgument(
                    name="topic",
                    description="The topic to create a script about",
                    required=True
                ),
                PromptArgument(
                    name="duration_seconds",
                    description="Target duration of the script in seconds",
                    required=False
                ),
                PromptArgument(
                    name="style",
                    description="Script style (e.g., 'informative', 'engaging', 'funny')",
                    required=False
                ),
                PromptArgument(
                    name="query",
                    description="Optional specific query or requirements",
                    required=False
                )
            ]
        ),
        Prompt(
            name="content_creation",
            description=(
                "Complete content creation with automatic context injection. "
                "When used, automatically fetches all necessary context for end-to-end content creation. "
                "NO TOOL CALLS NEEDED - context is automatically included."
            ),
            arguments=[
                PromptArgument(
                    name="topic",
                    description="The topic for content creation",
                    required=True
                ),
                PromptArgument(
                    name="query",
                    description="User's content creation request",
                    required=False
                )
            ]
        ),
        Prompt(
            name="query_with_context",
            description=(
                "Generic prompt that automatically analyzes any query and injects relevant context. "
                "When used, automatically determines what context is needed and fetches it. "
                "NO TOOL CALLS NEEDED - context is automatically included."
            ),
            arguments=[
                PromptArgument(
                    name="query",
                    description="The user's query",
                    required=True
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, Any]):
    """Get a prompt with automatic context injection."""
    loop = asyncio.get_event_loop()
    
    middleware = get_middleware()
    
    # MCP protocol sends arguments as strings, so we need to convert them
    def parse_arg(key: str, default: Any, arg_type: type = str) -> Any:
        value = arguments.get(key, default)
        if value is None or value == "":
            return default
        if arg_type == int:
            try:
                return int(value) if isinstance(value, (str, int)) else default
            except (ValueError, TypeError):
                return default
        elif arg_type == float:
            try:
                return float(value) if isinstance(value, (str, int, float)) else default
            except (ValueError, TypeError):
                return default
        return str(value) if value else default
    
    if name == "trending_analysis":
        topic = parse_arg("topic", "")
        query = parse_arg("query", f"What's trending about {topic}?")
        
        # Automatically fetch and inject context
        enriched_query = await loop.run_in_executor(
            _executor,
            lambda: enrich_query_with_context(query)
        )
        middleware.track_prompt_enrichment(name, query)
        
        return GetPromptResult(
            description="Trending analysis prompt with automatic context",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=enriched_query
                    )
                )
            ]
        )
    
    elif name == "script_generation":
        topic = parse_arg("topic", "")
        duration = parse_arg("duration_seconds", 60, int)
        style = parse_arg("style", "informative and engaging")
        query = parse_arg("query", f"Generate a {duration}-second {style} script about {topic}")
        
        # Automatically fetch and inject context
        enriched_query = await loop.run_in_executor(
            _executor,
            lambda: enrich_query_with_context(query)
        )
        middleware.track_prompt_enrichment(name, query)
        
        # Add script generation instructions
        full_prompt = f"""{enriched_query}

Please generate a {duration}-second script in a {style} style based on the context above."""
        
        return GetPromptResult(
            description="Script generation prompt with automatic context",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=full_prompt
                    )
                )
            ]
        )
    
    elif name == "content_creation":
        topic = parse_arg("topic", "")
        query = parse_arg("query", f"Create content about {topic}")
        
        # Automatically fetch and inject context
        enriched_query = await loop.run_in_executor(
            _executor,
            lambda: enrich_query_with_context(query)
        )
        middleware.track_prompt_enrichment(name, query)
        
        return GetPromptResult(
            description="Content creation prompt with automatic context",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=enriched_query
                    )
                )
            ]
        )
    
    elif name == "query_with_context":
        query = parse_arg("query", "")
        
        # Automatically analyze and inject context
        enriched_query = await loop.run_in_executor(
            _executor,
            lambda: enrich_query_with_context(query)
        )
        middleware.track_prompt_enrichment(name, query)
        
        return GetPromptResult(
            description="Generic query prompt with automatic context",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=enriched_query
                    )
                )
            ]
        )
    
    else:
        raise ValueError(f"Unknown prompt: {name}")


# ============================================================================
# MCP RESOURCE HANDLERS - Automatic Data Availability
# ============================================================================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources (automatically maintained data)."""
    resources = [
        Resource(
            uri="trending://topics/current",
            name="Current Trending Topics",
            description="Currently trending topics across all sources (auto-updated)",
            mimeType="application/json"
        )
    ]
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> TextResourceContents:
    """Read a resource (returns pre-fetched, automatically maintained data)."""
    uri_str = uri
    loop = asyncio.get_event_loop()
    middleware = get_middleware()
    middleware.track_resource_access(uri_str)
    
    # Parse resource URI
    if uri_str.startswith("trending://topics/"):
        # Extract topic from URI
        topic = uri_str.replace("trending://topics/", "").strip()
        
        if topic == "current":
            content = json.dumps({
                "message": "Use trending://topics/{topic} to get specific topic data",
                "example": "trending://topics/AI"
            }, indent=2)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
        
        # Fetch or get from cache
        cache = get_cache()
        cache_key = f"trending:{topic}:reddit_youtube_news"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            content = json.dumps(cached_data, indent=2, default=str)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
        
        # Fetch fresh data
        try:
            ideas_data = await loop.run_in_executor(
                _executor,
                lambda: generate_ideas(topic=topic, limit=5)
            )
            # Cache it
            cache.set(cache_key, ideas_data, ttl=3600.0)
            content = json.dumps(ideas_data, indent=2, default=str)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
        except Exception as e:
            content = json.dumps({"error": str(e)}, indent=2)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
    
    elif uri_str.startswith("content://voices/"):
        # Extract voice name
        voice_name = uri_str.replace("content://voices/", "").strip()
        
        # Get voice info
        try:
            voice_result = await loop.run_in_executor(
                _executor,
                lambda: find_voice_by_name(voice_name)
            )
            content = json.dumps(voice_result, indent=2, default=str)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
        except Exception as e:
            content = json.dumps({"error": str(e)}, indent=2)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
    
    elif uri_str == "content://voices":
        # List all voices
        try:
            voices_result = await loop.run_in_executor(
                _executor,
                lambda: list_all_voices()
            )
            content = json.dumps(voices_result, indent=2, default=str)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
        except Exception as e:
            content = json.dumps({"error": str(e)}, indent=2)
            return TextResourceContents(
                uri=uri_str,
                text=content,
                mimeType="application/json"
            )
    
    else:
        content = json.dumps({"error": f"Unknown resource: {uri_str}"}, indent=2)
        return TextResourceContents(
            uri=uri_str,
            text=content,
            mimeType="application/json"
        )


# ============================================================================
# TOOL HANDLERS
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution."""
    try:
        # Run synchronous tool functions in a thread pool to avoid blocking
        # and prevent PRAW warnings about async environments
        loop = asyncio.get_event_loop()
        
        if name == "generate_ideas":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_ideas(
                    topic=arguments["topic"],
                    limit=arguments.get("limit", 10)
                )
            )
        
        elif name == "generate_reddit_ideas":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_reddit_ideas(
                    topic=arguments["topic"],
                    subreddit=arguments.get("subreddit", "all"),
                    limit=arguments.get("limit", 10)
                )
            )
        
        elif name == "generate_youtube_ideas":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_youtube_ideas(
                    topic=arguments["topic"],
                    order=arguments.get("order", "viewCount"),
                    limit=arguments.get("limit", 10)
                )
            )
        
        elif name == "generate_news_ideas":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_news_ideas(
                    topic=arguments["topic"],
                    limit=arguments.get("limit", 10)
                )
            )
        
        elif name == "generate_script":
            # Script generation may involve API calls, run in executor
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_script(
                    topic=arguments["topic"],
                    duration_seconds=arguments["duration_seconds"],
                    model=arguments.get("model"),
                    style=arguments.get("style", "informative and engaging"),
                    trending_info=arguments.get("trending_info"),
                    provider=arguments.get("provider")
                )
            )
        
        elif name == "generate_script_from_ideas":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_script_from_ideas(
                    ideas_data=arguments["ideas_data"],
                    duration_seconds=arguments["duration_seconds"],
                    model=arguments.get("model"),
                    style=arguments.get("style", "informative and engaging"),
                    provider=arguments.get("provider")
                )
            )
        
        elif name == "generate_complete_script":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_complete_script(
                    topic=arguments["topic"],
                    duration_seconds=arguments["duration_seconds"],
                    provider=arguments.get("provider"),
                    style=arguments.get("style", "informative and engaging"),
                    limit=arguments.get("limit", 3),
                    model=arguments.get("model")
                )
            )
        
        elif name == "generate_complete_content":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_complete_content(
                    topic=arguments["topic"],
                    duration_seconds=arguments["duration_seconds"],
                    video_path=arguments.get("video_path"),
                    provider=arguments.get("provider"),
                    style=arguments.get("style", "informative and engaging"),
                    limit=arguments.get("limit", 3),
                    model=arguments.get("model"),
                    output_audio_path=arguments.get("output_audio_path"),
                    voice_id=arguments.get("voice_id"),
                    voice_name=arguments.get("voice_name")
                )
            )
        
        elif name == "generate_script_with_audio":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_script_with_audio(
                    ideas_data=arguments["ideas_data"],
                    duration_seconds=arguments["duration_seconds"],
                    video_path=arguments.get("video_path"),
                    provider=arguments.get("provider"),
                    style=arguments.get("style", "informative and engaging"),
                    model=arguments.get("model"),
                    output_audio_path=arguments.get("output_audio_path"),
                    voice_id=arguments.get("voice_id"),
                    voice_name=arguments.get("voice_name")
                )
            )
        
        elif name == "generate_audio_from_script":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_audio_from_script(
                    script=arguments["script"],
                    video_path=arguments.get("video_path"),
                    output_audio_path=arguments.get("output_audio_path"),
                    voice_id=arguments.get("voice_id"),
                    voice_name=arguments.get("voice_name")
                )
            )
        
        elif name == "list_all_voices":
            result = await loop.run_in_executor(
                _executor,
                lambda: list_all_voices()
            )
        
        elif name == "find_voice_by_name":
            result = await loop.run_in_executor(
                _executor,
                lambda: find_voice_by_name(
                    voice_name=arguments["voice_name"]
                )
            )
        
        elif name == "generate_video_from_image_audio":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_video_from_image_audio(
                    image_path=arguments["image_path"],
                    audio_path=arguments["audio_path"],
                    output_video_path=arguments.get("output_video_path")
                )
            )
        
        elif name == "generate_video_from_video":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_video_from_video(
                    video_path=arguments["video_path"],
                    audio_path=arguments.get("audio_path"),
                    output_video_path=arguments.get("output_video_path"),
                    frame_timestamp=arguments.get("frame_timestamp", 2.0)
                )
            )
        
        elif name == "generate_complete_video":
            result = await loop.run_in_executor(
                _executor,
                lambda: generate_complete_video(
                    topic=arguments["topic"],
                    duration_seconds=arguments["duration_seconds"],
                    video_path=arguments["video_path"],
                    provider=arguments.get("provider"),
                    style=arguments.get("style", "informative and engaging"),
                    limit=arguments.get("limit", 3),
                    model=arguments.get("model"),
                    voice_name=arguments.get("voice_name"),
                    voice_id=arguments.get("voice_id"),
                    output_video_path=arguments.get("output_video_path"),
                    frame_timestamp=arguments.get("frame_timestamp", 2.0)
                )
            )
        
        elif name == "analyze_query":
            result = await loop.run_in_executor(
                _executor,
                lambda: analyze_query_intent(arguments["query"])
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Return the result as JSON
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    # Check configuration
    missing_configs = config.get_missing_configs()
    if missing_configs:
        print(f"Warning: Missing configuration for: {', '.join(missing_configs)}")
        print("Some tools may not work without proper API keys.")
        print("Please check your .env file or environment variables.\n")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

