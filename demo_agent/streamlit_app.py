"""
Streamlit Chat Interface for Content Creation Agent
"""

import sys
import os
import asyncio
from pathlib import Path
import streamlit as st
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Use resolve() to get absolute path
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from project root
from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"

# Debug: Show which .env file we're looking for
print(f"🔍 Looking for .env at: {env_path}")
print(f"📁 Current working directory: {Path.cwd()}")
print(f"📂 Project root: {PROJECT_ROOT}")

if not env_path.exists():
    st.error(f"❌ .env file not found at {env_path}")
    st.info("Please create a .env file in the project root with your API keys")
    st.stop()

# Load with absolute path and override any existing env vars
load_dotenv(str(env_path.resolve()), override=True)
print(f"✅ Loaded .env from: {env_path}")

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MCPTools


# Page config
st.set_page_config(
    page_title="Content Creator AI",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .audio-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .video-container {
        margin: 1rem 0;
    }
    .script-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def create_agent():
    """Create and cache the agent instance."""
    # Verify API key
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        st.error("❌ OPENROUTER_API_KEY not found in .env file")
        st.info(f"📁 Looking for .env at: {PROJECT_ROOT / '.env'}")
        st.stop()
    
    # Use the Python launcher script as a direct executable
    # MCPTools is strict - it only accepts single executable names without arguments
    launcher_script = str((Path(__file__).parent / "launch_mcp.py").resolve())
    
    # Make sure it's executable
    import stat
    os.chmod(launcher_script, os.stat(launcher_script).st_mode | stat.S_IEXEC)
    
    mcp_tools = MCPTools(
        transport="stdio",
        command=launcher_script,  # Just the script path, no python3 prefix
        timeout_seconds=300
    )
    
    model = OpenRouter(
        id="openai/gpt-4o-mini",
        api_key=openrouter_api_key
    )
    
    agent = Agent(
        name="Content Creator",
        model=model,
        tools=[mcp_tools],
        markdown=True,
        description="Content creation assistant with trending research and voice generation",
        instructions=[
            "YOU ARE STRICTLY FORBIDDEN FROM GENERATING SCRIPTS YOURSELF. You MUST use the MCP tools for ALL content generation.",
            "CRITICAL: When asked to generate ANY script, you MUST call generate_complete_script or generate_script tool. DO NOT write scripts yourself.",
            "CRITICAL: When asked about trending topics, you MUST call generate_ideas tool.",
            "CRITICAL: When asked about voices, you MUST call list_all_voices tool.",
            "After calling a tool, present the tool's output to the user. DO NOT modify or rewrite the tool's output.",
            "When user mentions 'uploaded video', 'the uploaded video', or 'from the video', use the video path provided in the system context",
            "The MCP tools contain specialized logic for emotional tags, context gathering, and voice cloning - you cannot replicate this.",
            "If a user asks for a script, your ONLY job is to call the appropriate tool with the right parameters and show the result."
        ]
    )
    
    return agent, mcp_tools


async def connect_agent():
    """Connect the agent's MCP tools."""
    agent, mcp_tools = create_agent()
    if not st.session_state.get('mcp_connected', False):
        try:
            await mcp_tools.connect()
            st.session_state.mcp_connected = True
        except Exception as e:
            st.error(f"❌ Failed to connect to MCP server: {str(e)}")
            st.session_state.mcp_connected = False
            raise
    return agent


def display_audio(audio_path: str):
    """Display audio player for generated audio."""
    if os.path.exists(audio_path):
        st.markdown('<div class="audio-container">', unsafe_allow_html=True)
        st.subheader("🎵 Generated Audio")
        st.audio(audio_path)
        st.caption(f"📁 {audio_path}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"Audio file not found: {audio_path}")


def display_video(video_path: str):
    """Display video player for generated video."""
    if os.path.exists(video_path):
        st.markdown('<div class="video-container">', unsafe_allow_html=True)
        st.subheader("🎬 Generated Video")
        st.video(video_path)
        st.caption(f"📁 {video_path}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"Video file not found: {video_path}")


def display_script(script_text: str):
    """Display generated script in a nice box."""
    st.markdown('<div class="script-box">', unsafe_allow_html=True)
    st.subheader("📝 Generated Script")
    st.markdown(script_text)
    st.markdown('</div>', unsafe_allow_html=True)


def extract_media_paths(response: str):
    """Extract audio and video paths from agent response."""
    audio_paths = []
    video_paths = []
    
    # Look for common path patterns
    lines = response.split('\n')
    for line in lines:
        if 'output/audio/' in line and ('.mp3' in line or '.wav' in line):
            # Extract path
            for word in line.split():
                if 'output/audio/' in word and ('.mp3' in word or '.wav' in word):
                    path = word.strip('`"\'()[]{}')
                    # Clean up markdown links [text](path)
                    if path.startswith('file:'):
                        path = path[5:]  # Remove 'file:' prefix
                    
                    # Extract just the filename if path contains output/audio/
                    if 'output/audio/' in path:
                        # Get everything from 'output/audio/' onwards
                        idx = path.find('output/audio/')
                        relative_path = path[idx:]
                        path = str(PROJECT_ROOT / relative_path)
                    elif not path.startswith('/'):
                        # Resolve relative path properly
                        path = str((Path(path).resolve()))
                    
                    if Path(path).exists():
                        audio_paths.append(path)
        
        if 'output/video/' in line and '.mp4' in line:
            for word in line.split():
                if 'output/video/' in word and '.mp4' in word:
                    path = word.strip('`"\'()[]{}')
                    # Clean up markdown links
                    if path.startswith('file:'):
                        path = path[5:]
                    
                    # Extract just the filename if path contains output/video/
                    if 'output/video/' in path:
                        idx = path.find('output/video/')
                        relative_path = path[idx:]
                        path = str(PROJECT_ROOT / relative_path)
                    elif not path.startswith('/'):
                        path = str((Path(path).resolve()))
                    
                    if Path(path).exists():
                        video_paths.append(path)
    
    return audio_paths, video_paths


def extract_script(response: str):
    """Extract script text from response."""
    # Look for script in code blocks or after "script:" labels
    if '```' in response:
        parts = response.split('```')
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Inside code block
                if len(part) > 50 and not part.startswith('json') and not part.startswith('python'):
                    return part.strip()
    
    # Look for "Script:" or "Generated script:" sections
    for keyword in ['Script:', 'Generated script:', 'Here\'s the script:']:
        if keyword in response:
            idx = response.index(keyword)
            script_section = response[idx + len(keyword):].strip()
            # Get first paragraph or until next section
            lines = script_section.split('\n\n')
            if lines:
                return lines[0].strip()
    
    return None


# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False

if 'mcp_connected' not in st.session_state:
    st.session_state.mcp_connected = False

if 'agent_instance' not in st.session_state:
    st.session_state.agent_instance = None

# Auto-connect MCP on startup
if not st.session_state.mcp_connected:
    with st.spinner("🔌 Connecting to MCP server..."):
        try:
            # Create and store event loop
            if 'event_loop' not in st.session_state or st.session_state.event_loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                st.session_state.event_loop = loop
            else:
                loop = st.session_state.event_loop
            
            agent = loop.run_until_complete(connect_agent())
            st.session_state.agent_instance = agent
            st.success("✅ MCP server connected!")
        except Exception as e:
            st.error(f"❌ MCP connection failed: {str(e)}")
            import traceback
            st.text(traceback.format_exc())


# Sidebar
with st.sidebar:
    st.title("🎬 Content Creator AI")
    st.markdown("---")
    
    st.subheader("✨ Quick Actions")
    
    if st.button("🔥 Research Trending Topics", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "What are the top trending topics about AI today?"
        })
        st.rerun()
    
    if st.button("📝 Generate Script", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "Generate a 30-second script about current AI trends"
        })
        st.rerun()
    
    if st.button("🎤 List Voices", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "List all available voices"
        })
        st.rerun()
    
    st.markdown("---")
    
    # Upload video for voice cloning
    st.subheader("🎥 Video Upload")
    st.caption("Upload a video for voice cloning")
    uploaded_video = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'mov', 'avi'],
        help="Upload 10-60 second video with clear speech"
    )
    
    if uploaded_video is not None:
        # Save uploaded file
        upload_dir = PROJECT_ROOT / "test_content"
        upload_dir.mkdir(exist_ok=True)
        video_path = upload_dir / f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        st.success(f"✅ Video saved!")
        st.code(str(video_path), language=None)
        st.session_state.uploaded_video_path = str(video_path)
        
        # Show example prompt
        st.info("💡 **Example prompt:**")
        st.code(f'Generate a 30-second script about AI trends, clone voice from the uploaded video, and create audio', language=None)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.caption("Powered by MCP + Agno")
    st.caption(f"Model: openai/gpt-4o-mini")


# Main chat interface
st.title("💬 Chat with Content Creator AI")
st.caption("Ask me to research trends, generate scripts, create audio, or make videos!")

# Show helpful example prompts when chat is empty
if len(st.session_state.messages) == 0:
    st.info("💡 **Example prompts to try:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Research & Scripts:**
        - "What's trending about climate change?"
        - "Generate a 30-second script about AI ethics"
        - "Research space exploration trends and create a 45-second script"
        """)
    
    with col2:
        st.markdown("""
        **Voice & Video:**
        - "List all available voices"
        - "Clone voice from the uploaded video and save as 'narrator'"
        - "Generate audio using my 'narrator' voice for this script: [text]"
        """)
    
    st.markdown("---")
    
    if 'uploaded_video_path' in st.session_state:
        st.success(f"✅ Video uploaded and ready to use!")
        st.markdown(f"**Try this prompt:**")
        st.code(f"Generate a 30-second script about AI trends, then clone the voice from the uploaded video and create audio with it", language=None)
    else:
        st.markdown("📤 **Upload a video in the sidebar to enable voice cloning!**")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display media if present
        if "audio_paths" in message:
            for audio_path in message["audio_paths"]:
                display_audio(audio_path)
        
        if "video_paths" in message:
            for video_path in message["video_paths"]:
                display_video(video_path)
        
        if "script" in message:
            display_script(message["script"])


# Chat input
if prompt := st.chat_input("Ask me to create content..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        status = st.status("Processing...", expanded=True)
        
        try:
            with status:
                st.write("🤖 Initializing agent...")
                
                # Get or create agent instance
                if st.session_state.agent_instance is None:
                    if 'event_loop' not in st.session_state or st.session_state.event_loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        st.session_state.event_loop = loop
                    else:
                        loop = st.session_state.event_loop
                    
                    agent = loop.run_until_complete(connect_agent())
                    st.session_state.agent_instance = agent
                else:
                    agent = st.session_state.agent_instance
                
                # Get event loop
                if 'event_loop' not in st.session_state or st.session_state.event_loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    st.session_state.event_loop = loop
                else:
                    loop = st.session_state.event_loop
                
                st.write("📝 Preparing query...")
                
                # Enrich prompt with context if uploaded video exists
                enriched_prompt = prompt
                if 'uploaded_video_path' in st.session_state:
                    video_path = st.session_state.uploaded_video_path
                    # Add context to help agent understand
                    enriched_prompt = f"""User request: {prompt}

SYSTEM CONTEXT:
- User has uploaded a video at: {video_path}
- When user mentions "uploaded video", "the video", or "from the video", use this path: {video_path}
- For voice cloning tools, use video_path parameter with: {video_path}
"""
                
                st.write("🔧 Calling MCP tools...")
                st.caption("This may take 30-60 seconds for script generation...")
                
                # Debug: Print what we're sending
                print(f"DEBUG: Sending prompt to agent: {enriched_prompt[:100]}...")
                
                # Run agent with timeout
                async def run_with_timeout():
                    print("DEBUG: Starting agent.arun()")
                    result = await agent.arun(enriched_prompt)
                    print("DEBUG: agent.arun() completed")
                    return result
                
                print("DEBUG: Running with timeout...")
                response = loop.run_until_complete(
                    asyncio.wait_for(run_with_timeout(), timeout=180)  # 3 minute timeout
                )
                print("DEBUG: Response received")
                print(f"DEBUG: Response type: {type(response)}")
                print(f"DEBUG: Response dir: {dir(response)}")
                
                # Extract response text
                response_text = response.content if hasattr(response, 'content') else str(response)
                print(f"DEBUG: Response text length: {len(response_text)}")
                print(f"DEBUG: Response text (first 500 chars): {response_text[:500]}")
                
                # Display response
                message_placeholder.markdown(response_text)
                
                # Extract and display media
                audio_paths, video_paths = extract_media_paths(response_text)
                script = extract_script(response_text)
                
                # Store in message
                message_data = {
                    "role": "assistant",
                    "content": response_text
                }
                
                if audio_paths:
                    message_data["audio_paths"] = audio_paths
                    for audio_path in audio_paths:
                        display_audio(audio_path)
                
                if video_paths:
                    message_data["video_paths"] = video_paths
                    for video_path in video_paths:
                        display_video(video_path)
                
                if script:
                    message_data["script"] = script
                    display_script(script)
                
                st.session_state.messages.append(message_data)
                status.update(label="✅ Complete!", state="complete")
                
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            status.update(label="❌ Error", state="error")


# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💬 Messages", len(st.session_state.messages))

with col2:
    if 'mcp_connected' in st.session_state and st.session_state.mcp_connected:
        st.metric("🔌 MCP Status", "Connected", delta="✓")
    else:
        st.metric("🔌 MCP Status", "Not Connected", delta="✗")

with col3:
    # Count generated files
    audio_dir = PROJECT_ROOT / "output" / "audio"
    video_dir = PROJECT_ROOT / "output" / "video"
    audio_count = len(list(audio_dir.glob("*.mp3"))) if audio_dir.exists() else 0
    video_count = len(list(video_dir.glob("*.mp4"))) if video_dir.exists() else 0
    st.metric("📁 Generated Files", f"{audio_count + video_count}")

