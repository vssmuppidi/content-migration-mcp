# How to Test the MCP Server

## Understanding MCP Architecture

**MCP Server ≠ Standalone Application**

The MCP server is a **service provider**, not a standalone application. It needs an **AI Agent** to:
1. Accept natural language from users
2. Decide which MCP tools to call
3. Orchestrate the workflow
4. Present results to users

```
┌──────────────────────────────────────────────────────────┐
│  USER: "Generate a 30 sec script about Pluribus"         │
└────────────────────────┬─────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  AI AGENT (Agno/Claude/GPT)                              │
│  - Understands: User wants script generation             │
│  - Decides: Call generate_complete_script tool           │
│  - Calls: MCP Server with structured request             │
└────────────────────────┬─────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  MCP SERVER (Your Content MCP)                           │
│  - Receives: generate_complete_script(topic="Pluribus")  │
│  - Executes: Fetch trends → Generate script              │
│  - Returns: {"script": "...", "success": true}           │
└────────────────────────┬─────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  AI AGENT                                                 │
│  - Receives: MCP result                                  │
│  - Formats: Into natural language                        │
│  - Presents: To user                                     │
└────────────────────────┬─────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  USER: Gets final script!                                │
└──────────────────────────────────────────────────────────┘
```

---

## Testing Methods

### Method 1: Agno Agent (RECOMMENDED - Natural Language)

**What it does:** You give natural language prompts, agent automatically calls MCP tools

**How to use:**

```bash
# Activate environment
source .venv/bin/activate

# Run the Agno agent
cd demo_agent
python simple_example.py
```

**Example conversation:**
```
You: Generate a 30 second script about Pluribus Reactions
Agent: [Automatically calls generate_complete_script tool]
Agent: [Returns the generated script]

You: Now create audio using test.mp4 for the voice
Agent: [Automatically calls generate_audio_from_script]
Agent: [Returns audio file path]

You: Create a video from that
Agent: [Automatically calls generate_video_from_video]
Agent: [Returns video file path]
```

**Advantages:**
- ✅ Natural language input
- ✅ Agent decides which tools to call
- ✅ Can chain multiple operations
- ✅ This is how MCP is meant to be used!

---

### Method 2: Interactive Test (Manual Tool Calls)

**What it does:** You manually specify which tools to call

**How to use:**

```bash
source .venv/bin/activate
python interactive_test.py
```

**Commands:**

#### Complete Workflows (One Command):
```
complete-script "Pluribus Reactions"
# Does: Ideas → Script

complete-audio "Pluribus Reactions"  
# Does: Ideas → Script → Audio

complete-video "Pluribus Reactions"
# Does: Ideas → Script → Audio → Video
```

#### Manual Tool Calls:
```
tool generate_complete_script {"topic": "AI", "duration_seconds": 30}
tool generate_ideas {"topic": "AI", "limit": 5}
tool list_all_voices {}
```

#### Context Injection (Prompts):
```
prompt script_generation {"topic": "AI", "duration_seconds": "30"}
# Returns enriched prompt with context (for Challenge demonstration)
```

**Advantages:**
- ✅ Direct control over tool selection
- ✅ Good for debugging specific tools
- ✅ Can test prompts/resources separately

**Disadvantages:**
- ❌ Requires knowing exact tool names
- ❌ Manual JSON formatting
- ❌ Not how end-users would interact

---

## Which Method Should You Use?

### For Testing Natural Interaction:
**Use Agno Agent** (`demo_agent/simple_example.py`)
- This demonstrates how MCP servers are meant to be used
- Best for challenge submission videos
- Shows the full power of context injection

### For Debugging Specific Tools:
**Use Interactive Test** (`interactive_test.py`)
- Quick testing of individual tools
- Verify tool outputs
- Debug specific functionality

### For Challenge Submission:
**Show BOTH:**

1. **Context Injection** (via prompts):
   ```
   prompt script_generation {"topic": "AI"}
   → Shows automatic context fetching from Reddit/YouTube/News
   → Demonstrates "Contextual Intelligence"
   ```

2. **Natural Language** (via Agno agent):
   ```
   User: "Create a video about AI trends"
   → Agent automatically orchestrates complete workflow
   → Demonstrates real-world utility
   ```

---

## Complete Workflow Tools Available

Your MCP server has **3 complete workflow tools** that do everything in one call:

### 1. `generate_complete_script`
**Does:** Ideas → Script
```json
{
  "topic": "Pluribus Reactions",
  "duration_seconds": 30,
  "style": "informative and engaging"
}
```

### 2. `generate_complete_content`  
**Does:** Ideas → Script → Audio
```json
{
  "topic": "Pluribus Reactions",
  "duration_seconds": 30,
  "video_path": "test_content/test.mp4",
  "voice_name": "test_woman"
}
```

### 3. `generate_complete_video`
**Does:** Ideas → Script → Audio → Video
```json
{
  "topic": "Pluribus Reactions",
  "duration_seconds": 30,
  "video_path": "test_content/test.mp4",
  "voice_name": "test_woman"
}
```

**Each of these tools:**
- ✅ Automatically fetches trending data from Reddit, YouTube, News
- ✅ Generates AI-powered summary
- ✅ Creates content based on trends
- ✅ Returns complete result in one call

---

## Quick Start

### To test with natural language (BEST):
```bash
source .venv/bin/activate
cd demo_agent
python simple_example.py

# Then type:
> Generate a 30 second script about Pluribus Reactions
```

### To test complete workflows:
```bash
source .venv/bin/activate
python interactive_test.py

# Then type:
> complete-video "Pluribus Reactions"
```

### To test context injection (for Challenge):
```bash
source .venv/bin/activate
python interactive_test.py

# Then type:
> prompt script_generation {"topic": "Pluribus Reactions", "duration_seconds": "30"}
```

---

## Key Insight

**You cannot test an MCP server in isolation with natural language.** 

The MCP server provides **capabilities** (tools/prompts/resources).  
An AI agent provides **intelligence** (understanding natural language).

Together, they create a powerful system where users can say:
- "What's trending about AI?"
- "Generate a script about that"
- "Turn it into a video"

And the agent automatically knows to call your MCP server's tools!

