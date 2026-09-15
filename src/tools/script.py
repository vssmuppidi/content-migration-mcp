"""Script generation tool using OpenRouter and Groq APIs."""

import requests
from typing import Dict, Any, Optional
from groq import Groq
from ..config import config
from .context_processor import create_context_summary


def _generate_with_groq(
    prompt: str,
    model: str
) -> Dict[str, Any]:
    """
    Generate script using Groq API.
    
    Args:
        prompt: The prompt to send
        model: Model to use
        
    Returns:
        Dictionary with success status and content or error
    """
    try:
        client = Groq(api_key=config.groq_api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )
        
        if not response.choices:
            return {
                "success": False,
                "error": "Groq API returned no choices",
                "provider": "groq"
            }
        
        choice = response.choices[0]
        if not hasattr(choice, 'message') or not choice.message:
            return {
                "success": False,
                "error": "Groq API returned invalid message structure",
                "provider": "groq"
            }
        
        content = choice.message.content
        if content is None:
            return {
                "success": False,
                "error": "Groq API returned None content",
                "provider": "groq",
                "debug": {
                    "model": model,
                    "response_id": getattr(response, 'id', None),
                    "choices_count": len(response.choices),
                    "finish_reason": getattr(choice, 'finish_reason', None)
                }
            }
        
        content_str = str(content).strip()
        if not content_str:
            return {
                "success": False,
                "error": "Groq API returned empty content",
                "provider": "groq",
                "debug": {
                    "model": model,
                    "response_id": getattr(response, 'id', None),
                    "choices_count": len(response.choices),
                    "finish_reason": getattr(choice, 'finish_reason', None),
                    "content_type": type(content).__name__
                }
            }
        
        # Clean up reasoning model output - remove reasoning tags and metadata
        # Some reasoning models include reasoning in the content that needs to be filtered
        cleaned_content = content_str
        
        # Remove reasoning blocks if present (common in reasoning models)
        import re
        # Remove content between <reasoning> tags
        cleaned_content = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove content between <think> tags
        cleaned_content = re.sub(r'<think>.*?</think>', '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove lines that look like reasoning (starting with "Okay, let's", "First,", etc.)
        lines = cleaned_content.split('\n')
        filtered_lines = []
        skip_reasoning = False
        for line in lines:
            line_lower = line.strip().lower()
            # Skip obvious reasoning lines
            if any(phrase in line_lower for phrase in [
                "okay, let's", "first,", "looking at", "the user wants", 
                "tackle this", "need to be", "let me", "so i need"
            ]) and len(line.strip()) < 200:  # Short reasoning lines
                continue
            # Look for the actual script content (usually starts after reasoning)
            if line.strip() and not line_lower.startswith('<'):
                filtered_lines.append(line)
        
        cleaned_content = '\n'.join(filtered_lines).strip()
        
        # If cleaning removed everything, use original
        if not cleaned_content:
            cleaned_content = content_str.strip()
        
        return {
            "success": True,
            "content": cleaned_content,
            "provider": "groq"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Groq API error: {str(e)}",
            "provider": "groq",
            "exception_type": type(e).__name__
        }


def _generate_with_openrouter(
    prompt: str,
    model: str,
    max_tokens: int
) -> Dict[str, Any]:
    """
    Generate script using OpenRouter API.
    
    Args:
        prompt: The prompt to send
        model: Model to use
        max_tokens: Maximum tokens to generate
        
    Returns:
        Dictionary with success status and content or error
    """
    try:
        headers = {
            "Authorization": f"Bearer {config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/content-mcp",
            "X-Title": "Content MCP Server"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return {
                "success": True,
                "content": result["choices"][0]["message"]["content"].strip(),
                "provider": "openrouter"
            }
        else:
            return {
                "success": False,
                "error": "No content generated from OpenRouter",
                "provider": "openrouter"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"OpenRouter API error: {str(e)}",
            "provider": "openrouter"
        }


def generate_script(
    topic: str,
    duration_seconds: int,
    model: Optional[str] = None,
    style: Optional[str] = "informative and engaging",
    trending_info: Optional[str] = None,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a monologue script based on a topic using OpenRouter or Groq.
    Automatically falls back to the alternative provider if the primary fails.
    
    Args:
        topic: The main topic or subject for the script
        duration_seconds: Target duration of the script in seconds
        model: Model to use (default: from config based on provider)
        style: Style/tone of the script (default: "informative and engaging")
        trending_info: Optional context from trending data to incorporate
        provider: Inference provider - "openrouter" or "groq" (default: from config)
        
    Returns:
        Dictionary containing the generated script and metadata
    """
    if not config.has_inference_api():
        return {
            "success": False,
            "error": "No inference API configured. Please set OPENROUTER_API_KEY or GROQ_API_KEY.",
            "script": None
        }
    
    # Calculate target word count based on speaking rate
    duration_minutes = duration_seconds / 60
    target_word_count = int(duration_minutes * config.speaking_rate_wpm)
    
    # Determine provider and model first (needed for prompt customization)
    selected_provider = provider or config.inference_provider
    selected_model = model or (config.groq_model if selected_provider == "groq" else config.openrouter_model)
    
    # Construct the prompt
    prompt = f"""Write a {duration_seconds}-second monologue script about: {topic}

Style: {style}
Target word count: approximately {target_word_count} words (for {duration_seconds} seconds at {config.speaking_rate_wpm} words per minute)
"""
    
    if trending_info:
        prompt += f"\nContext from trending data:\n{trending_info}\n"
        prompt += "\nIMPORTANT: Use the context information above to write about the ACTUAL CONTENT and topics. "
        prompt += "DO NOT mention Reddit, YouTube, or other sources in the script. "
        prompt += "Focus on the subject matter itself, not where the information came from.\n"
    
    # Add ElevenLabs emotional tags instructions
    prompt += """
VOICE ENHANCEMENT: You can use ElevenLabs emotional and delivery tags to make the audio more expressive.
Available tags (use sparingly and naturally):
- Emotions: [happy], [excited], [sad], [angry], [nervous], [curious], [mischievously], [sarcastic]
- Delivery: [whispers], [shouts], [speaking softly], [calm], [slowly], [rushed]
- Sounds: [laughs], [chuckles], [giggles], [sighs], [clears throat]
- Timing: [pause], [long pause]

Example: "This is incredible! [excited] The results show a 300% increase [pause] which nobody expected."

Use these tags naturally to enhance emotion and pacing. Don't overuse them - 2-4 tags per 30 seconds is ideal.
"""
    
    # Check if this is a reasoning model and adjust prompt accordingly
    is_reasoning_model = selected_provider == "groq" and selected_model and ("oss" in selected_model.lower() or "qwen" in selected_model.lower())
    
    if is_reasoning_model:
        prompt += """
CRITICAL: Output ONLY the final script text. Do NOT include your reasoning process, thinking, or analysis.
Do NOT explain your approach. Do NOT say "First, I'll" or "Let me" or "I need to".
Start directly with the script content as if you are speaking.

Requirements:
- Write in a conversational, engaging tone suitable for spoken delivery
- Structure with clear beginning, middle, and end
- Make it interesting and informative
- Write ONLY the spoken script content
- NO reasoning, NO explanations, NO meta-commentary
- Include emotion/delivery tags where appropriate for expressiveness
- Start speaking immediately

BEGIN THE SCRIPT NOW:"""
    else:
        prompt += """
Requirements:
- Write in a conversational, engaging tone suitable for spoken delivery
- Structure the content with a clear beginning, middle, and end
- Make it interesting and informative
- Write ONLY the script content, no stage directions or meta-commentary
- Include emotion/delivery tags where appropriate to enhance expressiveness
- Ensure it flows naturally when read aloud

Script:"""
    
    # Define primary and fallback providers
    providers = []
    if selected_provider == "groq" and config.validate_groq_config():
        providers.append(("groq", model or config.groq_model))
        if config.validate_openrouter_config():
            providers.append(("openrouter", model or config.openrouter_model))
    else:
        if config.validate_openrouter_config():
            providers.append(("openrouter", model or config.openrouter_model))
        if config.validate_groq_config():
            providers.append(("groq", model or config.groq_model))
    
    # Try providers in order
    errors = []
    for provider_name, provider_model in providers:
        if provider_name == "groq":
            result = _generate_with_groq(prompt, provider_model)
        else:
            # For OpenRouter, still use max_tokens (they might need it)
            base_tokens = int(target_word_count * 2)
            max_tokens = max(100, min(base_tokens, 4096))
            result = _generate_with_openrouter(prompt, provider_model, max_tokens)
        
        if result["success"]:
            script_content = result["content"]
            
            # Calculate actual word count
            actual_word_count = len(script_content.split())
            estimated_duration = (actual_word_count / config.speaking_rate_wpm) * 60
            
            return {
                "success": True,
                "script": script_content,
                "metadata": {
                    "topic": topic,
                    "provider": result["provider"],
                    "model": provider_model,
                    "requested_duration_seconds": duration_seconds,
                    "estimated_duration_seconds": round(estimated_duration, 1),
                    "target_word_count": target_word_count,
                    "actual_word_count": actual_word_count,
                    "style": style,
                    "speaking_rate_wpm": config.speaking_rate_wpm
                },
                "error": None
            }
        else:
            errors.append(f"{provider_name}: {result['error']}")
    
    # All providers failed - show all errors
    error_summary = " | ".join(errors) if errors else "Unknown error"
    return {
        "success": False,
        "error": f"All inference providers failed. Errors: {error_summary}",
        "script": None,
        "provider_errors": errors
    }


def generate_script_from_ideas(
    ideas_data: Dict[str, Any],
    duration_seconds: int,
    model: Optional[str] = None,
    style: Optional[str] = "informative and engaging",
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a script based on aggregated ideas data.
    
    This is a convenience function that takes the output from generate_ideas()
    and creates a script incorporating the trending information.
    
    Args:
        ideas_data: Output from generate_ideas() function
        duration_seconds: Target duration of the script in seconds
        model: OpenRouter model to use (default: from config)
        style: Style/tone of the script
        provider: Inference provider - "openrouter" or "groq" (default: from config)
        
    Returns:
        Dictionary containing the generated script and metadata
    """
    topic = ideas_data.get("topic", "trending topics")
    
    # Use intelligent context processor to create rich, structured context
    trending_context = create_context_summary(ideas_data, topic, top_n_per_source=5)
    
    return generate_script(
        topic=topic,
        duration_seconds=duration_seconds,
        model=model,
        style=style,
        trending_info=trending_context,
        provider=provider
    )


def generate_complete_script(
    topic: str,
    duration_seconds: int,
    provider: Optional[str] = None,
    style: Optional[str] = "informative and engaging",
    limit: int = 3,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete script in one step: fetches trending topics AND generates script.
    
    This is a composite tool that handles the entire workflow internally:
    1. Fetches trending topics from Reddit, YouTube, and Google News
    2. Generates a script incorporating those topics
    
    Perfect for agents - no need to orchestrate multiple tool calls.
    
    Args:
        topic: The topic to research and write about
        duration_seconds: Target duration of the script in seconds
        provider: Inference provider - "groq" or "openrouter" (default: from config)
        style: Script style/tone (default: "informative and engaging")
        limit: Number of items to fetch per source (default: 3)
        model: Model to use (default: from config based on provider)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - script: The generated script text
        - metadata: Script metadata (provider, model, word count, etc.)
        - trending_data: The fetched trending topics data
        - topic: The input topic
        - error: Error message if failed
    """
    from .ideas import generate_ideas
    
    try:
        # Step 1: Get trending ideas
        ideas_data = generate_ideas(topic=topic, limit=limit)
        
        # Check if we got any data
        total_items = ideas_data.get("summary", {}).get("total_items", 0)
        if total_items == 0:
            return {
                "success": False,
                "error": "No trending topics found. Unable to generate script without source material.",
                "script": None,
                "trending_data": ideas_data,
                "topic": topic
            }
        
        # Step 2: Generate script from ideas
        script_result = generate_script_from_ideas(
            ideas_data=ideas_data,
            duration_seconds=duration_seconds,
            provider=provider,
            style=style,
            model=model
        )
        
        # Combine results
        if script_result.get("success"):
            return {
                **script_result,
                "trending_data": ideas_data,
                "topic": topic
            }
        else:
            return {
                **script_result,
                "trending_data": ideas_data,
                "topic": topic
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in generate_complete_script: {str(e)}",
            "script": None,
            "topic": topic
        }

