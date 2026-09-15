# Query Analysis and Context Injection Examples

This document demonstrates how the MCP server automatically analyzes queries, fetches context, and enriches responses **without requiring explicit tool calls**.

## Key Concept: Automatic Context Injection

The server provides **three paths** to automatic context (no tool calls required):

1. **Prompts**: Use `get_prompt()` - Server automatically fetches and injects context
2. **Resources**: Read `read_resource()` - Server returns pre-fetched context
3. **Composite Tools**: Call composite tools - They automatically fetch context internally

## Example 1: Trending Topics (Using Prompts)

### Before (Manual - Requires Tool Calls):
```
User: "What's trending about AI?"
Agent: 
  1. Calls generate_ideas(topic="AI")
  2. Waits for response
  3. Processes data
  4. Responds to user
```

### After (Automatic - No Tool Calls):
```
User: "What's trending about AI?"
Agent: 
  1. Uses get_prompt("trending_analysis", {"topic": "AI"})
  2. Server AUTOMATICALLY:
     - Analyzes query intent
     - Fetches trending data from Reddit, YouTube, News
     - Formats context summary
     - Injects context into prompt
  3. Agent receives enriched prompt with context
  4. Agent responds directly (no tool calls needed)
```

### Result:
- **No tool calls required**
- Context is automatically fetched and injected
- Agent gets enriched prompt ready to use

## Example 2: Script Generation (Using Prompts)

### Before (Manual - Requires Tool Calls):
```
User: "Generate a 60-second script about climate change"
Agent:
  1. Calls generate_ideas(topic="climate change")
  2. Waits for trending data
  3. Calls generate_script_from_ideas(ideas_data, duration=60)
  4. Waits for script
  5. Returns script to user
```

### After (Automatic - No Tool Calls):
```
User: "Generate a 60-second script about climate change"
Agent:
  1. Uses get_prompt("script_generation", {
       "topic": "climate change",
       "duration_seconds": 60
     })
  2. Server AUTOMATICALLY:
     - Fetches trending data about climate change
     - Generates intelligent context summary
     - Injects context into prompt
  3. Agent receives enriched prompt
  4. Agent generates script using enriched context (or calls generate_complete_script)
```

### Result:
- **No manual tool chaining**
- Context automatically fetched and formatted
- Enriched prompt ready for script generation

## Example 3: Reading Resources (No Tool Calls)

### Before (Manual - Requires Tool Calls):
```
User: "What's trending about AI?"
Agent:
  1. Calls generate_ideas(topic="AI")
  2. Processes response
  3. Returns to user
```

### After (Automatic - Resource Access):
```
User: "What's trending about AI?"
Agent:
  1. Reads resource("trending://topics/AI")
  2. Server returns pre-fetched/cached trending data
  3. Agent uses data directly (no tool calls)
```

### Result:
- **Direct resource access**
- Data is automatically maintained and cached
- No tool calls needed

## Example 4: Complete Content Creation (Composite Tool)

### Before (Manual - Multiple Tool Calls):
```
User: "Create content about AI"
Agent:
  1. Calls generate_ideas(topic="AI")
  2. Calls generate_script_from_ideas(ideas_data, ...)
  3. Calls generate_audio_from_script(script, video_path)
  4. Returns result
```

### After (Automatic - One Composite Tool Call):
```
User: "Create content about AI"
Agent:
  1. Calls generate_complete_content(topic="AI", ...)
  2. Tool AUTOMATICALLY:
     - Fetches trending data (internally)
     - Generates script with context
     - Clones voice
     - Generates audio
  3. Returns complete result
```

### Result:
- **One tool call does everything**
- All context fetching happens internally
- No tool chaining required

## Example 5: Generic Query with Automatic Context

### Query:
```
User: "What's happening with artificial intelligence these days?"
```

### Server Behavior:
1. **Query Analysis**: Server analyzes query intent → `trending_topics`
2. **Topic Extraction**: Extracts topics → `["artificial intelligence"]`
3. **Context Needs**: Determines context sources → `["reddit", "youtube", "news"]`
4. **Automatic Fetching**: Fetches trending data from all sources
5. **Context Formatting**: Generates intelligent summary
6. **Prompt Enrichment**: Injects context into prompt

### Agent Uses Prompt:
```python
prompt = get_prompt("query_with_context", {
    "query": "What's happening with artificial intelligence these days?"
})
# Prompt automatically includes:
# CONTEXT: [Intelligent summary of trending AI topics from Reddit, YouTube, News]
# USER QUERY: What's happening with artificial intelligence these days?
```

### Agent Response:
Agent can now respond with full context without making any tool calls!

## Example 6: Video Generation (Complete Workflow)

### Query:
```
User: "Create a video about climate change using my video sample"
```

### Server Behavior (if using composite tool):
1. Agent calls `generate_complete_video(topic="climate change", video_path="...")`
2. Tool AUTOMATICALLY:
   - Fetches trending data about climate change
   - Generates script with context
   - Extracts audio from video
   - Clones voice
   - Generates audio
   - Extracts frame from video
   - Creates talking head video with D-ID
3. Returns complete video

### Result:
- **One tool call, complete workflow**
- All context fetching automatic
- No manual orchestration needed

## Comparison Summary

| Approach | Tool Calls Required | Context Fetching | Agent Complexity |
|----------|---------------------|------------------|------------------|
| **Before (Manual)** | 2-4 calls | Manual | High (must orchestrate) |
| **After (Prompts)** | 0 calls | Automatic | Low (just use prompt) |
| **After (Resources)** | 0 calls | Automatic | Low (just read resource) |
| **After (Composite)** | 1 call | Automatic | Low (one call does all) |

## Key Benefits

1. **No Tool Chaining**: Agent doesn't need to orchestrate multiple tool calls
2. **Automatic Context**: Context is automatically fetched when needed
3. **Intelligent Analysis**: Server analyzes queries to determine context needs
4. **Caching**: Context is cached for performance
5. **Transparent**: Works seamlessly - agent doesn't need to know about internal steps

## Usage Recommendations

- **For trending queries**: Use `trending_analysis` prompt or `trending://topics/{topic}` resource
- **For script generation**: Use `script_generation` prompt or `generate_complete_script` tool
- **For video creation**: Use `generate_complete_video` tool (does everything)
- **For general queries**: Use `query_with_context` prompt (automatic analysis)

## Technical Details

### Query Analysis
- Uses AI (Groq/OpenRouter) for intent detection
- Falls back to rule-based analysis if AI unavailable
- Extracts topics, detects requirements, determines context needs

### Context Fetching
- Automatically fetches from Reddit, YouTube, News
- Uses intelligent ranking and filtering
- Generates AI-powered summaries
- Caches results for performance

### Prompt Enrichment
- Formats context as "CONTEXT: ..." block
- Injects context before user query
- Returns ready-to-use enriched prompt

### Resource Management
- Resources are automatically maintained
- Cached data is refreshed periodically
- Direct access without tool calls

## Error Handling

- If query analysis fails → Falls back to rule-based analysis
- If context fetch fails → Returns query without context (with warning)
- If prompt enrichment fails → Returns original query
- All errors are logged for debugging

## Performance

- Query analysis: < 500ms (cached: < 50ms)
- Context fetching: < 5s (cached: < 100ms)
- Prompt enrichment: < 100ms
- Resource access: < 50ms (cached: < 10ms)

## Monitoring

Middleware tracks:
- Queries analyzed
- Context fetches
- Prompt enrichments
- Resource accesses
- Cache hits/misses

Check `/tmp/mcp_context_middleware.log` for detailed logs.

