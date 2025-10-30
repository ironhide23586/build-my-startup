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

    agents["IdeationAgent"] = CodeWriterAgent(
        name="IdeationAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert startup architect and product designer. Given a high-level startup idea or product "
            "description, you break it down into concrete technical components, files, and implementation tasks. "
            "You identify what needs to be built (backend, frontend, APIs, agents, handlers, etc.), what technologies "
            "to use, and provide detailed descriptions for each component. You think about architecture, user flow, "
            "data handling, and integration points. Generate comprehensive, actionable build task specifications."
        ),
    )

    agents["FrontendTestAgent"] = CodeWriterAgent(
        name="FrontendTestAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert frontend testing engineer. You test HTML, CSS, and JavaScript files for correctness. "
            "You have access to testing tools: test_html_file(), test_javascript_file(), test_css_file(). "
            "You analyze test results, identify issues, and generate fixes. You understand browser compatibility, "
            "DOM structure, CSS syntax, and JavaScript best practices. When tests fail, you provide clear, "
            "actionable fixes. You iterate until all frontend tests pass."
        ),
    )

    agents["BackendTestAgent"] = CodeWriterAgent(
        name="BackendTestAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert backend testing engineer. You test Python code for syntax, imports, and runtime errors. "
            "You have access to testing tools: test_python_file(). You analyze test results, identify issues with "
            "imports, logic errors, syntax problems, and runtime exceptions. You generate fixes that pass tests. "
            "You understand Python best practices, error handling, and proper code structure. You iterate until "
            "all backend tests pass."
        ),
    )

    agents["IntegrationTestAgent"] = CodeWriterAgent(
        name="IntegrationTestAgent",
        message_bus=bus,
        system_prompt=(
            "You are an expert integration testing engineer. You verify that frontend and backend components work "
            "together correctly. You check API endpoints, data flow, request/response formats, error handling, and "
            "edge cases. You identify integration issues between components and suggest fixes. You ensure the entire "
            "system works as a cohesive whole."
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


