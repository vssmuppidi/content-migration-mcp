# Quick Setup Guide

Follow these steps to get your Content MCP Server up and running:

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Get Your API Keys

### Reddit API (Free)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: Content MCP (or any name)
   - **App type**: Select "script"
   - **Description**: Optional
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Click "Create app"
5. Note the **client_id** (under the app name) and **client_secret**

### YouTube Data API v3 (Free - 10k units/day)
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable "YouTube Data API v3":
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy your API key

### OpenRouter (Paid - Optional)
1. Go to https://openrouter.ai/keys
2. Sign up or log in
3. Generate an API key
4. Add credits to your account

**Note:** You can skip this if you use Groq instead (see below)

### Groq (FREE - Recommended!)
1. Go to https://console.groq.com/keys
2. Sign up with your email (free account)
3. Click "Create API Key"
4. Copy your API key
5. **No credit card required!** Groq offers generous free tier

## 3. Configure Environment Variables

Copy the example env file:
```bash
cp env.example .env
```

Edit `.env` and add your API keys:
```bash
REDDIT_CLIENT_ID=your_actual_client_id
REDDIT_CLIENT_SECRET=your_actual_secret
REDDIT_USER_AGENT=ContentMCP/0.1.0 by YourRedditUsername

YOUTUBE_API_KEY=your_actual_youtube_key

# Choose at least one inference API (or both for automatic fallback)
OPENROUTER_API_KEY=your_actual_openrouter_key  # (Optional - Paid)
GROQ_API_KEY=your_actual_groq_key              # (Recommended - FREE!)

# Set your preferred provider (defaults to openrouter)
INFERENCE_PROVIDER=groq  # Use "groq" for free tier or "openrouter" for paid

# Model selection (optional)
OPENROUTER_MODEL=anthropic/claude-3-sonnet
GROQ_MODEL=llama-3.1-70b-versatile
```

**💡 Pro Tip:** Configure both APIs for automatic fallback! If one fails, the system automatically uses the other.

## 4. Test the Server

Run the server:
```bash
python -m src.server
```

If configured correctly, you should see a message about the server starting. If any API keys are missing, you'll see warnings.

## 5. Use with Claude Desktop (Optional)

### On macOS:
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

### On Windows:
Edit `%APPDATA%/Claude/claude_desktop_config.json`

Add this configuration:
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

Replace `/absolute/path/to/Content-MCP` with the actual path to this directory.

Restart Claude Desktop.

## 6. Test the Tools

Once connected, try these commands in Claude:

1. **Get trending ideas about AI:**
   ```
   Use the generate_ideas tool with topic "AI" and limit 5
   ```

2. **Generate a 30-second script:**
   ```
   Use the generate_script tool with topic "AI trends" and duration_seconds 30
   ```

3. **Get Reddit ideas specifically:**
   ```
   Use the generate_reddit_ideas tool with topic "technology" and subreddit "technology"
   ```

## Troubleshooting

### Import Errors
Make sure you're in the project root directory and have installed all dependencies:
```bash
pip install -r requirements.txt
```

### API Key Errors
- Verify your `.env` file exists and contains all required keys
- Check that there are no extra spaces or quotes around the values
- Ensure the file is named exactly `.env` (not `env.txt` or `.env.txt`)

### Reddit "invalid_grant" Error
- Verify your `client_id` and `client_secret` are correct
- Ensure your app type is "script" not "web app"

### YouTube Quota Exceeded
- You've used your daily quota of 10,000 units
- Wait until midnight Pacific Time for the quota to reset
- Each search typically uses ~100 units

### Inference API Errors
**"No inference API configured"**
- You need at least one: OpenRouter or Groq
- **Quick fix:** Get a FREE Groq key at https://console.groq.com/keys

**OpenRouter Errors**
- Check your API key is correct
- Verify you have credits in your account
- Try a different model if the specified one doesn't work
- Or switch to Groq (FREE!) by setting `INFERENCE_PROVIDER=groq`

**Groq Errors**
- Check your API key is correct
- Verify your account is active at https://console.groq.com
- The system will automatically fall back to OpenRouter if both are configured

## Next Steps

Once your server is working:
1. Explore different topics and sources
2. Try different OpenRouter models for script generation
3. Adjust the speaking rate (SPEAKING_RATE_WPM) for your needs
4. Check out the full README.md for advanced usage

## Need Help?

- Review the full [README.md](README.md) for detailed information
- Check the error messages in your terminal
- Verify each API key is configured correctly
- Test each service independently to isolate issues

