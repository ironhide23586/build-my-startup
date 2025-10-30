"""
Clean reference implementation: Face Detection Web App Builder

This script demonstrates how to use the StandardBuildPipeline from the agent framework
to build a complete web application with minimal boilerplate code.
"""
import asyncio
import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agent_framework.pipelines.standard_build import StandardBuildPipeline, BuildConfig
from agent_framework.paths import default_app_paths


# Get output paths for this app
OUTPUT_DIR, TEMPLATES_DIR, STATIC_DIR = default_app_paths(__file__)


# Define what we want to build
BUILD_TASKS = [
    {
        "task": "app.py",
        "description": """Create a Flask web application (app.py) for a face detection web app. 
        Requirements:
        - Use Flask framework
        - Host locally on port 5000
        - Include route for video feed at /video_feed
        - Include route for index page at /
        - Use OpenCV to capture camera feed
        - Apply face detection to video frames
        - Stream video as MJPEG
        - Must work on macOS (M2 MacBook)
        - Import from parent directory: from camera_handler import CameraHandler
        - Store files in OUTPUT_DIR and use templates from TEMPLATES_DIR
        
        Code should be complete and ready to run."""
    },
    {
        "task": "camera_handler.py",
        "description": """Create a camera handler module (camera_handler.py) using OpenCV.
        Requirements:
        - Class named CameraHandler
        - Methods: get_frame() returns video frame with face detection
        - Use OpenCV's Haar Cascade or dlib for face detection
        - Handle camera initialization and cleanup
        - Draw rectangles around detected faces
        - Must work on macOS
        - Use cv2.VideoCapture(0) for default camera
        - Include proper error handling
        
        Code should be complete and ready to use."""
    },
    {
        "task": "face_detection_agent.py",
        "description": """Create a face detection agent (face_detection_agent.py) using the agent framework.
        Requirements:
        - Extends the Agent class from parent directory
        - Processes face detection events
        - Can communicate via MessageBus
        - Handles face detection results (coordinates, count, etc.)
        - Can broadcast detection events to other agents
        - Integrates with camera_handler
        
        Import from parent: from agent import Agent, Message
        Code should follow the agent framework patterns."""
    },
    {
        "task": "templates/index.html",
        "description": """Create an HTML template (templates/index.html) for the face detection web app.
        Requirements:
        - Modern, beautiful UI
        - Live video feed displayed in center
        - Shows detected faces with real-time updates
        - Responsive design
        - Clean, professional styling
        - Include title "Live Face Detection"
        - Video feed from /video_feed route
        - Works in modern browsers
        
        Code should be complete HTML with inline CSS for simplicity."""
    }
]


# Project description for plan generation
PROJECT_DESCRIPTION = "Face Detection Web App with live camera feed and face detection, hosted locally on macOS"


async def main():
    """Build the face detection app using the standard pipeline."""
    
    print("=" * 70)
    print("🤖 Building Face Detection Web App")
    print("=" * 70)
    
    # Check for OpenAI API key (env var or config file)
    from agent_framework.config import OPENAI_API_KEY as CONFIG_KEY
    api_key = os.getenv("OPENAI_API_KEY") or CONFIG_KEY
    
    if not api_key:
        print("\n❌ ERROR: OpenAI API key not found!")
        print("=" * 70)
        print("Please set your OpenAI API key:")
        print("  1. In agent_framework/config.py, or")
        print("  2. Via: export OPENAI_API_KEY='your-api-key-here'")
        print("=" * 70)
        sys.exit(1)
    
    # Show confirmation without exposing full key
    key_source = "environment variable" if os.getenv("OPENAI_API_KEY") else "config file"
    print(f"\n✅ OpenAI API key loaded from {key_source}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"📋 Tasks to build: {len(BUILD_TASKS)}")
    print()
    
    # Configure the build pipeline
    config = BuildConfig(
        output_dir=OUTPUT_DIR,
        templates_dir=TEMPLATES_DIR,
        static_dir=STATIC_DIR,
        max_fix_attempts=3,
        max_iterations_per_file=5,
        safe_commands_allowed=True,
        timeout=300.0,  # 5 minutes
        poll_interval=1.0,
        show_progress=True,
        generate_plan=True
    )
    
    # Create and run the pipeline
    print("🚀 Starting build pipeline...\n")
    pipeline = StandardBuildPipeline(config)
    
    try:
        result = await pipeline.run_build(BUILD_TASKS, PROJECT_DESCRIPTION)
        
        # Display results
        print("\n" + "=" * 70)
        print("✅ Build Complete!")
        print("=" * 70)
        print(f"📊 Results:")
        print(f"   • Files generated: {result['generated']}")
        print(f"   • Files saved: {result['saved']}")
        print(f"   • Tests run: {len(result['tests'])}")
        
        # Test results summary
        passed = sum(1 for t in result['tests'].values() if t.get('passed'))
        if result['tests']:
            print(f"   • Tests passed: {passed}/{len(result['tests'])}")
        
        # Command history
        if result.get('command_history'):
            print(f"   • Commands executed: {len(result['command_history'])}")
        
        print(f"\n📁 Location: {OUTPUT_DIR}")
        
        if result.get('plan'):
            print(f"📋 Plan saved to: {os.path.join(OUTPUT_DIR, 'BUILD_PLAN.md')}")
        
        print("\n" + "=" * 70)
        print("🎉 Success! Your app is ready to run.")
        print("=" * 70)
        print("\n💡 Next steps:")
        print(f"   1. cd {OUTPUT_DIR}")
        print("   2. pip install flask opencv-python")
        print("   3. python app.py")
        print("   4. Open http://localhost:5000 in your browser")
        print()
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Build Failed")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Run the async build process
    result = asyncio.run(main())
    
    # Exit with success code
    sys.exit(0 if result['saved'] > 0 else 1)
