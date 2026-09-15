# Content Creation Agent Demo

This demo showcases an AI agent built with [Agno](https://docs.agno.com/introduction) that connects to your Content MCP Server to create engaging content with voice generation capabilities.

## 🎯 What This Agent Can Do

- 📊 **Research Trending Topics**: Automatically fetch trending content from Reddit, YouTube, and Google News
- 📝 **Generate Scripts**: Create engaging scripts based on trending topics and custom requirements
- 🎤 **Voice Generation**: Clone voices and generate audio narrations
- 🔄 **Voice Management**: List, search, and reuse existing voices
- 💬 **Natural Conversation**: Chat naturally to request content creation tasks

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd demo_agent
pip install -r requirements.txt
```

### 2. Option A: Run with AgentOS UI (Recommended)

This starts the agent with a beautiful web interface for testing and monitoring:

```bash
python content_agent.py
```

Then open your browser to: **http://localhost:7777**

The AgentOS UI provides:
- 💬 Interactive chat interface
- 📊 Real-time monitoring
- 🔍 Tool call inspection
- 📝 Conversation history

### 3. Option B: Run Simple Examples

For quick testing without the UI:

```bash
python simple_example.py
```

This provides:
- Pre-built example workflows
- Interactive command-line chat
- Step-by-step demonstrations

## 📚 Usage Examples

### Example 1: Research Trending Topics

```python
agent.run("What are the top 5 trending topics about AI on Reddit?")
```

### Example 2: Generate a Script

```python
agent.run(
    "Create a 30-second script about machine learning trends. "
    "Research trending topics first, then write an engaging script."
)
```

### Example 3: List Available Voices

```python
agent.run("List all voices in my ElevenLabs account")
```

### Example 4: Complete Content Creation

```python
agent.run(
    "Create complete content about climate change: "
    "1. Research trending topics "
    "2. Generate a 45-second script "
    "3. Generate audio using my 'narrator' voice"
)
```

### Example 5: Voice Generation with Voice Name

```python
agent.run(
    "Generate audio for a 20-second script about AI trends "
    "using my 'test' voice. Research the trends first."
)
```

## 🛠️ Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Content Agent                         │
│                                                          │
│  Model: OpenRouter (gpt-oss-120b:exacto) with Groq backup│
│  Framework: Agno 2.0                                     │
│  Database: SQLite (conversation history)                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ MCP Protocol (stdio)
                  │
┌─────────────────▼───────────────────────────────────────┐
│              Content MCP Server                          │
│                                                          │
│  Tools Available:                                        │
│    • generate_ideas (all sources)                        │
│    • generate_reddit_ideas                               │
│    • generate_youtube_ideas                              │
│    • generate_news_ideas                                 │
│    • generate_script                                     │
│    • generate_script_from_ideas                          │
│    • generate_complete_script                            │
│    • generate_complete_content (ideas→script→audio)      │
│    • generate_script_with_audio                          │
│    • generate_audio_from_script                          │
│    • list_all_voices                                     │
│    • find_voice_by_name                                  │
└──────────────────────────────────────────────────────────┘
```

## 🎨 AgentOS UI Features

When you run with `content_agent.py`, you get:

1. **Chat Interface**: Natural conversation with your agent
2. **Tool Visibility**: See which MCP tools the agent uses
3. **Response Streaming**: Watch the agent think and respond in real-time
4. **History Management**: Review past conversations
5. **Session Management**: Multiple conversation threads

## 💡 Tips for Best Results

### For Content Generation:
- Be specific about the topic and target duration
- Ask the agent to research trending topics first
- Specify the style/tone you want (e.g., "casual", "professional", "engaging")

### For Voice Generation:
- List your voices first to see what's available
- Use voice names consistently for reuse
- Provide a video sample only when creating a new voice

### Example Prompts:
```
"Research trending AI topics and create a 30-second engaging script"
"List my voices, then generate audio for this script using my narrator voice"
"Create complete content about [topic] with my [voice_name] voice"
```

## 🔧 Configuration

### Inference Provider

The agent uses **OpenRouter** as the primary inference provider with **Groq** as a backup. This provides flexibility and reliability:

- **Primary**: OpenRouter (openai/gpt-oss-120b:exacto) - Fast, reliable, good for tool calling
- **Backup**: Groq (openai/gpt-oss-20b) - Automatically used if OpenRouter is unavailable

To use these providers, set at least one API key in your `.env` file:
```bash
OPENROUTER_API_KEY=your_key_here  # Primary
GROQ_API_KEY=your_key_here         # Backup (optional)
```

**Why gpt-oss-120b:exacto?**
- Cost-effective for your $10 budget
- Excellent at function calling and tool use
- Good balance of speed and quality
- Reliable for agent workflows

### Change the AI Model

Edit `content_agent.py` to use a different model or provider:

```python
# Use Claude instead
from agno.models.anthropic import Claude

content_agent = Agent(
    name="Content Creator",
    model=Claude(id="claude-sonnet-4-5"),
    # ... rest of config
)
```

```python
# Use a different OpenRouter model
model = OpenRouter(
    id="anthropic/claude-3.5-sonnet",  # More powerful model
    api_key=openrouter_api_key
)
```

### Customize Agent Behavior

Edit the `description` and `instructions` in `content_agent.py`:

```python
content_agent = Agent(
    # ...
    description="Your custom agent description",
    instructions=[
        "Custom instruction 1",
        "Custom instruction 2",
    ]
)
```

### Change the Port

```python
agent_os.serve(app="content_agent:app", port=8080)
```

## 🐛 Troubleshooting

### Agent can't connect to MCP server
- Ensure the MCP server dependencies are installed in the parent directory
- Check that all API keys are set in the `.env` file
- Verify the `cwd` path in the MCPTools configuration

### Voice generation fails
- Confirm `ELEVENLABS_API_KEY` is set in parent `.env`
- Check that ffmpeg is installed for video processing
- Ensure video file paths are absolute or relative to project root

### Tool calls not working
- Check that the MCP server runs successfully: `cd .. && python -m src`
- Verify all required environment variables are set
- Review error messages in the agent output

## 📖 Learn More

- [Agno Documentation](https://docs.agno.com/introduction)
- [Agno Examples](https://docs.agno.com/examples)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Content MCP Server](../README.md) - Your custom MCP server docs

## 🎯 Next Steps

1. **Try the Examples**: Run `python simple_example.py` to see the agent in action
2. **Open AgentOS**: Run `python content_agent.py` and open http://localhost:7777
3. **Customize**: Modify the agent's instructions to match your use case
4. **Experiment**: Try different prompts and workflows
5. **Build**: Create your own agent-based application!

---

**Need Help?** Check the [Agno Discord](https://discord.gg/agno) or [GitHub Issues](https://github.com/agno-agi/agno)

