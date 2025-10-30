"""
Example: Multiple agents having asynchronous conversations.
"""
import asyncio
from build_my_startup.agent import Agent, Message
from build_my_startup.message_bus import MessageBus


async def agent_conversation_demo():
    """Demonstrate direct agent-to-agent communication."""
    print("\n=== Direct Agent Communication Demo ===\n")
    
    # Create agents
    alice = Agent(name="Alice")
    bob = Agent(name="Bob")
    charlie = Agent(name="Charlie")
    
    # Custom message handler for Bob
    async def bob_handler(message: Message):
        print(f"[Bob] 💬 Got message from {message.sender_id[:8]}: {message.content}")
        # Bob responds to Alice
        if message.sender_id == alice.agent_id:
            await asyncio.sleep(0.5)  # Simulate processing time
            await bob.send_message(alice, "Thanks for the message, Alice!")
    
    bob.message_handler = bob_handler
    
    # Start all agents
    agents = [alice, bob, charlie]
    for agent in agents:
        agent.running = True
    
    # Start message processing for all agents concurrently
    agent_tasks = [agent.receive_messages() for agent in agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    # Simulate a conversation
    async def conversation():
        await asyncio.sleep(0.1)  # Give agents time to start
        await alice.send_message(bob, "Hello Bob!")
        await asyncio.sleep(0.2)
        await alice.send_message(charlie, "Hello Charlie!")
        await asyncio.sleep(0.2)
        await charlie.send_message(bob, "Hey Bob, did you get Alice's message?")
        await asyncio.sleep(1)
        
        # Stop all agents
        for agent in agents:
            agent.running = False
    
    # Run conversation and message processing concurrently
    await asyncio.gather(message_processing, conversation())


async def message_bus_demo():
    """Demonstrate communication via message bus."""
    print("\n=== Message Bus Communication Demo ===\n")
    
    # Create message bus
    bus = MessageBus()
    
    # Create agents with custom handlers
    async def worker_handler(message: Message):
        agent_name = message.receiver_id[:8]
        print(f"[Worker] Processing: {message.content}")
        # Send result back via bus
        await bus.send_to_agent(
            message.receiver_id,
            message.sender_id,
            f"Processed: {message.content}"
        )
    
    # Create different types of agents
    coordinator = Agent(name="Coordinator")
    worker1 = Agent(name="Worker-1", message_handler=worker_handler)
    worker2 = Agent(name="Worker-2", message_handler=worker_handler)
    monitor = Agent(name="Monitor")
    
    # Register all agents with the bus
    for agent in [coordinator, worker1, worker2, monitor]:
        bus.register_agent(agent)
        agent.running = True
    
    # Start message processing
    agent_tasks = [agent.receive_messages() for agent in [coordinator, worker1, worker2, monitor]]
    message_processing = asyncio.gather(*agent_tasks)
    
    async def coordinator_work():
        await asyncio.sleep(0.1)
        
        # Coordinator sends tasks to workers
        await bus.send_to_agent(
            coordinator.agent_id,
            worker1.agent_id,
            "Task 1: Process data batch A"
        )
        await bus.send_to_agent(
            coordinator.agent_id,
            worker2.agent_id,
            "Task 2: Process data batch B"
        )
        
        await asyncio.sleep(0.5)
        
        # Broadcast announcement
        await bus.broadcast_message(
            coordinator.agent_id,
            "Meeting in 5 minutes!"
        )
        
        await asyncio.sleep(1)
        
        # Stop all agents
        for agent in [coordinator, worker1, worker2, monitor]:
            agent.running = False
    
    await asyncio.gather(message_processing, coordinator_work())


async def topic_subscription_demo():
    """Demonstrate topic-based pub/sub communication."""
    print("\n=== Topic Subscription Demo ===\n")
    
    bus = MessageBus()
    
    # Create agents
    publisher = Agent(name="Publisher")
    
    async def subscriber_handler(message: Message):
        topic = message.message_type.replace("topic:", "")
        print(f"[{message.receiver_id[:8]}] Received on '{topic}': {message.content}")
    
    subscriber1 = Agent(name="Subscriber-1", message_handler=subscriber_handler)
    subscriber2 = Agent(name="Subscriber-2", message_handler=subscriber_handler)
    subscriber3 = Agent(name="Subscriber-3", message_handler=subscriber_handler)
    
    # Register agents
    for agent in [publisher, subscriber1, subscriber2, subscriber3]:
        bus.register_agent(agent)
        agent.running = True
    
    # Subscribe to topics
    bus.subscribe_to_topic(subscriber1.agent_id, "news")
    bus.subscribe_to_topic(subscriber2.agent_id, "news")
    bus.subscribe_to_topic(subscriber2.agent_id, "updates")
    bus.subscribe_to_topic(subscriber3.agent_id, "updates")
    
    # Start message processing
    all_agents = [publisher, subscriber1, subscriber2, subscriber3]
    agent_tasks = [agent.receive_messages() for agent in all_agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    async def publish_events():
        await asyncio.sleep(0.1)
        
        # Publish to "news" topic
        await bus.publish_to_topic(
            publisher.agent_id,
            "news",
            "Breaking: New feature released!"
        )
        
        await asyncio.sleep(0.5)
        
        # Publish to "updates" topic
        await bus.publish_to_topic(
            publisher.agent_id,
            "updates",
            "System maintenance scheduled for tonight"
        )
        
        await asyncio.sleep(1)
        
        # Stop all agents
        for agent in all_agents:
            agent.running = False
    
    await asyncio.gather(message_processing, publish_events())


async def complex_interaction_demo():
    """More complex example with multiple conversation patterns."""
    print("\n=== Complex Multi-Agent Interaction Demo ===\n")
    
    bus = MessageBus()
    
    # Create specialized agents
    async def researcher_handler(message: Message):
        if message.message_type == "research_query":
            result = f"Research result for: {message.content}"
            await bus.send_to_agent(
                message.receiver_id,
                message.sender_id,
                result,
                "research_result"
            )
    
    async def writer_handler(message: Message):
        if message.message_type == "research_result":
            article = f"Article written based on: {message.content}"
            await bus.broadcast_message(
                message.receiver_id,
                article,
                "article_published"
            )
    
    manager = Agent(name="Manager")
    researcher = Agent(name="Researcher", message_handler=researcher_handler)
    writer = Agent(name="Writer", message_handler=writer_handler)
    editor = Agent(name="Editor")
    
    # Register agents
    all_agents = [manager, researcher, writer, editor]
    for agent in all_agents:
        bus.register_agent(agent)
        agent.running = True
    
    # Subscribe editor to articles
    bus.subscribe_to_topic(editor.agent_id, "article_published")
    
    # Start processing
    agent_tasks = [agent.receive_messages() for agent in all_agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    async def workflow():
        await asyncio.sleep(0.1)
        
        # Manager initiates workflow
        await bus.send_to_agent(
            manager.agent_id,
            researcher.agent_id,
            "Investigate quantum computing trends",
            "research_query"
        )
        
        await asyncio.sleep(1.5)
        
        # Stop all agents
        for agent in all_agents:
            agent.running = False
    
    await asyncio.gather(message_processing, workflow())


async def main():
    """Run all demos."""
    await agent_conversation_demo()
    await asyncio.sleep(1)
    await message_bus_demo()
    await asyncio.sleep(1)
    await topic_subscription_demo()
    await asyncio.sleep(1)
    await complex_interaction_demo()


if __name__ == "__main__":
    asyncio.run(main())

