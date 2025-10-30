import asyncio
import os
import tempfile
import time
import shutil
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from ..message_bus import MessageBus
from ..agent import Message
from ..agents_registry import create_default_agents, register_agents, start_agents, stop_agents
from ..workflow_utils import TaskTracker, wait_for_completion
from ..code_extraction import extract_file_content
from ..sandbox import prepend_test_setup, run_python
from ..command_exec import execute_command_safe
from ..code_safety import is_safe_code
from ..pretty_print import print_code, print_review, print_status
from ..progress import ProgressSpinner, print_step


@dataclass
class BuildConfig:
    """Configuration for the standard build pipeline."""
    output_dir: str
    max_fix_attempts: int = 3
    max_iterations_per_file: int = 5
    safe_commands_allowed: bool = True
    timeout: float = 300.0
    poll_interval: float = 1.0
    show_progress: bool = True
    generate_plan: bool = True
    templates_dir: Optional[str] = None
    static_dir: Optional[str] = None
    
    def __post_init__(self):
        if self.templates_dir is None:
            self.templates_dir = os.path.join(self.output_dir, "templates")
        if self.static_dir is None:
            self.static_dir = os.path.join(self.output_dir, "static")


class StandardBuildPipeline:
    """A comprehensive build pipeline with all standard agent handlers."""
    
    def __init__(self, config: BuildConfig):
        self.config = config
        self.bus = MessageBus()
        self.agents = create_default_agents(self.bus)
        self.tracker = TaskTracker()
        
        # Storage
        self.generated_files: Dict[str, str] = {}
        self.test_files: Dict[str, str] = {}
        self.test_results: Dict[str, Dict] = {}
        self.file_versions: Dict[str, List[Dict]] = {}
        self.task_states: Dict[str, Dict] = {}
        self.command_history: List[Dict] = []
        self.plan_output: Dict[str, any] = {"plan": "", "ready": False}
        
        # Sandbox
        self.sandbox_dir = tempfile.mkdtemp(prefix="build_sandbox_")
        
        # Setup
        self._setup_directories()
        self._setup_agents()
    
    def _setup_directories(self):
        """Create necessary directories."""
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.templates_dir, exist_ok=True)
        os.makedirs(self.config.static_dir, exist_ok=True)
    
    def _setup_agents(self):
        """Register and start all agents."""
        register_agents(self.bus, self.agents)
        start_agents(self.agents)
        
        # Attach handlers
        self.agents["CodeWriter"].message_handler = self._enhanced_writer_handler
        self.agents["CodeReviewer"].message_handler = self._reviewer_handler
        self.agents["TestGenerator"].message_handler = self._test_generator_handler
        self.agents["TestRunner"].message_handler = self._test_runner_handler
        self.agents["RollbackAgent"].message_handler = self._rollback_handler
        self.agents["CommandGenerator"].message_handler = self._command_generator_handler
        self.agents["CommandExecutor"].message_handler = self._command_executor_handler
        self.agents["PlannerAgent"].message_handler = self._planner_handler
        self.agents["OfflineModelAgent"].message_handler = self._offline_model_handler
        self.agents["IterationAgent"].message_handler = self._iteration_handler
        self.agents["ValidationAgent"].message_handler = self._validation_handler
    
    def save_version(self, task_name: str, code: str, test_result=None) -> int:
        """Save a version of code for potential rollback."""
        if task_name not in self.file_versions:
            self.file_versions[task_name] = []
        version_num = len(self.file_versions[task_name])
        self.file_versions[task_name].append({
            "version": version_num,
            "code": code,
            "timestamp": time.time(),
            "test_result": test_result
        })
        return version_num
    
    async def get_task_state(self, task_name: str) -> Dict:
        """Get or create task state with lock."""
        if task_name not in self.task_states:
            self.task_states[task_name] = {
                "state": "init",
                "fix_count": 0,
                "lock": asyncio.Lock()
            }
        return self.task_states[task_name]
    
    # ==================== AGENT HANDLERS ====================
    
    async def _enhanced_writer_handler(self, message: Message):
        """Handle code generation, fixes, and improvements."""
        writer = self.agents["CodeWriter"]
        reviewer = self.agents["CodeReviewer"]
        
        if message.message_type == "code_request":
            task = message.content.get("task")
            description = message.content.get("description", task)
            task_id = f"code_gen_{task}"
            
            state_info = await self.get_task_state(task)
            async with state_info["lock"]:
                if state_info["state"] in ["generating", "reviewing", "testing"]:
                    return
                state_info["state"] = "generating"
            
            self.tracker.create_task(task_id)
            
            enhanced_description = f"""{description}

CRITICAL FORMATTING REQUIREMENTS:
- Generate ONLY the code file content, NO explanations, NO markdown
- Do NOT wrap code in ```python blocks
- Start directly with imports if Python file, or <!DOCTYPE if HTML
- Do NOT include "Here is..." or "Here's..." introductions
- Return ONLY the raw code that would go directly into the file
- The code must be complete, executable, and ready to save

Output ONLY the file contents."""
            
            print_step(f"🤖 Generating code for: {task}", substep=True)
            with ProgressSpinner(f"Writing {task}"):
                code = await writer.write_code(enhanced_description)
            
            # Pretty print the generated code
            print_status(f"\n✨ Generated code for: {task}", "success")
            language = "python" if task.endswith(".py") else "html" if task.endswith(".html") else "javascript"
            print_code(code, language=language, title=f"📄 {task}")
            
            safe, violations = is_safe_code(task, code)
            if not safe:
                fix_task_id = f"fix_safety_{task}"
                self.tracker.create_task(fix_task_id)
                desc = (
                    f"The generated file '{task}' contains unsafe patterns: {violations}.\n"
                    f"Rewrite the file to remove dangerous calls and use safe alternatives. Return ONLY the corrected code."
                )
                asyncio.create_task(self.bus.send_to_agent(
                    writer.agent_id,
                    writer.agent_id,
                    {"file": task, "task_id": fix_task_id, "description": desc},
                    "improve_code_request"
                ))
                return
            
            self.generated_files[task] = code
            self.save_version(task, code)
            
            state_info = await self.get_task_state(task)
            async with state_info["lock"]:
                state_info["state"] = "reviewing"
            
            self.tracker.complete_task(task_id)
            
            review_task_id = f"review_{task}"
            self.tracker.create_task(review_task_id)
            asyncio.create_task(self.bus.send_to_agent(
                writer.agent_id,
                reviewer.agent_id,
                {"file": task, "code": code, "task_id": review_task_id, "is_fix": False},
                "review_request"
            ))
        
        elif message.message_type == "improve_code_request":
            file_task = message.content.get("file")
            description = message.content.get("description", "")
            iteration = message.content.get("iteration", 1)
            improve_task_id = message.content.get("task_id")
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                if state_info["state"] == "done":
                    state_info["state"] = "improving"
            
            improved_code = await writer.write_code(description)
            self.generated_files[file_task] = improved_code
            self.save_version(file_task, improved_code)
            
            # Pretty print the improved code
            print_status(f"\n🔧 Code improved for: {file_task} (iteration {iteration})", "success")
            language = "python" if file_task.endswith(".py") else "html" if file_task.endswith(".html") else "javascript"
            print_code(improved_code, language=language, title=f"✨ Improved: {file_task}")
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                state_info["state"] = "reviewing"
            
            self.tracker.complete_task(improve_task_id)
            
            review_task_id = f"review_{file_task}_iter_{iteration}"
            self.tracker.create_task(review_task_id)
            asyncio.create_task(self.bus.send_to_agent(
                writer.agent_id,
                reviewer.agent_id,
                {"file": file_task, "code": improved_code, "task_id": review_task_id, "is_fix": True},
                "review_request"
            ))
        
        elif message.message_type == "fix_code_request":
            file_task = message.content.get("file")
            test_result = message.content.get("test_result")
            original_code = message.content.get("original_code")
            fix_task_id = message.content.get("task_id")
            fix_count = message.content.get("fix_count", 0)
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                if state_info["state"] != "fixing":
                    self.tracker.complete_task(fix_task_id)
                    return
                state_info["state"] = "generating"
            
            fix_description = f"""Fix the code in '{file_task}' based on test failures (fix attempt {fix_count}).

Original code:
```python
{original_code[:2000]}
```

Test failure details:
{test_result.get('errors', 'N/A')[:500]}

Test output:
{test_result.get('output', 'N/A')[:500]}

Fix the code to make tests pass and ensure proper integration."""
            
            fixed_code = await writer.write_code(fix_description)
            self.generated_files[file_task] = fixed_code
            self.save_version(file_task, fixed_code)
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                state_info["state"] = "reviewing"
            
            self.tracker.complete_task(fix_task_id)
            
            review_task_id = f"review_{file_task}_fix_{fix_count}"
            self.tracker.create_task(review_task_id)
            asyncio.create_task(self.bus.send_to_agent(
                writer.agent_id,
                reviewer.agent_id,
                {"file": file_task, "code": fixed_code, "task_id": review_task_id, "is_fix": True},
                "review_request"
            ))
    
    async def _reviewer_handler(self, message: Message):
        """Handle code review."""
        reviewer = self.agents["CodeReviewer"]
        writer = self.agents["CodeWriter"]
        test_generator = self.agents["TestGenerator"]
        
        if message.message_type == "review_request":
            file_task = message.content.get("file")
            code = message.content.get("code")
            review_task_id = message.content.get("task_id", f"review_{file_task}")
            is_fix = message.content.get("is_fix", False)
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                if state_info["state"] not in ["reviewing", "generating"] and not is_fix:
                    return
                if not is_fix:
                    state_info["state"] = "reviewing"
            
            print_step(f"🔍 Reviewing code for: {file_task}", substep=True)
            with ProgressSpinner(f"Reviewing {file_task}"):
                review = await reviewer.review_code(code, writer.agent_id)
            
            # Pretty print the code review
            print_status(f"\n📝 Code review completed for: {file_task}", "info")
            print_review(review, title=f"🔍 Review: {file_task}")
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                state_info["state"] = "testing"
            
            self.tracker.complete_task(review_task_id)
            
            # Request test generation
            if review_task_id.startswith("review_"):
                test_task_id = f"test_gen_{file_task}"
                self.tracker.create_task(test_task_id)
                asyncio.create_task(self.bus.send_to_agent(
                    reviewer.agent_id,
                    test_generator.agent_id,
                    {
                        "file": file_task,
                        "code": code,
                        "review": review,
                        "task_id": test_task_id,
                        "sandbox_dir": self.sandbox_dir,
                        "output_dir": self.config.output_dir,
                        "is_fix": is_fix
                    },
                    "generate_test_request"
                ))
    
    async def _test_generator_handler(self, message: Message):
        """Generate test code."""
        if message.message_type == "generate_test_request":
            test_generator = self.agents["TestGenerator"]
            test_runner = self.agents["TestRunner"]
            
            file_task = message.content.get("file")
            code = message.content.get("code")
            review = message.content.get("review", "")
            test_task_id = message.content.get("task_id")
            
            test_description = f"""Generate comprehensive test code for the file '{file_task}'.
            
Requirements:
- Test functionality, integration, and alignment with project requirements
- Test should run safely in a sandbox environment
- Test should validate proper code integration
- Test should check imports, dependencies, and compatibility
- Test code should be executable standalone
- Include error handling and validation

The code being tested:
```python
{code[:1000]}
```

Code Review feedback:
{review[:500]}

Generate complete test code ready to execute."""
            
            print_step(f"🧪 Generating tests for: {file_task}", substep=True)
            with ProgressSpinner(f"Creating tests for {file_task}"):
                test_code = await test_generator.write_code(test_description)
            self.test_files[file_task] = test_code
            self.tracker.complete_task(test_task_id)
            
            run_task_id = f"test_run_{file_task}"
            self.tracker.create_task(run_task_id)
            await self.bus.send_to_agent(
                test_generator.agent_id,
                test_runner.agent_id,
                {
                    "file": file_task,
                    "test_code": test_code,
                    "task_id": run_task_id,
                    "sandbox_dir": self.sandbox_dir,
                    "output_dir": self.config.output_dir
                },
                "run_test_request"
            )
    
    async def _test_runner_handler(self, message: Message):
        """Execute tests in sandbox."""
        if message.message_type == "run_test_request":
            test_runner = self.agents["TestRunner"]
            writer = self.agents["CodeWriter"]
            rollback_agent = self.agents["RollbackAgent"]
            
            file_task = message.content.get("file")
            test_code = message.content.get("test_code")
            run_task_id = message.content.get("task_id")
            
            result = {
                "file": file_task,
                "passed": False,
                "output": "",
                "errors": ""
            }
            
            try:
                actual_test_code = test_code
                if "```" in test_code:
                    actual_test_code, _ = extract_file_content("test.py", test_code)
                
                test_file_path = os.path.join(self.sandbox_dir, f"test_{file_task.replace('/', '_')}.py")
                with open(test_file_path, 'w') as f:
                    f.write(actual_test_code)
                
                src_path = os.path.join(self.config.output_dir, file_task)
                if os.path.exists(src_path):
                    shutil.copy(
                        src_path,
                        os.path.join(self.sandbox_dir, os.path.basename(file_task))
                    )
                
                prepend_test_setup(test_file_path, self.config.output_dir, self.sandbox_dir)
                print_step(f"▶️  Running tests for: {file_task}", substep=True)
                with ProgressSpinner(f"Testing {file_task}"):
                    rc, out, err = run_python(test_file_path, self.sandbox_dir, timeout=30)
                result["output"] = out
                result["errors"] = err
                result["passed"] = rc == 0
                
                # Pretty print test result
                if result["passed"]:
                    print_status(f"\n✅ Tests PASSED for: {file_task}", "success")
                else:
                    print_status(f"\n❌ Tests FAILED for: {file_task}", "error")
                    if result["errors"]:
                        print_code(result["errors"], language="text", title=f"Test Errors: {file_task}")
                
            except Exception as e:
                result["errors"] = str(e)
                print_status(f"\n⚠️  Test execution error for: {file_task}", "warning")
            
            self.test_results[file_task] = result
            self.tracker.complete_task(run_task_id)
            
            current_code = self.generated_files.get(file_task, "")
            self.save_version(file_task, current_code, test_result=result)
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                if result["passed"]:
                    state_info["state"] = "done"
                else:
                    if state_info["fix_count"] >= self.config.max_fix_attempts:
                        state_info["state"] = "rollback_assessment"
                        
                        rollback_task_id = f"rollback_assess_{file_task}"
                        self.tracker.create_task(rollback_task_id)
                        asyncio.create_task(self.bus.send_to_agent(
                            test_runner.agent_id,
                            rollback_agent.agent_id,
                            {
                                "file": file_task,
                                "test_result": result,
                                "versions": self.file_versions.get(file_task, []),
                                "fix_count": state_info["fix_count"],
                                "task_id": rollback_task_id
                            },
                            "rollback_assessment_request"
                        ))
                    else:
                        state_info["state"] = "fixing"
                        state_info["fix_count"] += 1
            
            state_info = await self.get_task_state(file_task)
            async with state_info["lock"]:
                should_fix = not result["passed"] and state_info["fix_count"] < self.config.max_fix_attempts and state_info["state"] == "fixing"
            
            if should_fix:
                fix_task_id = f"fix_{file_task}_{state_info['fix_count']}"
                self.tracker.create_task(fix_task_id)
                asyncio.create_task(self.bus.send_to_agent(
                    test_runner.agent_id,
                    writer.agent_id,
                    {
                        "file": file_task,
                        "test_result": result,
                        "original_code": self.generated_files.get(file_task, ""),
                        "task_id": fix_task_id,
                        "fix_count": state_info["fix_count"]
                    },
                    "fix_code_request"
                ))
    
    async def _rollback_handler(self, message: Message):
        """Handle rollback assessment and execution."""
        if message.message_type == "rollback_assessment_request":
            rollback_agent = self.agents["RollbackAgent"]
            reviewer = self.agents["CodeReviewer"]
            
            file_task = message.content.get("file")
            test_result = message.content.get("test_result")
            versions = message.content.get("versions", [])
            fix_count = message.content.get("fix_count", 0)
            rollback_task_id = message.content.get("task_id")
            
            last_working_version = None
            for version in reversed(versions):
                test_res = version.get("test_result")
                if test_res and test_res.get("passed"):
                    last_working_version = version
                    break
            
            assessment_prompt = f"""Assess whether a rollback is needed for the file '{file_task}'.

Current situation:
- Fix attempts exhausted: {fix_count} attempts made
- Test failure: {test_result.get('errors', 'N/A')[:300]}
- Available versions: {len(versions)} saved versions

Question: Should we rollback to a previous working version?

Generate your assessment and recommendation."""
            
            assessment = await rollback_agent.generate_response(assessment_prompt)
            should_rollback = last_working_version is not None and ("rollback" in assessment.lower() or "revert" in assessment.lower())
            
            self.tracker.complete_task(rollback_task_id)
            
            if should_rollback and last_working_version:
                rollback_exec_task_id = f"rollback_exec_{file_task}"
                self.tracker.create_task(rollback_exec_task_id)
                
                restored_code = last_working_version["code"]
                self.generated_files[file_task] = restored_code
                self.save_version(file_task, restored_code, test_result={"passed": True, "rollback": True})
                
                state_info = await self.get_task_state(file_task)
                async with state_info["lock"]:
                    state_info["state"] = "rolled_back"
                    state_info["fix_count"] = 0
                
                self.tracker.complete_task(rollback_exec_task_id)
            else:
                state_info = await self.get_task_state(file_task)
                async with state_info["lock"]:
                    state_info["state"] = "done"
    
    async def _command_generator_handler(self, message: Message):
        """Generate shell commands using AI."""
        if message.message_type == "generate_command_request":
            command_generator = self.agents["CommandGenerator"]
            command_executor = self.agents["CommandExecutor"]
            
            task_description = message.content.get("task_description")
            context = message.content.get("context", "")
            cmd_task_id = message.content.get("task_id")
            working_dir = message.content.get("working_dir", self.config.output_dir)
            
            command_prompt = f"""Generate a shell command (zsh/bash compatible for macOS) to accomplish this task:

Task: {task_description}
Context: {context}
Working directory: {working_dir}

Requirements:
- Command should be safe and appropriate for macOS
- Use zsh/bash compatible syntax
- Consider the working directory when generating relative paths
- Avoid destructive operations unless explicitly requested
- Return ONLY the command(s) without explanation

Generate the shell command(s) needed."""
            
            ai_response = await command_generator.generate_response(command_prompt)
            
            command = ai_response.strip()
            if "```" in command:
                command, _ = extract_file_content("command.sh", command)
            
            self.tracker.complete_task(cmd_task_id)
            
            exec_task_id = f"cmd_exec_{cmd_task_id}"
            self.tracker.create_task(exec_task_id)
            asyncio.create_task(self.bus.send_to_agent(
                command_generator.agent_id,
                command_executor.agent_id,
                {
                    "command": command,
                    "task_description": task_description,
                    "working_dir": working_dir,
                    "task_id": exec_task_id,
                    "context": context
                },
                "execute_command_request"
            ))
    
    async def _command_executor_handler(self, message: Message):
        """Safely execute shell commands."""
        if message.message_type == "execute_command_request":
            command = message.content.get("command")
            working_dir = message.content.get("working_dir", self.config.output_dir)
            exec_task_id = message.content.get("task_id")
            task_description = message.content.get("task_description", "")
            
            result = {
                "command": command,
                "success": False,
                "output": "",
                "error": "",
                "return_code": None
            }
            
            try:
                dangerous_patterns = [
                    "rm -rf /", "sudo rm", "format", "dd if=",
                    "mkfs", "fdisk", ":(){ :|:& };:",
                    "> /dev/sd", "shutdown", "reboot"
                ]
                
                is_dangerous = any(pattern in command.lower() for pattern in dangerous_patterns)
                
                if is_dangerous and not self.config.safe_commands_allowed:
                    result["error"] = "Dangerous command blocked for safety"
                else:
                    exec_res = execute_command_safe(
                        command,
                        cwd=working_dir,
                        allow_dangerous=self.config.safe_commands_allowed,
                        timeout=60
                    )
                    result.update(exec_res)
            except Exception as e:
                result["error"] = str(e)
            
            self.command_history.append({
                "command": command,
                "result": result,
                "timestamp": time.time(),
                "task": task_description
            })
            
            self.tracker.complete_task(exec_task_id)
    
    async def _planner_handler(self, message: Message):
        """Generate comprehensive project plans."""
        if message.message_type == "generate_plan_request":
            planner = self.agents["PlannerAgent"]
            
            project_description = message.content.get("project_description")
            build_tasks = message.content.get("build_tasks", [])
            plan_task_id = message.content.get("task_id")
            
            plan_prompt = f"""Generate a comprehensive project plan in markdown format for building: {project_description}

Build Tasks:
{chr(10).join([f"- {t.get('task', 'unknown')}: {t.get('description', '')[:200]}..." for t in build_tasks])}

Generate a detailed markdown plan with these sections:
## Objectives
## Agent Assignments
## Timeline
## Locations
## Methodology
## Workflow
## Risk Mitigation

Generate the complete plan in markdown format."""
            
            plan_content = await planner.generate_response(plan_prompt)
            plan_md, _ = extract_file_content("PLAN.md", plan_content)
            
            self.plan_output["plan"] = plan_md
            self.plan_output["ready"] = True
            
            plan_file = os.path.join(self.config.output_dir, "BUILD_PLAN.md")
            try:
                with open(plan_file, "w", encoding="utf-8") as f:
                    f.write(plan_md)
            except Exception:
                pass
            
            self.tracker.complete_task(plan_task_id)
    
    async def _offline_model_handler(self, message: Message):
        """Integrate offline AI model support."""
        if message.message_type == "integrate_offline_models":
            # Placeholder for future offline model integration
            integration_task_id = message.content.get("task_id")
            self.tracker.complete_task(integration_task_id)
    
    async def _iteration_handler(self, message: Message):
        """Handle iteration requests for continuous improvement."""
        if message.message_type == "iterate_request":
            iteration_agent = self.agents["IterationAgent"]
            writer = self.agents["CodeWriter"]
            
            file_task = message.content.get("file")
            test_result = message.content.get("test_result")
            iteration = message.content.get("iteration", 1)
            iterate_task_id = message.content.get("task_id")
            
            improve_task_id = f"improve_{file_task}_iter_{iteration}"
            self.tracker.create_task(improve_task_id)
            
            asyncio.create_task(self.bus.send_to_agent(
                iteration_agent.agent_id,
                writer.agent_id,
                {
                    "file": file_task,
                    "code": self.generated_files.get(file_task, ""),
                    "test_result": test_result,
                    "iteration": iteration,
                    "task_id": improve_task_id,
                    "description": f"Improve {file_task} based on test failure (iteration {iteration}). Fix: {test_result.get('errors', 'N/A')[:300]}"
                },
                "improve_code_request"
            ))
            
            self.tracker.complete_task(iterate_task_id)
    
    async def _validation_handler(self, message: Message):
        """Validate code and trigger fixes if needed."""
        if message.message_type == "validate_code_request":
            validation_agent = self.agents["ValidationAgent"]
            writer = self.agents["CodeWriter"]
            
            file_task = message.content.get("file")
            code = message.content.get("code", "")
            task_id = message.content.get("task_id")
            
            validation_errors = []
            
            try:
                import ast
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    validation_errors.append(f"Syntax error: {e}")
            except Exception as e:
                validation_errors.append(f"Validation error: {e}")
            
            self.tracker.complete_task(task_id)
            
            if validation_errors:
                fix_prompt = f"""Fix the code in {file_task} based on these validation errors:

Errors:
{chr(10).join(f"- {e}" for e in validation_errors)}

Current code:
```python
{code[:1500]}
```

Generate a comprehensive fix description."""
                
                fix_description = await validation_agent.generate_response(fix_prompt)
                fix_task_id = f"fix_validation_{file_task}"
                self.tracker.create_task(fix_task_id)
                
                enhanced_fix_desc = f"Fix {file_task}:\n\nValidation Errors:\n{chr(10).join(f'- {e}' for e in validation_errors)}\n\nAI Fix Strategy:\n{fix_description[:800]}"
                
                asyncio.create_task(self.bus.send_to_agent(
                    validation_agent.agent_id,
                    writer.agent_id,
                    {
                        "file": file_task,
                        "code": code,
                        "validation_errors": validation_errors,
                        "task_id": fix_task_id,
                        "description": enhanced_fix_desc
                    },
                    "improve_code_request"
                ))
    
    # ==================== BUILD EXECUTION ====================
    
    async def run_build(self, build_tasks: List[Dict], project_description: str = "") -> Dict:
        """Execute the complete build pipeline."""
        # Start message processing
        agent_tasks = [agent.receive_messages() for agent in self.agents.values()]
        message_processing = asyncio.gather(*agent_tasks)
        
        async def coordinate():
            await asyncio.sleep(1)  # Let agents initialize
            
            # Generate plan if requested
            if self.config.generate_plan:
                plan_task_id = "generate_plan"
                self.tracker.create_task(plan_task_id)
                await self.bus.send_to_agent(
                    self.agents["Coordinator"].agent_id,
                    self.agents["PlannerAgent"].agent_id,
                    {
                        "project_description": project_description,
                        "build_tasks": build_tasks,
                        "output_dir": self.config.output_dir,
                        "task_id": plan_task_id
                    },
                    "generate_plan_request"
                )
                await wait_for_completion(
                    [self.agents["PlannerAgent"]],
                    self.tracker,
                    [plan_task_id],
                    timeout=30.0,
                    poll_interval=0.5,
                    show_progress=False
                )
            
            # Request code generation
            print(f"\n🚀 Building {len(build_tasks)} components...\n")
            for idx, task_info in enumerate(build_tasks, 1):
                task_name = task_info.get("task", "unknown")
                print(f"\n📦 Component {idx}/{len(build_tasks)}: {task_name}")
                print("─" * 50)
                await self.bus.send_to_agent(
                    self.agents["Coordinator"].agent_id,
                    self.agents["CodeWriter"].agent_id,
                    task_info,
                    "code_request"
                )
                await asyncio.sleep(3)
            
            # Wait for completion
            all_task_ids = []
            for task_info in build_tasks:
                task_name = task_info["task"]
                all_task_ids.extend([
                    f"code_gen_{task_name}",
                    f"review_{task_name}",
                    f"test_gen_{task_name}",
                    f"test_run_{task_name}"
                ])
            
            await wait_for_completion(
                list(self.agents.values()),
                self.tracker,
                all_task_ids,
                timeout=self.config.timeout,
                poll_interval=self.config.poll_interval,
                show_progress=self.config.show_progress
            )
            
            # Stop agents
            stop_agents(self.agents)
            
            # Save files
            saved_count = 0
            os.makedirs(self.config.templates_dir, exist_ok=True)
            os.makedirs(self.config.static_dir, exist_ok=True)
            
            for task_name, code in self.generated_files.items():
                file_path = os.path.join(self.config.output_dir, task_name)
                cleaned, _ = extract_file_content(task_name, code)
                code = cleaned
                
                safe, violations = is_safe_code(task_name, code)
                if not safe:
                    continue
                
                file_dir = os.path.dirname(file_path)
                if file_dir and file_dir != self.config.output_dir:
                    os.makedirs(file_dir, exist_ok=True)
                
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    saved_count += 1
                except Exception:
                    pass
            
            # Cleanup
            try:
                shutil.rmtree(self.sandbox_dir)
            except Exception:
                pass
            
            return {
                "saved": saved_count,
                "generated": len(self.generated_files),
                "tests": self.test_results,
                "plan": self.plan_output.get("plan", ""),
                "command_history": self.command_history
            }
        
        try:
            result = await asyncio.gather(message_processing, coordinate(), return_exceptions=True)
            return result[1] if len(result) > 1 else {}
        except Exception as e:
            stop_agents(self.agents)
            raise


async def run_standard_build(build_tasks: List[Dict], output_dir: str, project_description: str = "", **config_kwargs) -> Dict:
    """Run the standard multi-agent build for given tasks into output_dir.
    
    Args:
        build_tasks: list of {"task": filename, "description": text}
        output_dir: directory to save generated files
        project_description: optional description for plan generation
        **config_kwargs: additional configuration options (max_fix_attempts, timeout, etc.)
    
    Returns:
        Dict with keys: saved, generated, tests, plan, command_history
    """
    config = BuildConfig(output_dir=output_dir, **config_kwargs)
    pipeline = StandardBuildPipeline(config)
    return await pipeline.run_build(build_tasks, project_description)


def build_standard_sync(build_tasks: List[Dict], output_dir: str, project_description: str = "", **config_kwargs) -> Dict:
    """Synchronous facade that runs the standard build pipeline."""
    return asyncio.run(run_standard_build(build_tasks, output_dir, project_description, **config_kwargs))


