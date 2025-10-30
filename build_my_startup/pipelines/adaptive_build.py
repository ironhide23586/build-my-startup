"""
Adaptive Build Pipeline - Automatically infers build tasks from high-level descriptions.

This pipeline uses AI agents to:
1. Take a high-level startup/product description
2. Break it down into concrete build tasks
3. Execute the standard build pipeline with generated tasks
"""
import asyncio
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from .standard_build import StandardBuildPipeline, BuildConfig
from ..message_bus import MessageBus
from ..agent import Message
from ..agents_registry import create_default_agents, register_agents, start_agents, stop_agents
from ..workflow_utils import TaskTracker, wait_for_completion
from ..progress import ProgressSpinner, print_step, print_status, print_phase


@dataclass
class AdaptiveBuildConfig(BuildConfig):
    """Extended configuration for adaptive builds."""
    ideation_timeout: float = 60.0
    min_files: int = 2
    max_files: int = 10


class AdaptiveBuildPipeline:
    """Pipeline that automatically generates build tasks from high-level descriptions."""
    
    def __init__(self, config: AdaptiveBuildConfig):
        self.config = config
        self.bus = MessageBus()
        self.agents = create_default_agents(self.bus)
        self.tracker = TaskTracker()
        
        # Storage for ideation phase
        self.inferred_tasks: List[Dict] = []
        self.project_analysis: str = ""
        
        # Setup
        print("🔧 Registering agents...", flush=True)
        register_agents(self.bus, self.agents)
        print("▶️  Starting agents...", flush=True)
        start_agents(self.agents)
        print("🔌 Setting up handlers...", flush=True)
        self._setup_handlers()
        print("✅ Adaptive pipeline initialized\n", flush=True)
    
    def _setup_handlers(self):
        """Setup handlers for ideation phase."""
        self.agents["IdeationAgent"].message_handler = self._ideation_handler
    
    async def _ideation_handler(self, message: Message):
        """Handle build task inference from high-level description."""
        print(f"📨 IdeationAgent received message: {message.message_type}", flush=True)
        if message.message_type == "infer_tasks_request":
            ideation_agent = self.agents["IdeationAgent"]
            print("🧠 IdeationAgent processing request...", flush=True)
            
            description = message.content.get("description")
            target_platform = message.content.get("target_platform", "macOS")
            tech_preferences = message.content.get("tech_preferences", {})
            task_id = message.content.get("task_id")
            
            # Generate comprehensive build task specification
            ideation_prompt = f"""Analyze this startup/product idea and break it down into concrete build tasks:

PRODUCT DESCRIPTION:
{description}

TARGET PLATFORM: {target_platform}
TECH PREFERENCES: {json.dumps(tech_preferences, indent=2)}

Your task is to generate a JSON array of build tasks. Each task should specify:
1. The file to create (with path if in subdirectory like templates/ or static/)
2. A detailed description of what the file should contain and its requirements
3. How it integrates with other components

Consider:
- What backend files are needed? (Flask/FastAPI app, handlers, agents, utilities)
- What frontend files are needed? (HTML templates, CSS, JavaScript)
- What agent framework components are needed? (agents extending Agent class, message handlers)
- What data handling is needed? (database, file storage, API clients)
- What external APIs or services to integrate?
- What dependencies and libraries are required?
- Error handling, validation, and testing considerations

Generate {self.config.min_files} to {self.config.max_files} files that form a complete, working MVP.

CRITICAL: Return ONLY a valid JSON array in this exact format:
```json
[
  {{
    "task": "app.py",
    "description": "Detailed requirements for the main Flask application...",
    "priority": 1,
    "type": "backend"
  }},
  {{
    "task": "templates/index.html",
    "description": "Detailed requirements for the main HTML template...",
    "priority": 2,
    "type": "frontend"
  }}
]
```

Return ONLY the JSON array, no other text."""

            print("🧠 IdeationAgent analyzing your startup idea...", flush=True)
            print("🔄 Calling OpenAI API (this takes 10-30 seconds)...", flush=True)
            
            response = await ideation_agent.generate_response(ideation_prompt)
            
            print("✅ Got response from OpenAI", flush=True)
            print("📝 Parsing component list...", flush=True)
            
            # Extract JSON from response
            tasks = self._parse_task_response(response)
            
            if tasks:
                self.inferred_tasks = tasks
                self.project_analysis = response
                print(f"\n✅ IdeationAgent identified {len(tasks)} components to build:", flush=True)
                for i, task in enumerate(tasks, 1):
                    task_name = task.get('task', 'unknown')
                    task_type = task.get('type', 'unknown')
                    print(f"   {i}. {task_name} ({task_type})", flush=True)
            else:
                print("\n⚠️  Failed to parse build tasks from IdeationAgent response", flush=True)
                print(f"Raw response preview: {response[:500]}...", flush=True)
            
            print("✅ Ideation complete, marking task done", flush=True)
            self.tracker.complete_task(task_id)
    
    def _parse_task_response(self, response: str) -> List[Dict]:
        """Parse JSON task list from AI response."""
        try:
            # Try to extract JSON array from markdown code blocks
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                tasks = json.loads(json_str)
                return tasks
            
            # Try to find JSON array directly
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                tasks = json.loads(json_str)
                return tasks
            
            return []
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error: {e}")
            # Try to salvage partial JSON
            try:
                # Find the array start and try to fix common issues
                start = response.find('[')
                end = response.rfind(']')
                if start != -1 and end != -1:
                    json_str = response[start:end+1]
                    # Remove trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    tasks = json.loads(json_str)
                    return tasks
            except:
                pass
            return []
    
    async def infer_build_tasks(
        self,
        description: str,
        target_platform: str = "macOS",
        tech_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Infer build tasks from a high-level description.
        
        Args:
            description: High-level description of what to build
            target_platform: Target platform (default: macOS)
            tech_preferences: Dict of tech preferences (e.g., {"framework": "Flask", "frontend": "vanilla_js"})
        
        Returns:
            List of build task dictionaries
        """
        if tech_preferences is None:
            tech_preferences = {}
        
        async def coordinate_ideation():
            print("⏳ Initializing IdeationAgent...", flush=True)
            await asyncio.sleep(0.5)
            
            print("📤 Sending task inference request to IdeationAgent...", flush=True)
            await self.bus.send_to_agent(
                self.agents["Coordinator"].agent_id,
                self.agents["IdeationAgent"].agent_id,
                {
                    "description": description,
                    "target_platform": target_platform,
                    "tech_preferences": tech_preferences,
                    "task_id": "infer_build_tasks"
                },
                "infer_tasks_request"
            )
            
            # Poll for results - check inferred_tasks directly
            print("🔄 Polling for inferred tasks (checking every 0.5s)...", flush=True)
            start_time = asyncio.get_event_loop().time()
            timeout = self.config.ideation_timeout
            
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if self.inferred_tasks:
                    print(f"✅ Got {len(self.inferred_tasks)} tasks after {elapsed:.1f}s!", flush=True)
                    return self.inferred_tasks
                
                if elapsed > timeout:
                    print(f"⏱️  Timeout after {timeout}s", flush=True)
                    return []
                
                # Show we're still polling
                if int(elapsed) % 5 == 0 and elapsed > 0:
                    print(f"⏳ Still waiting... ({elapsed:.0f}s elapsed)", flush=True)
                
                await asyncio.sleep(0.5)  # Poll every 0.5 seconds
        
        # Start agent message processing in background
        agent_task = asyncio.create_task(self.agents["IdeationAgent"].receive_messages())
        
        # Run coordination and get tasks
        print("🚀 Starting ideation process...", flush=True)
        try:
            tasks = await coordinate_ideation()
            print(f"✅ Returning {len(tasks)} inferred tasks", flush=True)
            return tasks
        finally:
            # Stop the agent
            self.agents["IdeationAgent"].running = False
            agent_task.cancel()
    
    async def run_adaptive_build(
        self,
        description: str,
        target_platform: str = "macOS",
        tech_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Run complete adaptive build: infer tasks then build.
        
        Args:
            description: High-level description of what to build
            target_platform: Target platform
            tech_preferences: Technology preferences
        
        Returns:
            Build result dictionary
        """
        print_phase("PHASE 1: IDEATION - Inferring Build Tasks")
        
        # Phase 1: Infer build tasks
        print("🔍 Calling infer_build_tasks...", flush=True)
        tasks = await self.infer_build_tasks(description, target_platform, tech_preferences)
        
        print(f"📋 Got {len(tasks)} tasks back from infer_build_tasks", flush=True)
        
        if not tasks:
            print("❌ No tasks were inferred!", flush=True)
            raise ValueError("Failed to infer build tasks from description")
        
        print_phase("PHASE 2: BUILD - Generating Code for Each Component")
        print_status(f"Generating {len(tasks)} components with AI agents...", "info")
        print()
        
        # Stop ideation agents
        print("🛑 Stopping ideation agents...", flush=True)
        stop_agents(self.agents)
        print("✅ Ideation agents stopped", flush=True)
        
        # Phase 2: Execute standard build with inferred tasks
        build_config = BuildConfig(
            output_dir=self.config.output_dir,
            templates_dir=self.config.templates_dir,
            static_dir=self.config.static_dir,
            max_fix_attempts=self.config.max_fix_attempts,
            max_iterations_per_file=self.config.max_iterations_per_file,
            safe_commands_allowed=self.config.safe_commands_allowed,
            timeout=self.config.timeout,
            poll_interval=self.config.poll_interval,
            show_progress=self.config.show_progress,
            generate_plan=self.config.generate_plan
        )
        
        pipeline = StandardBuildPipeline(build_config)
        result = await pipeline.run_build(tasks, description)
        
        # Add ideation info to result
        result['inferred_tasks'] = tasks
        result['project_analysis'] = self.project_analysis
        
        return result


async def run_adaptive_build(
    description: str,
    output_dir: str,
    target_platform: str = "macOS",
    tech_preferences: Optional[Dict] = None,
    **config_kwargs
) -> Dict:
    """
    Run adaptive build from high-level description.
    
    Args:
        description: High-level startup/product description
        output_dir: Directory to save generated files
        target_platform: Target platform (default: macOS)
        tech_preferences: Technology preferences
        **config_kwargs: Additional configuration options
    
    Returns:
        Dict with keys: saved, generated, tests, plan, inferred_tasks, project_analysis
    """
    config = AdaptiveBuildConfig(output_dir=output_dir, **config_kwargs)
    pipeline = AdaptiveBuildPipeline(config)
    return await pipeline.run_adaptive_build(description, target_platform, tech_preferences)


def build_adaptive_sync(
    description: str,
    output_dir: str,
    target_platform: str = "macOS",
    tech_preferences: Optional[Dict] = None,
    **config_kwargs
) -> Dict:
    """Synchronous facade for adaptive build."""
    return asyncio.run(run_adaptive_build(description, output_dir, target_platform, tech_preferences, **config_kwargs))

