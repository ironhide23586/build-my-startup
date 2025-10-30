"""
Agent class for asynchronous communication between multiple agents.
"""
import asyncio
import uuid
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Message structure for agent communication."""
    sender_id: str
    receiver_id: str
    content: Any
    message_type: str = "default"
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class Agent:
    """An agent that can asynchronously communicate with other agents."""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        message_handler: Optional[Callable] = None
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or f"Agent-{self.agent_id[:8]}"
        self.message_handler = message_handler or self.default_message_handler
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        
    async def default_message_handler(self, message: Message) -> None:
        """Default message handler - prints received messages."""
        print(f"[{self.name}] Received from {message.sender_id[:8]}: {message.content}")
    
    async def send_message(
        self,
        receiver: 'Agent',
        content: Any,
        message_type: str = "default"
    ) -> None:
        """Send a message to another agent asynchronously."""
        message = Message(
            sender_id=self.agent_id,
            receiver_id=receiver.agent_id,
            content=content,
            message_type=message_type
        )
        await receiver.message_queue.put(message)
        print(f"[{self.name}] Sent to {receiver.name}: {content}")
    
    async def receive_messages(self) -> None:
        """Process incoming messages asynchronously."""
        while self.running or not self.message_queue.empty():
            try:
                # Wait for message with timeout to allow checking running status
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=0.1
                )
                await self.message_handler(message)
                self.message_queue.task_done()
            except asyncio.TimeoutError:
                continue
    
    async def start(self) -> None:
        """Start the agent's message processing loop."""
        self.running = True
        print(f"[{self.name}] Agent started (ID: {self.agent_id[:8]})")
        await self.receive_messages()
    
    async def stop(self) -> None:
        """Stop the agent's message processing loop."""
        self.running = False
        print(f"[{self.name}] Agent stopped")
    
    async def run_async(self, coro_func: Callable, *args, **kwargs) -> None:
        """Run an async function concurrently with message processing."""
        await asyncio.gather(
            self.receive_messages(),
            coro_func(*args, **kwargs)
        )

