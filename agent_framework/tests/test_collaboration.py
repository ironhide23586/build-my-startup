"""
Test multi-agent collaboration with real OpenAI API calls.
"""
import asyncio
from agent_framework.message_bus import MessageBus
from agent_framework.ai_agent import CodeWriterAgent, CodeReviewAgent
from agent_framework.agent import Message


async def test_real_collaboration():
    """Test real AI agents collaborating on a task."""
    print("=" * 60)
    print("Testing Real AI Agent Collaboration")
    print("=" * 60)
    
    bus = MessageBus()
    
    # Create a coordinator agent (simple agent, no AI needed)
    from agent_framework.agent import Agent
    coordinator = Agent(name="Coordinator")
    bus.register_agent(coordinator)
    
    # Create specialized agents
    writer = CodeWriterAgent(name="CodeWriter", message_bus=bus)
    reviewer = CodeReviewAgent(name="CodeReviewer", message_bus=bus)
    
    print(f"\n✅ CodeWriter created (OpenAI: {writer.client is not None})")
    print(f"✅ CodeReviewer created (OpenAI: {reviewer.client is not None})")
    
    bus.register_agent(writer)
    bus.register_agent(reviewer)
    
    writer.running = True
    reviewer.running = True
    
    # Track the workflow
    code_generated = False
    review_received = False
    
    async def writer_handler(message: Message):
        nonlocal code_generated
        if message.message_type == "write_request":
            print(f"\n📝 [{writer.name}] Generating code: {message.content}")
            code = await writer.write_code(str(message.content))
            code_generated = True
            print(f"✅ [{writer.name}] Code generated ({len(code)} chars)")
            
            # Send to reviewer
            await bus.send_to_agent(
                writer.agent_id,
                reviewer.agent_id,
                code,
                "code_review_request"
            )
    
    async def reviewer_handler(message: Message):
        nonlocal review_received
        if message.message_type == "code_review_request":
            print(f"\n🔍 [{reviewer.name}] Reviewing code...")
            review = await reviewer.review_code(str(message.content), writer.agent_id)
            review_received = True
            print(f"✅ [{reviewer.name}] Review completed ({len(review)} chars)")
            print(f"\n📄 Review Preview:\n{review[:300]}...")
    
    writer.message_handler = writer_handler
    reviewer.message_handler = reviewer_handler
    
    # Start message processing
    print("\n🚀 Starting agents...")
    agent_tasks = [
        writer.receive_messages(),
        reviewer.receive_messages()
    ]
    message_processing = asyncio.gather(*agent_tasks)
    
    # Trigger the workflow
    async def trigger_workflow():
        await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("Workflow: CodeWriter → CodeReviewer")
        print("=" * 60)
        
        # Request code generation
        await bus.send_to_agent(
            coordinator.agent_id,
            writer.agent_id,
            "Create a Python function that calculates factorial",
            "write_request"
        )
        
        # Wait for both agents to complete
        print("\n⏳ Waiting for agents to complete their work...")
        await asyncio.sleep(30)  # Allow time for API calls
        
        writer.running = False
        reviewer.running = False
        
        print("\n" + "=" * 60)
        print("Results:")
        print(f"  Code generated: {code_generated}")
        print(f"  Review completed: {review_received}")
        print("=" * 60)
    
    try:
        await asyncio.gather(message_processing, trigger_workflow(), return_exceptions=True)
        print("\n✅ Collaboration test completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        writer.running = False
        reviewer.running = False


if __name__ == "__main__":
    asyncio.run(test_real_collaboration())

