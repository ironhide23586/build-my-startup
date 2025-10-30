"""
Test basic agent messaging without OpenAI to verify communication works.
"""
import asyncio
from agent_framework.message_bus import MessageBus
from agent_framework.agent import Agent, Message


async def test_basic_messaging():
    """Test that agents can send/receive messages."""
    print("=" * 60)
    print("Testing Basic Agent Communication")
    print("=" * 60)
    
    bus = MessageBus()
    
    # Create simple agents
    agent1 = Agent(name="Agent1")
    agent2 = Agent(name="Agent2")
    
    bus.register_agent(agent1)
    bus.register_agent(agent2)
    
    agent1.running = True
    agent2.running = True
    
    # Track received messages
    agent1_messages = []
    agent2_messages = []
    
    async def handler1(message: Message):
        agent1_messages.append(message)
        print(f"[Agent1] ✓ Received: {message.content[:50]}...")
    
    async def handler2(message: Message):
        agent2_messages.append(message)
        print(f"[Agent2] ✓ Received: {message.content[:50]}...")
        # Respond back
        await bus.send_to_agent(
            agent2.agent_id,
            agent1.agent_id,
            f"Got it! Thanks for '{message.content}'",
            "response"
        )
    
    agent1.message_handler = handler1
    agent2.message_handler = handler2
    
    # Start processing
    tasks = [
        agent1.receive_messages(),
        agent2.receive_messages()
    ]
    message_processing = asyncio.gather(*tasks)
    
    async def send_messages():
        await asyncio.sleep(0.2)
        
        print("\n📤 Testing direct message...")
        await agent1.send_message(agent2, "Hello from Agent1!")
        
        await asyncio.sleep(0.3)
        
        print("\n📤 Testing message bus...")
        await bus.send_to_agent(
            agent1.agent_id,
            agent2.agent_id,
            "Message via bus",
            "test"
        )
        
        await asyncio.sleep(0.3)
        
        print("\n📢 Testing broadcast...")
        await bus.broadcast_message(
            agent1.agent_id,
            "Important announcement!",
            "broadcast"
        )
        
        await asyncio.sleep(0.5)
        
        agent1.running = False
        agent2.running = False
    
    await asyncio.gather(message_processing, send_messages())
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  Agent1 received {len(agent1_messages)} messages")
    print(f"  Agent2 received {len(agent2_messages)} messages")
    print("=" * 60)
    
    return len(agent1_messages) > 0 and len(agent2_messages) > 0


if __name__ == "__main__":
    result = asyncio.run(test_basic_messaging())
    print("\n✅ Basic messaging test:", "PASSED" if result else "FAILED")

