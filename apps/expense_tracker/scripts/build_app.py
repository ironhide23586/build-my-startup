"""
Expense Tracker MVP - Framework demonstration with failure recovery.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from build_my_startup.pipelines.adaptive_build import AdaptiveBuildConfig, AdaptiveBuildPipeline
from build_my_startup.paths import default_app_paths

OUTPUT_DIR, TEMPLATES_DIR, STATIC_DIR = default_app_paths(__file__)

STARTUP_IDEA = """
Build an Expense Tracker CLI tool.

Users can:
- Add expenses with amount, category, and description
- List all expenses
- View total by category
- Delete expenses
- Export to CSV

Store in JSON file.
Keep it simple, CLI only, works on Mac.
"""

async def main():
    print("=" * 70)
    print("💰 Expense Tracker MVP - Framework-Generated")
    print("=" * 70)
    
    config = AdaptiveBuildConfig(
        output_dir=OUTPUT_DIR,
        min_files=2,
        max_files=4,
        timeout=180,
        ideation_timeout=30
    )
    
    print("\n🚀 Building (est. 2-3 min)...\n")
    
    pipeline = AdaptiveBuildPipeline(config)
    result = await pipeline.run_adaptive_build(STARTUP_IDEA, "macOS", {})
    
    print(f"\n✅ Done: {result['saved']} files saved")
    print(f"📁 {OUTPUT_DIR}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.get('saved', 0) > 0 else 1)

