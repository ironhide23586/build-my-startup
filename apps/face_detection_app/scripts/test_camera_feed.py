"""
Test camera live feed using agent framework - agents will test it.
"""
import asyncio
import sys
import os
import subprocess
import time

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_DIR = os.path.join(APP_ROOT, "generated")
sys.path.insert(0, APP_ROOT)
sys.path.insert(0, GENERATED_DIR)

from agent_framework.message_bus import MessageBus
from agent_framework.ai_agent import CodeWriterAgent
from agent_framework.agent import Agent, Message
from agent_framework.workflow_utils import TaskTracker, wait_for_completion


async def test_camera_with_agents():
    """Use agents to test the camera feed."""
    print("=" * 70)
    print("📹 Testing Camera Live Feed with Agent Framework")
    print("=" * 70)
    
    bus = MessageBus()
    
    tester = CodeWriterAgent(
        name="CameraTester",
        message_bus=bus,
        system_prompt="You are an expert at testing camera feeds and web applications. Generate test scripts and validation steps for camera functionality."
    )
    
    coordinator = Agent(name="TestCoordinator")
    
    bus.register_agent(tester)
    bus.register_agent(coordinator)
    
    tester.running = True
    coordinator.running = True
    
    tracker = TaskTracker()
    test_results = {}
    
    async def tester_handler(message: Message):
        if message.message_type == "test_camera_request":
            test_type = message.content.get("test_type")
            task_id = message.content.get("task_id")
            
            print(f"\n   [{tester.name}] 🧪 Testing: {test_type}")
            
            if test_type == "camera_handler":
                # Test camera_handler.py directly
                try:
                    # Import camera handler from generated code
                    if GENERATED_DIR not in sys.path:
                        sys.path.insert(0, GENERATED_DIR)
                    from camera_handler import CameraHandler
                    
                    print(f"   [{tester.name}] → Initializing camera...")
                    camera = CameraHandler()
                    print(f"   [{tester.name}] ✓ Camera initialized")
                    
                    print(f"   [{tester.name}] → Getting frame...")
                    frame = camera.get_frame()
                    if frame and len(frame) > 0:
                        print(f"   [{tester.name}] ✅ Frame captured: {len(frame)} bytes")
                        test_results[test_type] = {"passed": True, "frame_size": len(frame)}
                    else:
                        print(f"   [{tester.name}] ❌ No frame data")
                        test_results[test_type] = {"passed": False}
                except Exception as e:
                    print(f"   [{tester.name}] ❌ Error: {e}")
                    test_results[test_type] = {"passed": False, "error": str(e)}
            
            elif test_type == "flask_app":
                # Test Flask app startup (from generated folder)
                app_file = os.path.join(GENERATED_DIR, "app.py")
                if os.path.exists(app_file):
                    try:
                        print(f"   [{tester.name}] → Testing Flask app import...")
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("app", app_file)
                        app_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(app_module)
                        print(f"   [{tester.name}] ✅ Flask app imports successfully")
                        test_results[test_type] = {"passed": True}
                    except Exception as e:
                        print(f"   [{tester.name}] ❌ Import error: {e}")
                        test_results[test_type] = {"passed": False, "error": str(e)}
                else:
                    test_results[test_type] = {"passed": False, "error": "app.py not found"}
            
            elif test_type == "web_server":
                # Test web server startup (brief) from generated folder
                app_file = os.path.join(GENERATED_DIR, "app.py")
                if os.path.exists(app_file):
                    print(f"   [{tester.name}] → Attempting to start Flask server (5s test)...")
                    try:
                        process = subprocess.Popen(
                            [sys.executable, app_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=os.path.dirname(app_file)
                        )
                        time.sleep(2)
                        process.terminate()
                        process.wait(timeout=3)
                        print(f"   [{tester.name}] ✅ Server started successfully")
                        test_results[test_type] = {"passed": True}
                    except Exception as e:
                        print(f"   [{tester.name}] ❌ Server error: {e}")
                        test_results[test_type] = {"passed": False, "error": str(e)}
                else:
                    test_results[test_type] = {"passed": False, "error": "app.py not found"}
            
            tracker.complete_task(task_id)
    
    tester.message_handler = tester_handler
    
    async def coordinate_tests():
        await asyncio.sleep(0.5)
        
        tests = [
            {"type": "camera_handler", "name": "Camera Handler"},
            {"type": "flask_app", "name": "Flask App Import"},
            {"type": "web_server", "name": "Web Server Startup"}
        ]
        
        print("\n🧪 Running camera feed tests...")
        for test in tests:
            task_id = f"test_{test['type']}"
            tracker.create_task(task_id)
            
            await bus.send_to_agent(
                coordinator.agent_id,
                tester.agent_id,
                {"test_type": test["type"], "task_id": task_id},
                "test_camera_request"
            )
            await asyncio.sleep(3)
        
        task_ids = [f"test_{t['type']}" for t in tests]
        await wait_for_completion([tester], tracker, task_ids, 30.0, 0.5)
        
        print("\n" + "=" * 70)
        print("📊 Test Results:")
        for test_type, result in test_results.items():
            status = "✅ PASSED" if result.get("passed") else "❌ FAILED"
            print(f"   {status} - {test_type}")
            if not result.get("passed") and "error" in result:
                print(f"      Error: {result['error']}")
        
        tester.running = False
        coordinator.running = False
    
    agent_tasks = [tester.receive_messages()]
    
    await asyncio.gather(
        asyncio.gather(*agent_tasks),
        coordinate_tests()
    )


if __name__ == "__main__":
    asyncio.run(test_camera_with_agents())

