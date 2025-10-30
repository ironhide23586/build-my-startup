"""
Comprehensive Reference App: Recipe Manager

Demonstrates ALL framework features:
- Adaptive Build Pipeline (AI infers architecture)
- Git integration with AI-generated commit messages
- Frontend testing by specialized agents
- Backend testing by specialized agents
- Iterative debugging and fixing
- Agent framework integration
- Progress indicators and real-time feedback
"""
import asyncio
import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from build_my_startup.pipelines.adaptive_build import AdaptiveBuildConfig, AdaptiveBuildPipeline
from build_my_startup.paths import default_app_paths


# Get output paths
OUTPUT_DIR, TEMPLATES_DIR, STATIC_DIR = default_app_paths(__file__)


# ============================================================================
# STARTUP IDEA - Just a high-level description!
# The AI will figure out EVERYTHING else automatically
# ============================================================================

STARTUP_IDEA = """
Build a Recipe Manager web application.

Users can:
- Add new recipes with ingredients, instructions, and cooking time
- View all recipes in a beautiful card layout
- Search recipes by name or ingredient
- Mark recipes as favorites
- Delete recipes they don't want

Technical requirements:
- Flask backend with RESTful API
- Store recipes in a JSON file (recipes.json)
- Beautiful, modern frontend with responsive design
- Use vanilla JavaScript (no frameworks)
- Real-time search filtering
- Agent that suggests recipe pairings based on ingredients
- Run locally on Mac

The app should have:
- Clean separation of frontend and backend
- Proper error handling
- Input validation
- Professional UI with gradients and smooth animations
- Mobile-friendly responsive design
"""

TARGET_PLATFORM = "macOS"

TECH_PREFERENCES = {
    "backend": "Flask",
    "frontend": "HTML/CSS/JavaScript (vanilla)",
    "storage": "JSON file",
    "api_style": "RESTful",
    "port": 5002,  # Different from other apps
    "agent_framework": "build_my_startup agents",
}


async def main():
    """Build the recipe manager using the adaptive pipeline with all features enabled."""
    
    print("=" * 80)
    print("🚀 COMPREHENSIVE FRAMEWORK DEMONSTRATION")
    print("   Building: Recipe Manager Web Application")
    print("=" * 80)
    print("\n📝 Startup Idea (High-Level Description):")
    print("-" * 80)
    print(STARTUP_IDEA.strip())
    print("-" * 80)
    
    # Check API key
    from build_my_startup.config import OPENAI_API_KEY as CONFIG_KEY
    api_key = os.getenv("OPENAI_API_KEY") or CONFIG_KEY
    
    if not api_key:
        print("\n❌ ERROR: OpenAI API key not found!")
        print("Please set OPENAI_API_KEY in config.py or environment")
        sys.exit(1)
    
    key_source = "environment" if os.getenv("OPENAI_API_KEY") else "config file"
    print(f"\n✅ OpenAI API key loaded from {key_source}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    
    # Configure with ALL features enabled
    config = AdaptiveBuildConfig(
        output_dir=OUTPUT_DIR,
        templates_dir=TEMPLATES_DIR,
        static_dir=STATIC_DIR,
        max_fix_attempts=3,  # Allow iterative fixing
        max_iterations_per_file=5,
        safe_commands_allowed=True,
        timeout=600.0,  # 10 minutes for complete build
        poll_interval=1.0,
        show_progress=True,
        generate_plan=True,
        ideation_timeout=60.0,
        min_files=5,  # Comprehensive app
        max_files=12,
        enable_git=True,  # ✅ Git integration
        use_ai_commit_messages=True,  # ✅ AI-generated commit messages
    )
    
    print("\n🎯 Framework Features Enabled:")
    print("   ✅ Adaptive Build (AI infers architecture)")
    print("   ✅ Git integration with AI commit messages")
    print("   ✅ Frontend testing agents (HTML/CSS/JS)")
    print("   ✅ Backend testing agents (Python)")
    print("   ✅ Iterative debugging and fixing")
    print("   ✅ Progress indicators")
    print("   ✅ Agent framework integration")
    
    print("\n🧠 Phase 1: AI will analyze your idea and infer architecture")
    print("🏗️  Phase 2: AI agents will generate, test, and debug all code")
    print("📝 Phase 3: Git commits will track every change with AI messages")
    print("\n⏱️  This will take 5-10 minutes. Sit back and watch the magic!\n")
    
    # Create and run the adaptive pipeline
    pipeline = AdaptiveBuildPipeline(config)
    
    try:
        result = await pipeline.run_adaptive_build(
            description=STARTUP_IDEA,
            target_platform=TARGET_PLATFORM,
            tech_preferences=TECH_PREFERENCES
        )
        
        # Display comprehensive results
        print("\n" + "=" * 80)
        print("🎉 BUILD COMPLETE!")
        print("=" * 80)
        
        print(f"\n📊 Build Statistics:")
        print(f"   • Components identified: {len(result.get('inferred_tasks', []))}")
        print(f"   • Files generated: {result['generated']}")
        print(f"   • Files saved: {result['saved']}")
        print(f"   • Tests run: {len(result['tests'])}")
        
        # Test results
        passed = sum(1 for t in result['tests'].values() if t.get('passed'))
        if result['tests']:
            print(f"   • Tests passed: {passed}/{len(result['tests'])}")
        
        # Git info
        if result.get('git_enabled'):
            print(f"   • Git repository: Initialized with AI commit messages")
        
        print(f"\n📁 Location: {OUTPUT_DIR}")
        
        if result.get('plan'):
            print(f"📋 Plan: {os.path.join(OUTPUT_DIR, 'BUILD_PLAN.md')}")
        
        # Show AI-inferred components
        if result.get('inferred_tasks'):
            print(f"\n🧠 AI-Inferred Architecture:")
            for i, task in enumerate(result['inferred_tasks'], 1):
                task_name = task.get('task', 'unknown')
                task_type = task.get('type', 'unknown')
                priority = task.get('priority', 'N/A')
                print(f"   {i}. {task_name:30s} [{task_type:15s}] Priority: {priority}")
        
        # Git history
        if result.get('git_enabled'):
            print(f"\n📝 Git Commit History:")
            print(f"   Run: cd {OUTPUT_DIR} && git log --oneline")
            print(f"   To see AI-generated commit messages")
        
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! Recipe Manager is ready!")
        print("=" * 80)
        
        print("\n💡 Next Steps:")
        print(f"   1. cd {OUTPUT_DIR}")
        print("   2. pip install flask")
        print("   3. python app.py")
        print("   4. Open http://localhost:5002")
        print("   5. Start managing recipes!")
        
        print("\n🔍 Explore the code:")
        print("   - Backend API: app.py")
        print("   - Frontend: templates/index.html")
        print("   - Styling: static/styles.css")
        print("   - Logic: static/script.js")
        print("   - Data: recipes.json")
        
        print("\n📚 Framework Features Demonstrated:")
        print("   ✅ AI architectural inference")
        print("   ✅ Automatic git commits with AI messages")
        print("   ✅ Specialized testing agents")
        print("   ✅ Iterative debugging")
        print("   ✅ Complete working application")
        print()
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ Build Failed")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Run the async build process
    result = asyncio.run(main())
    
    # Exit with success code
    sys.exit(0 if result['saved'] > 0 else 1)

