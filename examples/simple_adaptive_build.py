"""
Simple example: Build an app from just a high-level description.

This demonstrates the Adaptive Build Pipeline - you just describe what you want,
and AI agents figure out what needs to be built and generate it.
"""
import asyncio
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_my_startup.pipelines.adaptive_build import build_adaptive_sync
from build_my_startup.paths import default_app_paths


# ============================================================================
# USER INPUT: Just describe your startup idea in plain English!
# ============================================================================

STARTUP_IDEA = """
Build a simple task manager CLI tool.

Users should be able to:
- Add tasks with a description
- Mark tasks as complete
- List all tasks (showing which are done)
- Delete tasks

Store tasks in a JSON file. Make it work on Mac. Keep it simple - just a command-line tool.
"""

OUTPUT_DIR = "/Users/souhamb/a2a_comm/apps/task_manager_app/generated"


def main():
    """Build the app."""
    print("\n" + "=" * 70)
    print("🚀 Simple Adaptive Build Example")
    print("=" * 70)
    print("\n📝 Your idea:")
    print(STARTUP_IDEA.strip())
    print("\n🤖 AI agents will now:")
    print("   1. Analyze your idea")
    print("   2. Figure out what files are needed")
    print("   3. Generate all the code")
    print("   4. Test everything")
    print("\nThis may take 2-3 minutes...\n")
    
    # Run the adaptive build - it does everything automatically!
    result = build_adaptive_sync(
        description=STARTUP_IDEA,
        output_dir=OUTPUT_DIR,
        target_platform="macOS",
        tech_preferences={"type": "CLI", "language": "Python"},
        generate_plan=True,
        show_progress=True,
        min_files=2,
        max_files=4,  # Keep it small for testing
        timeout=180.0  # 3 minutes
    )
    
    print("\n" + "=" * 70)
    print("✅ Done!")
    print("=" * 70)
    print(f"Generated {result['generated']} files")
    print(f"Saved {result['saved']} files")
    print(f"\n📁 {OUTPUT_DIR}")
    
    if result.get('inferred_tasks'):
        print("\n🧠 AI figured out these components:")
        for task in result['inferred_tasks']:
            print(f"   • {task['task']}")
    
    return result


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result['saved'] > 0 else 1)

