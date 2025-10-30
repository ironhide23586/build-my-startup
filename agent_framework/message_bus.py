"""
Message bus for centralized agent communication.
"""
import asyncio
from typing import Dict, List, Callable, Any, Optional
from .agent import Agent, Message


class MessageBus:
    """Central message bus for agent-to-agent communication."""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.subscribers: Dict[str, List[str]] = {}  # topic -> agent_ids
        self.running = False
    
    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the message bus."""
        self.agents[agent.agent_id] = agent
        print(f"[MessageBus] Registered agent: {agent.name} ({agent.agent_id[:8]})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the message bus."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"[MessageBus] Unregistered agent: {agent_id[:8]}")
    
    async def broadcast_message(
        self,
        sender_id: str,
        content: Any,
        message_type: str = "broadcast",
        exclude_sender: bool = True
    ) -> None:
        """Broadcast a message to all registered agents."""
        sender = self.agents.get(sender_id)
        if not sender:
            print(f"[MessageBus] Sender {sender_id[:8]} not found")
            return
        
        tasks = []
        for agent_id, agent in self.agents.items():
            if exclude_sender and agent_id == sender_id:
                continue
            message = Message(
                sender_id=sender_id,
                receiver_id=agent_id,
                content=content,
                message_type=message_type
            )
            tasks.append(agent.message_queue.put(message))
        
        await asyncio.gather(*tasks)
        print(f"[MessageBus] Broadcast from {sender.name}: {content}")
    
    async def send_to_agent(
        self,
        sender_id: str,
        receiver_id: str,
        content: Any,
        message_type: str = "default"
    ) -> None:
        """Send a message from one agent to another via the bus."""
        sender = self.agents.get(sender_id)
        receiver = self.agents.get(receiver_id)
        
        if not sender:
            print(f"[MessageBus] Sender {sender_id[:8]} not found")
            return
        if not receiver:
            print(f"[MessageBus] Receiver {receiver_id[:8]} not found")
            return
        
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type
        )
        await receiver.message_queue.put(message)
        print(f"[MessageBus] {sender.name} -> {receiver.name}: {content}")
    
    def subscribe_to_topic(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        if agent_id not in self.subscribers[topic]:
            self.subscribers[topic].append(agent_id)
            print(f"[MessageBus] {self.agents[agent_id].name} subscribed to '{topic}'")
    
    async def publish_to_topic(
        self,
        sender_id: str,
        topic: str,
        content: Any
    ) -> None:
        """Publish a message to all subscribers of a topic."""
        if topic not in self.subscribers:
            print(f"[MessageBus] No subscribers for topic '{topic}'")
            return
        
        sender = self.agents.get(sender_id)
        if not sender:
            return
        
        tasks = []
        for agent_id in self.subscribers[topic]:
            if agent_id != sender_id:  # Exclude sender
                agent = self.agents.get(agent_id)
                if agent:
                    message = Message(
                        sender_id=sender_id,
                        receiver_id=agent_id,
                        content=content,
                        message_type=f"topic:{topic}"
                    )
                    tasks.append(agent.message_queue.put(message))
        
        await asyncio.gather(*tasks)
        print(f"[MessageBus] Published to '{topic}': {content}")

