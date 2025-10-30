"""
Test the generated commentary app - verify it was built correctly.
"""
import asyncio
import sys
import os

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_DIR = os.path.join(APP_ROOT, "generated")
sys.path.insert(0, APP_ROOT)
sys.path.insert(0, GENERATED_DIR)

from build_my_startup.message_bus import MessageBus
from build_my_startup.ai_agent import CodeWriterAgent
from build_my_startup.agent import Agent, Message
from build_my_startup.workflow_utils import TaskTracker, wait_for_completion


async def test_app_with_agents():
    """Use agents to test the generated app."""
    print("=" * 70)
    print("🧪 Testing AI Commentary Generator App")
    print("=" * 70)
    
    bus = MessageBus()
    
    tester = CodeWriterAgent(
        name="AppTester",
        message_bus=bus,
        system_prompt="You are an expert at testing web applications. Validate imports, structure, and basic functionality."
    )
    
    coordinator = Agent(name="TestCoordinator")
    
    bus.register_agent(tester)
    bus.register_agent(coordinator)
    
    tester.running = True
    coordinator.running = True
    
    tracker = TaskTracker()
    test_results = {}
    
    async def tester_handler(message: Message):
        if message.message_type == "test_request":
            test_type = message.content.get("test_type")
            task_id = message.content.get("task_id")
            
            print(f"\n   [{tester.name}] 🧪 Testing: {test_type}")
            
            if test_type == "directory_structure":
                # Check if generated directory exists
                if os.path.exists(GENERATED_DIR):
                    files = os.listdir(GENERATED_DIR)
                    print(f"   [{tester.name}] ✓ Generated directory exists")
                    print(f"   [{tester.name}]   Files: {files}")
                    test_results[test_type] = {"passed": True, "files": files}
                else:
                    print(f"   [{tester.name}] ❌ Generated directory not found")
                    test_results[test_type] = {"passed": False}
            
            elif test_type == "app_file":
                # Check if app.py exists
                app_file = os.path.join(GENERATED_DIR, "app.py")
                if os.path.exists(app_file):
                    try:
                        with open(app_file, 'r') as f:
                            content = f.read()
                        has_flask = "flask" in content.lower()
                        has_routes = "@app.route" in content
                        print(f"   [{tester.name}] ✓ app.py exists ({len(content)} bytes)")
                        print(f"   [{tester.name}]   Has Flask: {has_flask}, Has Routes: {has_routes}")
                        test_results[test_type] = {
                            "passed": has_flask and has_routes,
                            "size": len(content)
                        }
                    except Exception as e:
                        print(f"   [{tester.name}] ❌ Error reading app.py: {e}")
                        test_results[test_type] = {"passed": False, "error": str(e)}
                else:
                    print(f"   [{tester.name}] ❌ app.py not found")
                    test_results[test_type] = {"passed": False}
            
            elif test_type == "html_template":
                # Check if HTML template exists
                template_file = os.path.join(GENERATED_DIR, "templates", "index.html")
                if os.path.exists(template_file):
                    try:
                        with open(template_file, 'r') as f:
                            content = f.read()
                        has_html = "<!DOCTYPE" in content or "<html" in content
                        print(f"   [{tester.name}] ✓ index.html exists ({len(content)} bytes)")
                        print(f"   [{tester.name}]   Valid HTML: {has_html}")
                        test_results[test_type] = {"passed": has_html, "size": len(content)}
                    except Exception as e:
                        print(f"   [{tester.name}] ❌ Error reading index.html: {e}")
                        test_results[test_type] = {"passed": False, "error": str(e)}
                else:
                    print(f"   [{tester.name}] ❌ index.html not found")
                    test_results[test_type] = {"passed": False}
            
            elif test_type == "build_plan":
                # Check if build plan exists
                plan_file = os.path.join(GENERATED_DIR, "BUILD_PLAN.md")
                if os.path.exists(plan_file):
                    try:
                        with open(plan_file, 'r') as f:
                            content = f.read()
                        print(f"   [{tester.name}] ✓ BUILD_PLAN.md exists ({len(content)} bytes)")
                        test_results[test_type] = {"passed": True, "size": len(content)}
                    except Exception as e:
                        print(f"   [{tester.name}] ❌ Error reading BUILD_PLAN.md: {e}")
                        test_results[test_type] = {"passed": False, "error": str(e)}
                else:
                    print(f"   [{tester.name}] ⚠️  BUILD_PLAN.md not found (optional)")
                    test_results[test_type] = {"passed": True, "optional": True}
            
            tracker.complete_task(task_id)
    
    tester.message_handler = tester_handler
    
    async def coordinate_tests():
        await asyncio.sleep(0.5)
        
        tests = [
            {"type": "directory_structure", "name": "Directory Structure"},
            {"type": "app_file", "name": "Flask App File"},
            {"type": "html_template", "name": "HTML Template"},
            {"type": "build_plan", "name": "Build Plan"}
        ]
        
        print("\n🧪 Running tests...")
        for test in tests:
            task_id = f"test_{test['type']}"
            tracker.create_task(task_id)
            
            await bus.send_to_agent(
                coordinator.agent_id,
                tester.agent_id,
                {"test_type": test["type"], "task_id": task_id},
                "test_request"
            )
            await asyncio.sleep(1)
        
        task_ids = [f"test_{t['type']}" for t in tests]
        await wait_for_completion([tester], tracker, task_ids, 30.0, 0.5)
        
        print("\n" + "=" * 70)
        print("📊 Test Results:")
        passed_count = 0
        total_count = 0
        for test_type, result in test_results.items():
            if not result.get("optional"):
                total_count += 1
                if result.get("passed"):
                    passed_count += 1
            
            status = "✅ PASSED" if result.get("passed") else "❌ FAILED"
            optional = " (optional)" if result.get("optional") else ""
            print(f"   {status} - {test_type}{optional}")
            if not result.get("passed") and "error" in result:
                print(f"      Error: {result['error']}")
        
        print(f"\n   Summary: {passed_count}/{total_count} tests passed")
        
        tester.running = False
        coordinator.running = False
    
    agent_tasks = [tester.receive_messages()]
    
    await asyncio.gather(
        asyncio.gather(*agent_tasks),
        coordinate_tests()
    )


if __name__ == "__main__":
    asyncio.run(test_app_with_agents())

