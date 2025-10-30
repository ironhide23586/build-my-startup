from typing import Dict

from .message_bus import MessageBus
from .ai_agent import CodeWriterAgent, CodeReviewAgent
from .agent import Agent
from .agent_directives import apply_core_directive


def create_default_agents(bus: MessageBus) -> Dict[str, Agent]:
    """Create the standard set of agents used by builders."""
    agents: Dict[str, Agent] = {}

    agents["Coordinator"] = Agent(name="BuildCoordinator")
    agents["PlannerAgent"] = CodeWriterAgent(
        name="PlannerAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert project planner. Generate markdown plans: objectives, timelines, agent assignments, "
            "locations, methodologies. Clear, actionable plans coordinating multiple agents."
        ),
    )

    agents["CodeWriter"] = CodeWriterAgent(
        name="CodeWriter",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert software developer. Write clean, efficient, documented code. Follow best practices."
        )
    )
    agents["CodeReviewer"] = CodeReviewAgent(
        name="CodeReviewer",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert code reviewer. Identify bugs, suggest improvements, check best practices. Clear, actionable feedback."
        )
    )

    agents["TestGenerator"] = CodeWriterAgent(
        name="TestGenerator",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert test engineer. Generate comprehensive test code validating functionality, integration, "
            "project requirements. Tests run in sandbox environment safely."
        ),
    )

    agents["TestRunner"] = Agent(name="TestRunner")

    agents["RollbackAgent"] = CodeWriterAgent(
        name="RollbackAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert at analyzing code, determining rollback necessity. Assess test failures, integration issues, "
            "code quality. Decide if reverting to previous working version appropriate. Generate rollback decisions, "
            "restoration instructions."
        ),
    )

    agents["CommandGenerator"] = CodeWriterAgent(
        name="CommandGenerator",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert at generating shell commands (zsh/bash) for macOS. Generate safe, executable commands: "
            "package installation, tests, environment setup. Commands must be safe, appropriate."
        ),
    )

    agents["CommandExecutor"] = Agent(name="CommandExecutor")

    agents["OfflineModelAgent"] = CodeWriterAgent(
        name="OfflineModelAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert at integrating offline/local AI models (Ollama, LM Studio, local LLM servers). Generate "
            "code for local model integration with OpenAI fallback if local models unavailable."
        ),
    )

    agents["IterationAgent"] = Agent(name="IterationAgent")

    agents["ValidationAgent"] = CodeWriterAgent(
        name="ValidationAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert at validating code correctness. Test code, identify bugs, trigger fixes. Run actual tests, "
            "validate functionality."
        ),
    )

    agents["IdeationAgent"] = CodeWriterAgent(
        name="IdeationAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert startup architect, product designer. Break high-level ideas into concrete technical components, "
            "files, implementation tasks. Identify what needs building: backend, frontend, APIs, agents, handlers. "
            "Determine technologies. Provide detailed component descriptions. Consider architecture, user flow, "
            "data handling, integration points. Generate comprehensive, actionable build task specifications."
        ),
    )

    agents["FrontendTestAgent"] = CodeWriterAgent(
        name="FrontendTestAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert frontend testing engineer. Test HTML, CSS, JavaScript for correctness. Access to tools: "
            "test_html_file(), test_javascript_file(), test_css_file(). Analyze test results, identify issues, "
            "generate fixes. Know browser compatibility, DOM structure, CSS syntax, JavaScript best practices. "
            "Tests fail: provide clear, actionable fixes. Iterate until frontend tests pass."
        ),
    )

    agents["BackendTestAgent"] = CodeWriterAgent(
        name="BackendTestAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert backend testing engineer. Test Python code: syntax, imports, runtime errors. Access to tools: "
            "test_python_file(). Analyze test results, identify issues: imports, logic errors, syntax problems, "
            "runtime exceptions. Generate fixes passing tests. Know Python best practices, error handling, proper "
            "code structure. Iterate until backend tests pass."
        ),
    )

    agents["IntegrationTestAgent"] = CodeWriterAgent(
        name="IntegrationTestAgent",
        message_bus=bus,
        system_prompt=apply_core_directive(
            "Expert integration testing engineer. Verify frontend and backend components work together. Check "
            "API endpoints, data flow, request/response formats, error handling, edge cases. Identify integration "
            "issues between components, suggest fixes. Ensure entire system works as cohesive whole."
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


