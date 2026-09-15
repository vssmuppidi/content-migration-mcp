# Changelog

All notable changes to the Content MCP Server will be documented in this file.

## [0.2.0] - 2024-11-08

### Added
- **Groq API Integration**: FREE alternative/backup for script generation
  - Automatic fallback between OpenRouter and Groq
  - Configurable primary provider via `INFERENCE_PROVIDER`
  - Support for Llama 3.1, Mixtral, and other Groq models
  - Per-request provider override with `provider` parameter
- **Enhanced Configuration**:
  - `GROQ_API_KEY` environment variable
  - `GROQ_MODEL` for model selection
  - `INFERENCE_PROVIDER` to set primary provider
  - Validation accepts either OpenRouter or Groq (or both)
- **New Documentation**:
  - `GROQ_INTEGRATION.md` - Comprehensive Groq setup guide
  - Updated README with Groq information
  - Updated SETUP.md with Groq instructions
  - Enhanced troubleshooting sections

### Changed
- Script generation now tries primary provider first, then falls back to alternative
- Configuration validation now requires at least one inference API (was OpenRouter only)
- Tool descriptions updated to mention both providers
- Metadata now includes which provider was actually used

### Dependencies
- Added `groq>=0.9.0` to requirements.txt

## [0.1.0] - 2024-11-08

### Added
- Initial release of Content MCP Server
- **Content Idea Generation Tools**:
  - `generate_ideas`: Aggregate from all sources
  - `generate_reddit_ideas`: Reddit-specific trending posts
  - `generate_youtube_ideas`: YouTube trending videos
  - `generate_news_ideas`: Google News articles
- **Script Generation Tools**:
  - `generate_script`: AI-powered monologue generation
  - `generate_script_from_ideas`: Scripts from aggregated trending data
- **Data Source Integrations**:
  - Reddit API via PRAW (100 queries/min free)
  - YouTube Data API v3 (10k units/day free)
  - Google News RSS feeds (unlimited, free)
  - OpenRouter API for script generation
- **Configuration Management**:
  - Environment variable-based configuration
  - API key validation
  - Graceful error handling
- **Documentation**:
  - Comprehensive README.md
  - Quick start SETUP.md
  - PROJECT_SUMMARY.md
  - API setup instructions
  - Troubleshooting guide
- **Development Tools**:
  - `validate_setup.py` for configuration checking
  - Proper .gitignore
  - Type hints throughout codebase

### Dependencies
- `mcp>=0.1.0`
- `praw>=7.7.1`
- `google-api-python-client>=2.100.0`
- `feedparser>=6.0.10`
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`
- `typing-extensions>=4.8.0`

---

## Version Format

The version numbers follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

