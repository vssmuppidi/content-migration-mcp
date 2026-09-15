# How to Start the MCP Server

## Method 1: Run Server Directly (for testing)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
python -m src.server
```

The server will start and wait for MCP protocol messages via stdio.

## Method 2: Use Interactive Test Script

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the interactive test script
python interactive_test.py
```

This will:
1. Start the MCP server automatically
2. Connect to it
3. Allow you to send queries and see how the server analyzes context
4. Test prompts, resources, and tools interactively

## Method 3: Use with MCP Client (Claude Desktop, etc.)

The server is configured to run via stdio. Add to your MCP client configuration:

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

## Interactive Test Script Usage

Once you run `python interactive_test.py`, you can use these commands:

### Analyze a Query
```
analyze "Generate a 30 sec script about Pluribus Reactions"
```

### Get a Prompt (with automatic context injection)
```
prompt trending_analysis {"topic": "Pluribus Reactions"}
prompt script_generation {"topic": "Pluribus Reactions", "duration_seconds": 30}
```

### Read a Resource
```
resource trending://topics/Pluribus Reactions
resource content://voices
```

### Call a Tool Directly
```
tool generate_ideas {"topic": "Pluribus Reactions", "limit": 5}
tool analyze_query {"query": "Generate a 30 sec script about Pluribus Reactions"}
```

### Test Complete Workflow
```
workflow "Generate a 30 sec script about Pluribus Reactions"
```

This will:
1. Analyze the query to determine intent
2. Extract topics and requirements
3. Automatically test the appropriate prompt or tool based on the analysis

### List Available Items
```
list-tools
list-prompts
list-resources
```

### Exit
```
exit
```

## Example Session

```
> analyze "Generate a 30 sec script about Pluribus Reactions"

This will show:
- Intent: script_generation
- Topics: ["Pluribus Reactions"]
- Context Sources: ["reddit", "youtube", "news"]
- Requirements: {"duration": 30, ...}
- Confidence: 0.95

> workflow "Generate a 30 sec script about Pluribus Reactions"

This will:
1. Analyze the query
2. See it's a script_generation intent
3. Automatically test the script_generation prompt with automatic context injection
4. Show you how the server fetches trending data and enriches the prompt
```

