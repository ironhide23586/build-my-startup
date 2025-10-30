"""
Quick test to verify the agent system works with OpenAI.
"""
import asyncio
from agent_framework.message_bus import MessageBus
from agent_framework.ai_agent import CodeWriterAgent, CodeReviewAgent
from agent_framework.agent import Agent, Message


async def test_ai_agents():
    """Test that AI agents can communicate and use OpenAI."""
    print("=" * 60)
    print("Testing AI Agent System")
    print("=" * 60)
    
    # Create message bus
    bus = MessageBus()
    
    # Create test coordinator agent
    coordinator = Agent(name="TestCoordinator")
    bus.register_agent(coordinator)
    
    # Create agents
    print("\n1. Creating AI agents...")
    writer = CodeWriterAgent(name="CodeWriter", message_bus=bus)
    reviewer = CodeReviewAgent(name="CodeReviewer", message_bus=bus)
    
    print(f"   ✓ Writer agent created (Client: {writer.client is not None})")
    print(f"   ✓ Reviewer agent created (Client: {reviewer.client is not None})")
    
    # Register agents
    bus.register_agent(writer)
    bus.register_agent(reviewer)
    
    coordinator.running = True
    writer.running = True
    reviewer.running = True
    
    # Set up message handlers
    async def writer_handler(message: Message):
        if message.message_type == "test_request":
            print(f"\n   [{writer.name}] Received test request: {message.content}")
            # Generate simple code
            code = await writer.write_code("A simple hello world function in Python")
            print(f"   [{writer.name}] Generated code ({len(code)} chars)")
            # Send to reviewer
            await bus.send_to_agent(
                writer.agent_id,
                reviewer.agent_id,
                code,
                "code_review_request"
            )
    
    async def reviewer_handler(message: Message):
        if message.message_type == "code_review_request":
            print(f"\n   [{reviewer.name}] Received code for review ({len(str(message.content))} chars)")
            review = await reviewer.review_code(str(message.content), writer.agent_id)
            print(f"   [{reviewer.name}] Review completed ({len(review)} chars)")
            return review
    
    writer.message_handler = writer_handler
    reviewer.message_handler = reviewer_handler
    
    # Start message processing
    print("\n2. Starting message processing...")
    agent_tasks = [
        writer.receive_messages(),
        reviewer.receive_messages()
    ]
    message_processing = asyncio.gather(*agent_tasks)
    
    # Send test request
    async def run_test():
        await asyncio.sleep(0.5)  # Let agents initialize
        
        print("\n3. Sending test request...")
        await bus.send_to_agent(
            coordinator.agent_id,
            writer.agent_id,
            "Generate a simple hello world function",
            "test_request"
        )
        
        print("\n4. Waiting for agents to complete...")
        await asyncio.sleep(10)  # Give time for API calls
        
        print("\n5. Stopping agents...")
        coordinator.running = False
        writer.running = False
        reviewer.running = False
    
    try:
        await asyncio.gather(message_processing, run_test(), return_exceptions=True)
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        writer.running = False
        reviewer.running = False


if __name__ == "__main__":
    asyncio.run(test_ai_agents())

