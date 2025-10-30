"""
Quick test build - minimal files, less testing for faster iteration.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_my_startup.pipelines.adaptive_build import AdaptiveBuildConfig, AdaptiveBuildPipeline

STARTUP_IDEA = """
Build a simple calculator CLI tool.
Just add and subtract two numbers.
Store result in a text file.
"""

OUTPUT_DIR = "/Users/souhamb/a2a_comm/apps/calculator_app/generated"

async def main():
    print("🚀 Quick Test Build (minimal components, faster testing)\n")
    
    config = AdaptiveBuildConfig(
        output_dir=OUTPUT_DIR,
        templates_dir=os.path.join(OUTPUT_DIR, "templates"),
        static_dir=os.path.join(OUTPUT_DIR, "static"),
        max_fix_attempts=1,  # Less fixing
        max_iterations_per_file=2,  # Less iteration
        timeout=180.0,
        generate_plan=False,  # Skip plan generation
        min_files=1,
        max_files=2  # Only 1-2 files
    )
    
    pipeline = AdaptiveBuildPipeline(config)
    result = await pipeline.run_adaptive_build(STARTUP_IDEA, "macOS", {})
    
    print(f"\n✅ Generated {result['generated']} files")
    print(f"✅ Saved {result['saved']} files to {OUTPUT_DIR}")
    
    if result['saved'] > 0:
        print("\n📁 Generated files:")
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                print(f"   - {os.path.relpath(filepath, OUTPUT_DIR)}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n{'✅ Success!' if result['saved'] > 0 else '❌ No files saved'}")

