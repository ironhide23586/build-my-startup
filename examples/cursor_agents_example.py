"""
Example: Multiple Cursor-like AI agents collaborating on a coding task.
This demonstrates how multiple AI agents can work together asynchronously.
"""
import asyncio
from agent_framework.message_bus import MessageBus
from agent_framework.ai_agent import AIAgent, CodeReviewAgent, CodeWriterAgent, TestWriterAgent
from agent_framework.agent import Message
from agent_framework.workflow_utils import TaskTracker, wait_for_completion


async def cursor_agents_workflow():
    """
    Simulates how Cursor agents would collaborate on a coding task.
    Like having multiple AI assistants working together.
    """
    print("\n=== Cursor Agents Collaboration Workflow ===\n")
    
    # Create message bus for agent communication
    bus = MessageBus()
    
    # Create specialized AI agents (like different Cursor agent roles)
    writer = CodeWriterAgent(
        name="CodeWriter",
        message_bus=bus,
        system_prompt="You are an expert Python developer. Write clean, efficient code."
    )
    
    reviewer = CodeReviewAgent(
        name="CodeReviewer",
        message_bus=bus,
        system_prompt="You are a code review expert. Provide thorough, constructive feedback."
    )
    
    tester = TestWriterAgent(
        name="TestWriter",
        message_bus=bus,
        system_prompt="You are a QA expert. Write comprehensive test suites."
    )
    
    coordinator = AIAgent(
        name="Coordinator",
        role="project_manager",
        message_bus=bus,
        system_prompt="You coordinate tasks between agents and manage workflows."
    )
    
    # Register all agents
    all_agents = [writer, reviewer, tester, coordinator]
    for agent in all_agents:
        bus.register_agent(agent)
        agent.running = True
    
    # Create task tracker for workflow
    tracker = TaskTracker()
    code_task = tracker.create_task("code_generated")
    review_task = tracker.create_task("review_completed")
    
    # Conversation history for each agent
    def create_message_handler(agent_name, agent_id):
        async def handler(message: Message):
            print(f"[{agent_name}] 📨 Received: {message.content[:100]}...")
            
            # Handle different message types
            if message.message_type == "code_review_request":
                if agent_name == "CodeReviewer":
                    # Reviewer processes review request
                    print(f"[{agent_name}] 🔍 Reviewing code ({len(str(message.content))} chars)...")
                    await reviewer.handle_message_with_ai(message)
                    print(f"[{agent_name}] ✅ Review completed")
                    tracker.complete_task("review_completed")
            
            elif message.message_type == "write_code_request":
                if agent_name == "CodeWriter":
                    code = await writer.write_code(str(message.content))
                    print(f"[{agent_name}] ✅ Generated code ({len(code)} chars)")
                    tracker.complete_task("code_generated")
                    # Send to reviewer
                    await bus.send_to_agent(
                        agent_id,
                        reviewer.agent_id,
                        code,
                        "code_review_request"
                    )
            
            elif message.message_type == "ai_response":
                print(f"[{agent_name}] ✅ Got AI response")
            
        return handler
    
    # Set up handlers
    writer.message_handler = create_message_handler("CodeWriter", writer.agent_id)
    reviewer.message_handler = create_message_handler("CodeReviewer", reviewer.agent_id)
    tester.message_handler = create_message_handler("TestWriter", tester.agent_id)
    
    # Start message processing for all agents
    agent_tasks = [agent.receive_messages() for agent in all_agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    # Simulate a coding workflow
    async def run_workflow():
        await asyncio.sleep(0.2)  # Let agents initialize
        
        print("\n🚀 Starting coding workflow...\n")
        
        # Step 1: Coordinator requests code
        requirement = "Create a function that calculates fibonacci numbers"
        print(f"[Coordinator] 📝 Task: {requirement}\n")
        
        await bus.send_to_agent(
            coordinator.agent_id,
            writer.agent_id,
            requirement,
            "write_code_request"
        )
        
        # Efficiently poll for completion
        print("\n⏳ Waiting for workflow to complete...")
        completed = await wait_for_completion(
            all_agents,
            task_tracker=tracker,
            task_ids=["code_generated", "review_completed"],
            timeout=90.0,
            poll_interval=0.5,
            show_progress=True
        )
        
        if completed:
            print("\n✅ Workflow completed!\n")
        else:
            print("\n⚠️  Workflow timed out (some tasks may still be processing)\n")
        
        # Stop all agents
        await asyncio.sleep(1)
        for agent in all_agents:
            agent.running = False
    
    # Run everything concurrently
    await asyncio.gather(message_processing, run_workflow())


async def parallel_agents_demo():
    """
    Multiple agents working on different tasks in parallel.
    """
    print("\n=== Parallel Agent Tasks ===\n")
    
    bus = MessageBus()
    
    # Create coordinator
    from agent_framework.agent import Agent
    coordinator = Agent(name="Coordinator")
    bus.register_agent(coordinator)
    
    # Create multiple specialized agents
    frontend_agent = CodeWriterAgent(
        name="FrontendDev",
        message_bus=bus,
        system_prompt="You specialize in frontend development with React/TypeScript."
    )
    
    backend_agent = CodeWriterAgent(
        name="BackendDev",
        message_bus=bus,
        system_prompt="You specialize in backend development with Python/FastAPI."
    )
    
    devops_agent = AIAgent(
        name="DevOps",
        role="devops_engineer",
        message_bus=bus,
        system_prompt="You specialize in infrastructure and deployment."
    )
    
    # Register remaining agents (coordinator already registered)
    bus.register_agent(frontend_agent)
    bus.register_agent(backend_agent)
    bus.register_agent(devops_agent)
    
    # Create task tracker for parallel tasks
    tracker = TaskTracker()
    frontend_task = tracker.create_task("frontend_done")
    backend_task = tracker.create_task("backend_done")
    devops_task = tracker.create_task("devops_done")
    
    # Add handlers for agents to process tasks
    async def frontend_handler(message: Message):
        if message.message_type == "task":
            print(f"[FrontendDev] 💻 Generating: {message.content}")
            code = await frontend_agent.write_code(str(message.content))
            print(f"[FrontendDev] ✅ Completed ({len(code)} chars)")
            tracker.complete_task("frontend_done")
    
    async def backend_handler(message: Message):
        if message.message_type == "task":
            print(f"[BackendDev] 💻 Generating: {message.content}")
            code = await backend_agent.write_code(str(message.content))
            print(f"[BackendDev] ✅ Completed ({len(code)} chars)")
            tracker.complete_task("backend_done")
    
    async def devops_handler(message: Message):
        if message.message_type == "task":
            print(f"[DevOps] 💻 Generating: {message.content}")
            response = await devops_agent.generate_response(f"Provide instructions for: {message.content}")
            print(f"[DevOps] ✅ Completed ({len(response)} chars)")
            tracker.complete_task("devops_done")
    
    frontend_agent.message_handler = frontend_handler
    backend_agent.message_handler = backend_handler
    devops_agent.message_handler = devops_handler
    
    all_agents = [coordinator, frontend_agent, backend_agent, devops_agent]
    for agent in all_agents:
        agent.running = True
    
    # Start processing
    agent_tasks = [agent.receive_messages() for agent in all_agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    async def parallel_tasks():
        await asyncio.sleep(0.2)
        
        print("\n📤 Sending tasks to agents in parallel...\n")
        
        # Send tasks in parallel
        await asyncio.gather(
            bus.send_to_agent(
                coordinator.agent_id,
                frontend_agent.agent_id,
                "Create a login component",
                "task"
            ),
            bus.send_to_agent(
                coordinator.agent_id,
                backend_agent.agent_id,
                "Create a user authentication API",
                "task"
            ),
            bus.send_to_agent(
                coordinator.agent_id,
                devops_agent.agent_id,
                "Set up CI/CD pipeline",
                "task"
            )
        )
        
        # Efficiently poll for completion
        print("\n⏳ Waiting for all agents to complete...")
        completed = await wait_for_completion(
            [frontend_agent, backend_agent, devops_agent],
            task_tracker=tracker,
            task_ids=["frontend_done", "backend_done", "devops_done"],
            timeout=90.0,
            poll_interval=0.5,
            show_progress=True
        )
        
        if completed:
            print("\n✅ All parallel tasks completed!\n")
        else:
            print("\n⚠️  Some tasks timed out\n")
        for agent in all_agents:
            agent.running = False
    
    await asyncio.gather(message_processing, parallel_tasks())


async def agent_brainstorming():
    """
    Agents having a brainstorming session to solve a problem.
    """
    print("\n=== Agent Brainstorming Session ===\n")
    
    bus = MessageBus()
    
    # Create agents with different perspectives
    agent1 = AIAgent(
        name="Architect",
        role="solution_architect",
        message_bus=bus,
        system_prompt="Think about system architecture and design patterns."
    )
    
    agent2 = AIAgent(
        name="Optimizer",
        role="performance_engineer",
        message_bus=bus,
        system_prompt="Focus on performance, scalability, and efficiency."
    )
    
    agent3 = AIAgent(
        name="UXDesigner",
        role="product_designer",
        message_bus=bus,
        system_prompt="Consider user experience and product design."
    )
    
    all_agents = [agent1, agent2, agent3]
    for agent in all_agents:
        bus.register_agent(agent)
        agent.running = True
    
    # Custom handler for brainstorming - use each agent's own generate_response
    agent_dict = {agent.agent_id: agent for agent in all_agents}
    
    async def brainstorming_handler(message: Message):
        if message.message_type == "brainstorm":
            agent = agent_dict.get(message.receiver_id)
            if agent:
                agent_name = agent.name
                print(f"[{agent_name}] 💡 Idea: Processing...")
                # Use the agent's own generate_response method
                idea = await agent.generate_response(
                    f"Provide an idea about: {message.content}"
                )
                print(f"[{agent_name}] 💡 {idea[:150]}...")
                # Share with others
                await bus.broadcast_message(
                    message.receiver_id,
                    f"[{agent_name}]: {idea}",
                    "idea"
                )
    
    for agent in all_agents:
        agent.message_handler = brainstorming_handler
    
    agent_tasks = [agent.receive_messages() for agent in all_agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    async def brainstorm():
        await asyncio.sleep(0.2)
        
        # Start brainstorming session
        topic = "How to improve async agent communication"
        print(f"🧠 Brainstorming topic: {topic}\n")
        
        await bus.broadcast_message(
            agent1.agent_id,
            topic,
            "brainstorm"
        )
        
        await asyncio.sleep(3)
        for agent in all_agents:
            agent.running = False
    
    await asyncio.gather(message_processing, brainstorm())


async def main():
    """Run all Cursor agent examples."""
    # Note: These will work even without OpenAI API key (using mock responses)
    # To use real AI, set OPENAI_API_KEY environment variable
    
    print("=" * 60)
    print("Cursor Agents Communication Examples")
    print("=" * 60)
    print("\nNote: Set OPENAI_API_KEY for real AI responses")
    print("Otherwise agents will use mock responses\n")
    
    await cursor_agents_workflow()
    await asyncio.sleep(1)
    
    await parallel_agents_demo()
    await asyncio.sleep(1)
    
    await agent_brainstorming()


if __name__ == "__main__":
    asyncio.run(main())

