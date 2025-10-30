"""
Use agents to create multiple MVPs for diverse project validation.
Agents will generate different types of projects to validate the framework.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_framework.message_bus import MessageBus
from agent_framework.ai_agent import CodeWriterAgent
from agent_framework.agent import Agent, Message
from agent_framework.workflow_utils import TaskTracker, wait_for_completion


async def create_mvps_with_agents():
    """Use agents to create multiple MVPs for diverse validation."""
    print("=" * 70)
    print("🚀 Creating Multiple MVPs with Agent Framework")
    print("=" * 70)
    
    bus = MessageBus()
    
    # Create MVP generator agent
    mvp_generator = CodeWriterAgent(
        name="MVPGenerator",
        message_bus=bus,
        system_prompt="You are an expert at creating diverse MVP projects. Generate complete MVP specifications, architecture, and code for different project types (web apps, CLI tools, APIs, games, etc.)."
    )
    
    coordinator = Agent(name="MVPCoordinator")
    
    bus.register_agent(mvp_generator)
    bus.register_agent(coordinator)
    
    mvp_generator.running = True
    coordinator.running = True
    
    tracker = TaskTracker()
    mvp_projects = []
    
    async def mvp_generator_handler(message: Message):
        if message.message_type == "create_mvp_request":
            mvp_type = message.content.get("mvp_type")
            mvp_desc = message.content.get("description")
            task_id = message.content.get("task_id")
            
            print(f"\n   [{mvp_generator.name}] 🏗️  Creating MVP: {mvp_type}")
            
            mvp_spec_prompt = f"""Create a complete MVP specification for: {mvp_type}

Description: {mvp_desc}

Generate:
1. Project structure (files needed)
2. Technology stack
3. Key features (MVP scope)
4. Build steps using the agent framework
5. Test strategy

Return as structured markdown."""
            
            spec = await mvp_generator.generate_response(mvp_spec_prompt)
            mvp_projects.append({"type": mvp_type, "spec": spec})
            tracker.complete_task(task_id)
            
            print(f"   [{mvp_generator.name}] ✅ MVP specification generated")
    
    mvp_generator.message_handler = mvp_generator_handler
    
    # MVP types for diverse validation
    mvp_types = [
        {"type": "CLI Task Manager", "desc": "Command-line task manager with add/complete/list"},
        {"type": "REST API Server", "desc": "Simple REST API with CRUD operations"},
        {"type": "Data Visualization Tool", "desc": "Tool to visualize CSV data"},
        {"type": "File Organizer", "desc": "Organizes files by type/date"}
    ]
    
    async def coordinate_mvps():
        await asyncio.sleep(0.5)
        
        print("\n📋 Generating MVP specifications...")
        for mvp_info in mvp_types:
            task_id = f"mvp_{mvp_info['type'].replace(' ', '_')}"
            tracker.create_task(task_id)
            
            await bus.send_to_agent(
                coordinator.agent_id,
                mvp_generator.agent_id,
                {
                    "mvp_type": mvp_info["type"],
                    "description": mvp_info["desc"],
                    "task_id": task_id
                },
                "create_mvp_request"
            )
            await asyncio.sleep(2)
        
        task_ids = [f"mvp_{t['type'].replace(' ', '_')}" for t in mvp_types]
        await wait_for_completion([mvp_generator], tracker, task_ids, 60.0, 1.0)
        
        print("\n" + "=" * 70)
        print("📊 Generated MVP Specifications:")
        for project in mvp_projects:
            print(f"\n✅ {project['type']}")
            print(f"   Spec length: {len(project['spec'])} chars")
        
        mvp_generator.running = False
        coordinator.running = False
    
    agent_tasks = [mvp_generator.receive_messages()]
    
    await asyncio.gather(
        asyncio.gather(*agent_tasks),
        coordinate_mvps()
    )


if __name__ == "__main__":
    asyncio.run(create_mvps_with_agents())

