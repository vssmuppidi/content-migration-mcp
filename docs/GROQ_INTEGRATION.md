# Groq Integration Guide

## Why Groq?

Groq has been added as a **free alternative/backup** to OpenRouter for script generation:

✅ **FREE Tier** - No credit card required  
✅ **Fast Inference** - Lightning-fast generation  
✅ **Generous Limits** - Much more than enough for typical use  
✅ **Great Models** - Llama 3.1 70B, Mixtral, and more  
✅ **Automatic Fallback** - Seamlessly switches between providers  

## Quick Setup

### 1. Get Your Free Groq API Key

1. Visit https://console.groq.com/keys
2. Sign up for a free account (no credit card needed!)
3. Click "Create API Key"
4. Copy your API key

### 2. Add to Your Configuration

Edit your `.env` file:

```bash
# Add your Groq API key
GROQ_API_KEY=gsk_your_actual_key_here

# Set Groq as your primary provider (optional)
INFERENCE_PROVIDER=groq

# Choose a Groq model (optional)
GROQ_MODEL=llama-3.1-70b-versatile
```

### 3. That's It!

Your server will now use Groq for script generation. No changes to your usage required!

## Automatic Fallback

The system intelligently handles provider failures:

```
User requests script generation
    ↓
Try Primary Provider (e.g., Groq)
    ↓
Success? → Return script ✓
    ↓
Failed? → Try Backup Provider (e.g., OpenRouter)
    ↓
Success? → Return script ✓
    ↓
Failed? → Return error message
```

### Configuration Examples

**Option 1: Groq Only (100% Free)**
```bash
GROQ_API_KEY=gsk_your_key
INFERENCE_PROVIDER=groq
# OpenRouter not needed!
```

**Option 2: OpenRouter Only (Paid)**
```bash
OPENROUTER_API_KEY=sk_your_key
INFERENCE_PROVIDER=openrouter
# Groq not needed
```

**Option 3: Both (Maximum Reliability)**
```bash
GROQ_API_KEY=gsk_your_key
OPENROUTER_API_KEY=sk_your_key
INFERENCE_PROVIDER=groq  # Try Groq first (free), fall back to OpenRouter if needed
```

## Available Groq Models

Groq offers several high-performance models:

| Model | Description | Context Length |
|-------|-------------|----------------|
| `llama-3.1-70b-versatile` | Best overall (default) | 128K tokens |
| `llama-3.1-8b-instant` | Fastest, good quality | 128K tokens |
| `mixtral-8x7b-32768` | Great for creative tasks | 32K tokens |
| `gemma2-9b-it` | Efficient, good balance | 8K tokens |

To change models, update your `.env`:
```bash
GROQ_MODEL=llama-3.1-8b-instant  # For faster generation
```

## Using Groq in Scripts

The provider is transparent - just use the tools as normal:

```python
# Example 1: Use default provider (from config)
result = generate_script(
    topic="AI trends",
    duration_seconds=60
)

# Example 2: Force Groq for this request
result = generate_script(
    topic="AI trends",
    duration_seconds=60,
    provider="groq"
)

# Example 3: Force OpenRouter for this request
result = generate_script(
    topic="AI trends",
    duration_seconds=60,
    provider="openrouter"
)
```

## Performance Comparison

| Feature | Groq | OpenRouter |
|---------|------|------------|
| Cost | ✅ FREE | ❌ Paid per token |
| Speed | ✅ Very fast | Medium-fast |
| Model Selection | Good (5-10 models) | ✅ Excellent (100+ models) |
| Rate Limits | ✅ Generous free tier | Based on your plan |
| Setup | ✅ No payment needed | Requires credits |

## Monitoring Usage

Check your Groq usage at https://console.groq.com/usage

The response metadata tells you which provider was used:

```json
{
  "success": true,
  "script": "...",
  "metadata": {
    "provider": "groq",  // or "openrouter"
    "model": "llama-3.1-70b-versatile",
    ...
  }
}
```

## Troubleshooting

### "Groq API error: Rate limit exceeded"
- Wait a few seconds and try again
- The free tier is very generous, but not unlimited
- System will automatically try OpenRouter if configured

### "Invalid API key"
- Verify your key starts with `gsk_`
- Regenerate key at https://console.groq.com/keys
- Make sure there are no extra spaces in your `.env` file

### Script quality concerns
- Try different models: `llama-3.1-70b-versatile` is best for quality
- Use `mixtral-8x7b-32768` for more creative scripts
- You can still use OpenRouter for specific requests with `provider="openrouter"`

## Best Practices

1. **Start with Groq** - It's free and fast, perfect for testing
2. **Configure Both** - Use Groq as primary, OpenRouter as backup
3. **Monitor Usage** - Check Groq console occasionally
4. **Adjust Models** - Pick the right model for your needs (speed vs quality)

## Cost Savings

By using Groq as your primary provider:

- **100% free** for typical usage
- Only use OpenRouter when you need specific models
- Automatic fallback ensures reliability
- No surprise bills!

## Need Help?

- **Groq Documentation**: https://console.groq.com/docs
- **Get API Key**: https://console.groq.com/keys
- **View Usage**: https://console.groq.com/usage
- **Model Playground**: https://console.groq.com/playground

---

**Bottom Line:** Groq gives you a powerful, FREE inference API with automatic fallback to OpenRouter. Configure it and enjoy script generation without worrying about costs!

