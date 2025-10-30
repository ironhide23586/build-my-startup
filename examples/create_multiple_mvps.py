"""
Use agent framework to create multiple MVPs for diverse validation.
Agents will create different project types to validate framework robustness.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_framework.message_bus import MessageBus
from agent_framework.ai_agent import CodeWriterAgent
from agent_framework.agent import Agent, Message
from agent_framework.workflow_utils import TaskTracker, wait_for_completion


async def create_multiple_mvps():
    """Create multiple MVPs using agent framework."""
    print("=" * 70)
    print("🚀 Creating Multiple MVPs for Framework Validation")
    print("=" * 70)
    
    bus = MessageBus()
    
    mvp_planner = CodeWriterAgent(
        name="MVPPlanner",
        message_bus=bus,
        system_prompt="You are an expert at planning diverse MVP projects. Generate complete MVP specifications covering CLI tools, web apps, APIs, games, utilities, etc."
    )
    
    coordinator = Agent(name="MVPCoordinator")
    
    bus.register_agent(mvp_planner)
    bus.register_agent(coordinator)
    
    mvp_planner.running = True
    coordinator.running = True
    
    tracker = TaskTracker()
    mvp_specs = {}
    
    async def planner_handler(message: Message):
        if message.message_type == "plan_mvp":
            mvp_type = message.content.get("mvp_type")
            task_id = message.content.get("task_id")
            
            print(f"\n   [{mvp_planner.name}] 📋 Planning MVP: {mvp_type}")
            
            spec_prompt = f"""Create complete MVP specification for: {mvp_type}

Include:
1. Project structure (files/directories)
2. Technology stack
3. Key features (MVP scope)
4. Agent framework usage (how agents would build it)
5. Test strategy

Return structured markdown."""
            
            spec = await mvp_planner.generate_response(spec_prompt)
            mvp_specs[mvp_type] = spec
            
            # Save spec
            mvp_dir = os.path.join(os.path.dirname(__file__), "mvps", mvp_type.replace(" ", "_").lower())
            os.makedirs(mvp_dir, exist_ok=True)
            spec_file = os.path.join(mvp_dir, "SPEC.md")
            with open(spec_file, "w") as f:
                f.write(spec)
            
            print(f"   [{mvp_planner.name}] ✅ MVP spec saved: {spec_file}")
            tracker.complete_task(task_id)
    
    mvp_planner.message_handler = planner_handler
    
    mvp_types = [
        "CLI Task Manager",
        "REST API Server", 
        "Data Visualization Tool",
        "File Organizer Bot",
        "Simple Game",
        "Note-taking App"
    ]
    
    async def coordinate():
        await asyncio.sleep(0.5)
        
        print("\n📋 Generating MVP specifications...")
        for mvp_type in mvp_types:
            task_id = f"plan_{mvp_type.replace(' ', '_')}"
            tracker.create_task(task_id)
            
            await bus.send_to_agent(
                coordinator.agent_id,
                mvp_planner.agent_id,
                {"mvp_type": mvp_type, "task_id": task_id},
                "plan_mvp"
            )
            await asyncio.sleep(3)
        
        task_ids = [f"plan_{t.replace(' ', '_')}" for t in mvp_types]
        await wait_for_completion([mvp_planner], tracker, task_ids, 120.0, 1.0)
        
        print("\n" + "=" * 70)
        print(f"✅ Generated {len(mvp_specs)} MVP Specifications")
        print("=" * 70)
        for mvp_type in mvp_specs:
            print(f"   ✓ {mvp_type}")
        
        mvp_planner.running = False
        coordinator.running = False
    
    await asyncio.gather(
        mvp_planner.receive_messages(),
        coordinate()
    )


if __name__ == "__main__":
    asyncio.run(create_multiple_mvps())

