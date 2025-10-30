from typing import Dict

from .message_bus import MessageBus
from .ai_agent import CodeWriterAgent, CodeReviewAgent
from .agent import Agent


def create_default_agents(bus: MessageBus) -> Dict[str, Agent]:
    """Create the standard set of agents used by builders."""
    agents: Dict[str, Agent] = {}

    agents["Coordinator"] = Agent(name="BuildCoordinator")
    agents["PlannerAgent"] = CodeWriterAgent(
        name="PlannerAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert project planner. Generate comprehensive markdown plans with objectives, "
            "timelines, agent assignments, locations, and methodologies. Create clear, actionable plans "
            "that coordinate multiple agents working together."
        ),
    )

    agents["CodeWriter"] = CodeWriterAgent(name="CodeWriter", message_bus=bus)
    agents["CodeReviewer"] = CodeReviewAgent(name="CodeReviewer", message_bus=bus)

    agents["TestGenerator"] = CodeWriterAgent(
        name="TestGenerator",
        message_bus=bus,
        system_prompt=(
            "You are an expert test engineer. Generate comprehensive test code that validates functionality, "
            "integration, and alignment with project requirements. Tests should run in a sandbox environment safely."
        ),
    )

    agents["TestRunner"] = Agent(name="TestRunner")

    agents["RollbackAgent"] = CodeWriterAgent(
        name="RollbackAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert at analyzing code and determining when rollbacks are needed. You assess test "
            "failures, integration issues, and code quality to decide if reverting to a previous working version "
            "is appropriate. Generate rollback decisions and restoration instructions."
        ),
    )

    agents["CommandGenerator"] = CodeWriterAgent(
        name="CommandGenerator",
        message_bus=bus,
        system_prompt=(
            "You are an expert at generating shell commands (zsh/bash) for macOS. Generate safe, executable "
            "commands for tasks like installing packages, running tests, setting up environments, etc. Always "
            "produce commands that are safe and appropriate for the task."
        ),
    )

    agents["CommandExecutor"] = Agent(name="CommandExecutor")

    agents["OfflineModelAgent"] = CodeWriterAgent(
        name="OfflineModelAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert at integrating offline/local AI models (Ollama, LM Studio, local LLM servers). "
            "Generate code for local model integration that can fallback to OpenAI if local models unavailable."
        ),
    )

    agents["IterationAgent"] = Agent(name="IterationAgent")

    agents["ValidationAgent"] = CodeWriterAgent(
        name="ValidationAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert at validating code correctness. Test code, identify bugs, and trigger fixes. "
            "You run actual tests and validate functionality."
        ),
    )

    return agents


def register_agents(bus: MessageBus, agents: Dict[str, Agent]) -> None:
    for agent in agents.values():
        bus.register_agent(agent)


def start_agents(agents: Dict[str, Agent]) -> None:
    for agent in agents.values():
        agent.running = True


def stop_agents(agents: Dict[str, Agent]) -> None:
    for agent in agents.values():
        agent.running = False


