"""
Utility functions for efficient polling and workflow completion tracking.
"""
import asyncio
from typing import Dict, Set, Optional
from .agent import Agent


async def wait_for_queue_empty(agent: Agent, timeout: float = 60.0, poll_interval: float = 0.5) -> bool:
    """
    Efficiently poll until agent's message queue is empty.
    
    Args:
        agent: The agent to check
        timeout: Maximum time to wait in seconds
        poll_interval: How often to check (in seconds)
    
    Returns:
        True if queue emptied, False if timeout
    """
    elapsed = 0.0
    while elapsed < timeout:
        if agent.message_queue.empty():
            return True
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return False


async def wait_for_agents_idle(agents: list, timeout: float = 60.0, poll_interval: float = 0.5) -> bool:
    """
    Wait until all agents' queues are empty.
    
    Args:
        agents: List of agents to check
        timeout: Maximum time to wait in seconds
        poll_interval: How often to check (in seconds)
    
    Returns:
        True if all queues emptied, False if timeout
    """
    elapsed = 0.0
    while elapsed < timeout:
        if all(agent.message_queue.empty() for agent in agents):
            # Give a bit more time for any processing that started
            await asyncio.sleep(0.2)
            if all(agent.message_queue.empty() for agent in agents):
                return True
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return False


class TaskTracker:
    """Track completion of specific tasks using events."""
    
    def __init__(self):
        self.events: Dict[str, asyncio.Event] = {}
        self.completed: Set[str] = set()
    
    def create_task(self, task_id: str) -> asyncio.Event:
        """Create a new task event."""
        event = asyncio.Event()
        self.events[task_id] = event
        return event
    
    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        if task_id in self.events:
            self.completed.add(task_id)
            self.events[task_id].set()
    
    async def wait_for_task(self, task_id: str, timeout: float = 60.0) -> bool:
        """
        Wait for a specific task to complete.
        
        Returns:
            True if completed, False if timeout
        """
        if task_id not in self.events:
            return False
        
        try:
            await asyncio.wait_for(self.events[task_id].wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    async def wait_for_all_tasks(self, task_ids: list, timeout: float = 60.0) -> bool:
        """
        Wait for all specified tasks to complete.
        
        Returns:
            True if all completed, False if timeout
        """
        tasks = [self.wait_for_task(task_id, timeout) for task_id in task_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return all(r is True for r in results)


async def wait_for_completion(
    agents: list,
    task_tracker: Optional[TaskTracker] = None,
    task_ids: Optional[list] = None,
    timeout: float = 60.0,
    poll_interval: float = 0.3,
    show_progress: bool = False
) -> bool:
    """
    Efficiently wait for workflow completion using multiple strategies.
    
    Args:
        agents: List of agents to check
        task_tracker: Optional TaskTracker for specific task completion
        task_ids: Optional list of task IDs to wait for
        timeout: Maximum time to wait
        poll_interval: Polling interval in seconds
        show_progress: Whether to show progress dots
    
    Returns:
        True if completed, False if timeout
    """
    elapsed = 0.0
    last_progress = 0.0
    
    while elapsed < timeout:
        # Check task tracker if provided
        if task_tracker and task_ids:
            completed_tasks = sum(1 for tid in task_ids if tid in task_tracker.completed)
            all_tasks_done = all(task_id in task_tracker.completed for task_id in task_ids)
            
            if show_progress and elapsed - last_progress > 2.0:
                print(f"  [{completed_tasks}/{len(task_ids)} tasks completed]...", end="", flush=True)
                last_progress = elapsed
            
            if all_tasks_done:
                # Give a moment for any final processing
                await asyncio.sleep(0.2)
                if show_progress:
                    print()  # New line after progress
                return True
        
        # Check if all agent queues are empty (fallback check)
        all_empty = all(agent.message_queue.empty() for agent in agents)
        if all_empty:
            # Wait a bit to see if any new messages arrive
            await asyncio.sleep(poll_interval)
            if all(agent.message_queue.empty() for agent in agents):
                if show_progress:
                    print()  # New line after progress
                return True
        
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    
    if show_progress:
        print(f"\n  ⏱️  Timeout after {timeout:.1f}s")
    return False

