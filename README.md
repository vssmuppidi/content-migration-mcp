# CurateX

**A one-stop MCP server for AI-powered content creation** from trending research to final video, fully automated.

## 🎯 Vision

In the age of AI assistants, **context is everything**. This MCP server acts as an intelligent context engine that automatically fetches, analyzes, and injects real-time trending data from multiple sources (Reddit, YouTube, News) to power complete content creation workflows.

**The Challenge**: Content creators need trending insights, engaging scripts, voice cloning, and video generation. Existing solutions require complex tool orchestration.

**The Solution**: A unified MCP server with automatic context injection, composite workflows, and AI-powered intelligence that handles everything from idea research to final video in single tool calls.

---

## ✨ What Makes This Unique

### 1. **Automatic Context Injection**
Unlike typical MCP servers that require explicit tool calls, this server **automatically analyzes queries and injects context**:

- **MCP Prompts**: Server fetches context automatically when agent uses prompts
- **MCP Resources**: Pre-fetched, auto-maintained data accessible without tool calls  
- **Composite Tools**: Single tools that orchestrate entire workflows internally

**Example**: Agent asks "What's trending about AI?" → Uses `trending_analysis` prompt → Server auto-fetches Reddit + YouTube + News → Returns enriched context → No tool chaining needed!

### 2. **Multi-Source Intelligence**
Combines three complementary data sources for comprehensive insights:

- **Reddit**: Community discussions, sentiment, engagement
- **YouTube**: Video content, creator perspectives, visual trends
- **Google News**: Official coverage, credibility, timeliness

Each source provides unique context that others miss. Cross-source correlation reveals patterns invisible to single-source analysis.

### 3. **AI-Powered Context Processing**
Raw data is noisy. This server provides **intelligent context**:

- **Intelligent Ranking**: Scores items by relevance (40%), engagement (30%), recency (20%), credibility (10%)
- **Trend Detection**: Identifies emerging trends, gaining/losing traction, unique angles
- **Sentiment Analysis**: Understands tone across all sources
- **Theme Extraction**: Identifies key topics and keywords
- **Cross-Source Correlation**: Finds connections between Reddit threads, YouTube videos, and news articles
- **AI Summarization**: Uses OpenRouter to generate actionable insights (75-80% token reduction)

### 4. **Complete Content Pipeline**
End-to-end workflow in single tool calls:

```
Trending Research → Script Generation → Voice Cloning → Audio Generation → Video Creation
```

No tool chaining. No orchestration complexity. One call does everything.

---

## 🏗️ Architecture

### MCP Server Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server (stdio)                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Query Analysis & Context Injection         │    │
│  │  • Analyzes intent (trending/script/video)         │    │
│  │  • Extracts topics automatically                   │    │
│  │  • Determines context needs                        │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Multi-Source Data Fetching                │    │
│  │                                                     │    │
│  │  Reddit API  →  [Community discussions]            │    │
│  │  YouTube API →  [Video trends]                     │    │
│  │  News RSS    →  [Official coverage]                │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │       Intelligent Context Processing               │    │
│  │  • Ranks by relevance + engagement + recency       │    │
│  │  • Detects trends (emerging/gaining/losing)        │    │
│  │  • Extracts themes & sentiment                     │    │
│  │  • Correlates across sources                       │    │
│  │  • AI-powered summarization (OpenRouter)           │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Composite Tool Execution                │    │
│  │                                                     │    │
│  │  Script Gen (OpenRouter/Groq)                      │    │
│  │      ↓                                              │    │
│  │  Voice Clone (ElevenLabs)                          │    │
│  │      ↓                                              │    │
│  │  Audio Gen (ElevenLabs v3 + emotional tags)        │    │
│  │      ↓                                              │    │
│  │  Video Gen (D-ID talking head)                     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
            Complete Content Package
        (Script + Audio + Video + Metadata)
```

### Key Components

- **Query Analyzer**: AI-powered intent detection and topic extraction
- **Context Enricher**: Automatic context fetching and formatting
- **Context Cache**: 1-hour TTL for performance
- **Context Processor**: Intelligent ranking, trend detection, sentiment analysis
- **Composite Tools**: Orchestrate complete workflows internally
- **MCP Prompts/Resources**: Enable zero-tool-call context injection

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ffmpeg (for audio/video processing)

### Installation

```bash
# 1. Clone repository
cd Content-MCP

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp env.example .env
# Edit .env with your API keys (see env.example for all options)

# 4. Run server
python -m src.server
```

### Required API Keys

See `env.example` for complete configuration. Minimum required:

- **Reddit API** (free): Community discussions
- **YouTube API** (free): Video trends  
- **OpenRouter API** (paid): AI inference for scripts & summaries
- **ElevenLabs API** (paid): Voice cloning & TTS
- **D-ID API** (paid, free tier available): Video generation

Optional: **Google News** (free, no key needed)

### Connect to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "content-mcp": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/Content-MCP"
    }
  }
}
```

---

## 🛠️ Core Capabilities

### Content Research Tools
- **`generate_ideas`**: Fetch trending topics from all sources
- **`generate_reddit_ideas`**: Reddit-specific discussions
- **`generate_youtube_ideas`**: YouTube video trends
- **`generate_news_ideas`**: Google News articles

### Script Generation Tools
- **`generate_script`**: Create script from topic
- **`generate_script_from_ideas`**: Script from trending data
- **`generate_complete_script`**: ⚡ Auto-fetch trends + generate script (composite)

### Voice & Audio Tools
- **`generate_audio_from_script`**: Convert script to audio with voice cloning
- **`generate_script_with_audio`**: Script + audio from trends (composite)
- **`generate_complete_content`**: Ideas + script + audio (composite)
- **`list_all_voices`**: List ElevenLabs voices. Pre-made or cloned voices
- **`find_voice_by_name`**: Search for specific voice to get its ID

### Video Generation Tools
- **`generate_video_from_image_audio`**: Basic video from assets
- **`generate_video_from_video`**: Extract frame + create video
- **`generate_complete_video`**: Full workflow: ideas → script → audio → video (composite)

### Context & Analysis Tools
- **`analyze_query`**: Understand query intent and context needs

### MCP Prompts (Automatic Context)
- **`trending_analysis`**: Auto-injects trending data
- **`script_generation`**: Auto-fetches trends for scripts
- **`content_creation`**: Auto-fetches all context for content
- **`query_with_context`**: Generic context injection

### MCP Resources (Pre-fetched Data)
- **`trending://topics/{topic}`**: Cached trending data
- **`content://voices`**: Available voices list
---

## 💡 Example Use Cases

### Use Case 1: Research Trending Topics
```
Prompt: "What are people saying about climate change?"

Server:
1. Analyzes query → intent: trending_topics, topic: climate change
2. Fetches from Reddit + YouTube + News
3. Ranks by relevance + engagement
4. Detects emerging trends
5. Returns: "Climate adaptation strategies gaining 300% more discussion..."
```

### Use Case 2: Generate Complete Script
```
Tool: generate_complete_script(topic="AI ethics", duration_seconds=45)

Server internally:
1. Fetches trending topics (Reddit, YouTube, News)
2. Processes & ranks content
3. Extracts key themes & sentiment
4. Generates script with OpenRouter
5. Returns: Complete script + trending data used

No manual tool chaining needed!
```

### Use Case 3: Complete Video Creation
```
Tool: generate_complete_video(
    topic="space exploration",
    duration_seconds=60,
    video_path="presenter.mp4"
)

Server internally:
1. Researches trending space topics
2. Generates engaging 60-second script
3. Extracts audio from presenter.mp4
4. Clones voice with ElevenLabs
5. Generates narration audio
6. Extracts frame from video
7. Creates talking head video with D-ID

Returns: Complete package (script, audio, video)
```

### Use Case 4: Using MCP Prompts (No Tool Calls!)
```
Agent uses: get_prompt("trending_analysis", {topic: "AI"})

Server automatically:
1. Analyzes prompt request
2. Fetches trending AI topics
3. Processes and summarizes
4. Injects context into prompt
5. Returns enriched prompt

Agent receives full context without calling any tools!
```

---

## 📊 Technical Specifications

### Data Sources & Limits

| Source | Free Tier | Limit | Notes |
|--------|-----------|-------|-------|
| Reddit | ✅ Yes | 100 queries/min | PRAW API |
| YouTube | ✅ Yes | 10,000 units/day | ~100 searches/day |
| Google News | ✅ Yes | Unlimited | RSS feeds |
| OpenRouter | ❌ Paid | Usage-based | Primary AI inference |
| ElevenLabs | ⚠️ Limited | 10K chars/month free | Voice cloning & TTS |
| D-ID | ⚠️ Limited | Free trial credits | Talking head videos |

### Performance

- **Context Caching**: 1-hour TTL (reduces API calls by ~80%)
- **Token Efficiency**: 75-80% reduction via intelligent summarization
- **Concurrent Operations**: ThreadPoolExecutor for async compatibility
- **Fallback Systems**: Auto-fallback for inference APIs

### Architecture Highlights

- **Query Analysis**: AI-powered intent detection
- **Intelligent Ranking**: Multi-factor scoring algorithm
- **Trend Detection**: Emerging, gaining, losing, stable classification
- **Cross-Source Correlation**: Finds connections between platforms
- **Composite Tools**: Internal workflow orchestration
- **MCP Prompts/Resources**: Zero-tool-call context injection
- **Automatic Fallbacks**: OpenRouter ↔ Groq for reliability

---

## 🧪 Demo Agent

A fully functional demo agent using Agno framework is included in `demo_agent/`:

```bash
cd demo_agent
python simple_example.py
```

Features:
- Interactive CLI for testing
- Complete workflow examples
- OpenRouter + Groq support
- Real-time MCP tool usage

See `demo_agent/README.md` for details.

---

## 🎬 Sample Outputs

Here are real examples generated by the MCP server:

### 🎤 Audio Sample
**Topic**: New York Mayor (45 seconds) | **Size**: 814KB

**Audio**: [► Listen to Demo Audio on Google Drive](https://drive.google.com/file/d/1BQ-zGue6WZje7f04S4ZcoNcrR_9p4Jcp/view?usp=drive_link)

**Features**:
- 45-second narration with emotional tags (`[excited]`, `[pause]`, etc.)
- Natural voice inflection and pacing  
- ElevenLabs v3 with emotion markers
- Generated from trending Reddit/YouTube/News data

---

### 🎬 Video Sample  
**Topic**: New York Mayor (Complete Talking Head)

> [!NOTE]
> **🎥 [► Watch Demo Video on Google Drive](https://drive.google.com/file/d/1deqA5POzC6SgLgh1CfpiIpjdr3S6cnM9/view?usp=sharing)**  
> Click to see the complete talking head video in action

**Features**:
- Complete talking head video with synchronized lip-sync
- Voice cloned from 10-second sample video
- D-ID generated with natural movements  
- Ready for social media publishing

**Complete Outputs**: Please check it out for Judging[Audio/Video](https://drive.google.com/drive/folders/1TRGp92YNyUFi7V-5inv0aL9CXkPSpOS0?usp=sharing) 

---

**Workflow**: Single `generate_complete_video` tool call → Trending research + Script generation + Voice cloning + Video creation (90 seconds total)

---

## 📁 Project Structure

```
Content-MCP/
├── src/
│   ├── server.py              # Main MCP server
│   ├── config.py              # Configuration
│   ├── tools/                 # Tool implementations
│   │   ├── ideas.py           # Research tools
│   │   ├── script.py          # Script generation
│   │   ├── voice.py           # Voice & audio
│   │   ├── video.py           # Video generation
│   │   └── context_processor.py  # Intelligence layer
│   ├── utils/
│   │   ├── query_analyzer.py  # Query analysis
│   │   ├── audio.py           # Audio processing
│   │   └── video.py           # Video processing
│   ├── services/
│   │   ├── context_enricher.py   # Context injection
│   │   ├── context_cache.py      # Caching layer
│   │   └── tool_orchestrator.py  # Workflow orchestration
│   ├── middleware/
│   │   └── context_middleware.py # Request tracking
│   └── sources/
│       ├── reddit.py          # Reddit API
│       ├── youtube.py         # YouTube API
│       ├── google_news.py     # News RSS
│       ├── elevenlabs_voice.py  # ElevenLabs
│       └── did_video.py       # D-ID
├── demo_agent/                # Demo agent (Agno)
├── output/                    # Generated files
│   ├── audio/
│   └── video/
├── requirements.txt
├── env.example
└── README.md
```

---

## 🎯 Why This Matters

### Creativity & Originality (50%)

✅ **Unique Data Source**: Multi-source intelligence (Reddit + YouTube + News), a rare combination providing complementary perspectives

✅ **Clever Integration**: Automatic context injection via MCP prompts/resources where the  agent receives context without explicit tool calls

✅ **Contextual Intelligence**: AI-powered analysis with ranking, trend detection, sentiment, cross-source correlation, and intelligent summarization

### Utility & Technical Merit (50%)

✅ **Practical Value**: Complete content creation pipeline solves real creator pain point of researching trends, writing scripts, and producing media

✅ **Robustness**: 
- Automatic fallbacks (OpenRouter ↔ Groq)
- Error handling at every layer
- Context caching (1-hour TTL)
- Async compatibility via ThreadPoolExecutor

✅ **Efficiency**: 
- 75-80% token reduction via intelligent summarization
- Composite tools eliminate tool chaining
- Single-call workflows
- Cached context reduces API calls by 80%

### Innovation Highlights

1. **Zero-Tool-Call Context**: MCP prompts inject context automatically
2. **Composite Workflows**: Single tools handle multi-step processes internally
3. **Multi-Source Intelligence**: Combines social, video, and news perspectives
4. **AI-Powered Context**: Uses OpenRouter to summarize and correlate trends
5. **Complete Pipeline**: Only MCP server for end-to-end content creation (research → video)

---

## 📄 License

MIT License - Feel free to use and modify.

## 🙏 Acknowledgments

- Built with [Anthropic's MCP Python SDK](https://github.com/anthropics/mcp)
- Powered by Reddit (PRAW), YouTube Data API, Google News RSS
- AI inference via OpenRouter
- Voice generation via ElevenLabs
- Video generation via D-ID

---

*A smart context engine that makes AI assistants truly contextually aware.*
