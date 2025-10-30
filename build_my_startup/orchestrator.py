import asyncio
from typing import Dict, Any, Optional

from .message_bus import MessageBus
from .agents_registry import create_default_agents, register_agents, start_agents, stop_agents
from .workflow_utils import TaskTracker, wait_for_completion
from .context_store import ContextStore


class MVPOrchestrator:
    """High-level entry point: takes an MVP specification (string) and runs the build."""

    def __init__(self):
        self.bus = MessageBus()
        self.agents = create_default_agents(self.bus)
        register_agents(self.bus, self.agents)
        start_agents(self.agents)
        self.tracker = TaskTracker()
        self.context = ContextStore()

        # Default namespaces and ACLs
        coord_id = self.agents["Coordinator"].agent_id
        planner_id = self.agents["PlannerAgent"].agent_id
        writer_id = self.agents["CodeWriter"].agent_id
        reviewer_id = self.agents["CodeReviewer"].agent_id
        testgen_id = self.agents["TestGenerator"].agent_id
        testrun_id = self.agents["TestRunner"].agent_id

        self.context.create_namespace("planning", readers={coord_id, planner_id}, writers={planner_id})
        self.context.create_namespace("build_tasks", readers={coord_id, planner_id, writer_id, reviewer_id, testgen_id}, writers={planner_id})
        self.context.create_namespace("artifacts", readers=set(self.agents[a].agent_id for a in self.agents), writers={writer_id})

    async def plan_from_spec(self, mvp_spec: str, output_dir: str) -> bool:
        planner = self.agents["PlannerAgent"]
        coordinator = self.agents["Coordinator"]
        task_id = "generate_plan"
        self.tracker.create_task(task_id)

        plan_prompt = f"""Generate a comprehensive markdown plan for this MVP:

{mvp_spec}

Return ONLY markdown. Include objectives, agent assignments, timeline, locations (output_dir: {output_dir}), methodology and workflow."""

        await self.bus.send_to_agent(
            coordinator.agent_id,
            planner.agent_id,
            {
                "project_description": mvp_spec[:2000],
                "build_tasks": [],
                "agents_info": {},
                "output_dir": output_dir,
                "task_id": task_id,
            },
            "generate_plan_request",
        )

        ok = await wait_for_completion([planner], self.tracker, [task_id], timeout=60.0, poll_interval=0.5)
        return ok

    def stop(self) -> None:
        stop_agents(self.agents)


async def run_from_spec(mvp_spec: str, output_dir: str) -> Dict[str, Any]:
    orch = MVPOrchestrator()
    try:
        planned = await orch.plan_from_spec(mvp_spec, output_dir)
        return {"planned": planned}
    finally:
        orch.stop()


