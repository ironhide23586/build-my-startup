"""
Clean reference implementation: AI Commentary Generator App Builder

This demonstrates the Adaptive Build Pipeline - the user provides a high-level
description of their startup, and AI agents automatically infer what needs to be built.
"""
import asyncio
import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from build_my_startup.pipelines.adaptive_build import AdaptiveBuildConfig, AdaptiveBuildPipeline
from build_my_startup.paths import default_app_paths


# Get output paths for this app
OUTPUT_DIR, TEMPLATES_DIR, STATIC_DIR = default_app_paths(__file__)


# ============================================================================
# HIGH-LEVEL STARTUP DESCRIPTION
# This is all the user needs to provide - agents infer everything else!
# ============================================================================

STARTUP_IDEA = """
I want to build an AI-powered image commentary generator web app.

Users should be able to upload images through a beautiful web interface, and the app 
will use OpenAI's Vision API to generate engaging commentary about the image. 

The commentary should be intelligent and contextual - understanding what's in the image 
and providing interesting insights. Users can choose different styles of commentary 
(descriptive, humorous, technical, poetic).

The app should:
- Run locally on my Mac (M2 MacBook)
- Have a modern, beautiful web UI
- Process images quickly
- Use the agent framework for handling commentary generation
- Store images temporarily and clean up old ones
- Display the AI-generated commentary in a nice format

I want this to be a clean MVP that demonstrates the power of AI vision capabilities.
"""

TARGET_PLATFORM = "macOS"

TECH_PREFERENCES = {
    "backend_framework": "Flask",
    "frontend": "HTML/CSS/JavaScript (vanilla, no frameworks)",
    "ai_provider": "OpenAI Vision API",
    "port": 5001,
    "agent_framework": "build_my_startup agents",
}


async def main():
    """Build the commentary app using the adaptive pipeline."""
    
    print("=" * 70)
    print("🚀 AI-Powered Adaptive Build System")
    print("=" * 70)
    print("\n📝 Your Startup Idea:")
    print("-" * 70)
    print(STARTUP_IDEA.strip())
    print("-" * 70)
    
    # Check for OpenAI API key (env var or config file)
    from build_my_startup.config import OPENAI_API_KEY as CONFIG_KEY
    api_key = os.getenv("OPENAI_API_KEY") or CONFIG_KEY
    
    if not api_key:
        print("\n❌ ERROR: OpenAI API key not found!")
        print("=" * 70)
        print("Please set your OpenAI API key:")
        print("  1. In build_my_startup/config.py, or")
        print("  2. Via: export OPENAI_API_KEY='your-api-key-here'")
        print("=" * 70)
        sys.exit(1)
    
    # Show confirmation without exposing full key
    key_source = "environment variable" if os.getenv("OPENAI_API_KEY") else "config file"
    print(f"\n✅ OpenAI API key loaded from {key_source}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    
    # Configure the adaptive build pipeline
    config = AdaptiveBuildConfig(
        output_dir=OUTPUT_DIR,
        templates_dir=TEMPLATES_DIR,
        static_dir=STATIC_DIR,
        max_fix_attempts=3,
        max_iterations_per_file=5,
        safe_commands_allowed=True,
        timeout=300.0,  # 5 minutes
        poll_interval=1.0,
        show_progress=True,
        generate_plan=True,
        ideation_timeout=60.0,  # Time for AI to analyze and plan
        min_files=4,
        max_files=8
    )
    
    # Create and run the adaptive pipeline
    print("🧠 Starting adaptive build pipeline...")
    print("   Phase 1: AI agents will analyze your idea and infer build tasks")
    print("   Phase 2: AI agents will generate code for each component\n")
    
    pipeline = AdaptiveBuildPipeline(config)
    
    try:
        result = await pipeline.run_adaptive_build(
            description=STARTUP_IDEA,
            target_platform=TARGET_PLATFORM,
            tech_preferences=TECH_PREFERENCES
        )
        
        # Display results
        print("\n" + "=" * 70)
        print("✅ Build Complete!")
        print("=" * 70)
        print(f"📊 Results:")
        print(f"   • Components identified: {len(result.get('inferred_tasks', []))}")
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
        
        # Show inferred components
        if result.get('inferred_tasks'):
            print(f"\n🧠 AI-Inferred Components:")
            for i, task in enumerate(result['inferred_tasks'], 1):
                task_name = task.get('task', 'unknown')
                task_type = task.get('type', 'unknown')
                print(f"   {i}. {task_name} ({task_type})")
        
        print("\n" + "=" * 70)
        print("🎉 Success! Your AI-powered app is ready to run.")
        print("=" * 70)
        print("\n💡 Next steps:")
        print(f"   1. cd {OUTPUT_DIR}")
        print("   2. pip install flask openai pillow")
        print("   3. python app.py")
        print("   4. Open http://localhost:5001 in your browser")
        print("   5. Upload an image to get AI-generated commentary!")
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


