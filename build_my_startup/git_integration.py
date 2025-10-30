"""
Git integration for tracking agent-generated code changes.
Creates local repos and commits after each successful file generation.
Uses AI agents to generate meaningful commit messages.
"""
import subprocess
import os
from datetime import datetime
from typing import Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_agent import AIAgent


class GitManager:
    """Manages git operations for agent-generated code."""
    
    def __init__(self, repo_path: str, ai_agent: Optional['AIAgent'] = None):
        self.repo_path = repo_path
        self.initialized = False
        self.ai_agent = ai_agent  # AI agent for generating commit messages
        self.use_ai_messages = ai_agent is not None
    
    def init_repo(self) -> bool:
        """Initialize a git repository if it doesn't exist."""
        git_dir = os.path.join(self.repo_path, '.git')
        
        if os.path.exists(git_dir):
            self.initialized = True
            return True
        
        try:
            # Initialize repo
            subprocess.run(
                ['git', 'init'],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            
            # Create .gitignore
            gitignore_path = os.path.join(self.repo_path, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w') as f:
                    f.write("__pycache__/\n")
                    f.write("*.pyc\n")
                    f.write("*.pyo\n")
                    f.write(".DS_Store\n")
                    f.write("venv/\n")
                    f.write("*.log\n")
            
            # Initial commit
            subprocess.run(
                ['git', 'add', '.gitignore'],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ['git', 'commit', '-m', 'Initial commit - AI agent framework initialized'],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            
            self.initialized = True
            print(f"✅ Git repository initialized at {self.repo_path}", flush=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git init failed: {e}", flush=True)
            return False
    
    async def _generate_ai_commit_message(
        self,
        file_path: str,
        agent_name: str,
        action: str,
        metadata: Optional[Dict] = None,
        code_preview: Optional[str] = None
    ) -> str:
        """Use AI to generate a meaningful commit message."""
        if not self.use_ai_messages or not self.ai_agent:
            return self._generate_default_message(file_path, agent_name, action, metadata)
        
        # Get file diff if available
        diff = self.get_diff(file_path)
        if not diff and code_preview:
            diff = f"New file:\n{code_preview[:500]}"
        
        prompt = f"""Generate a concise, professional git commit message for this change.

File: {file_path}
Agent: {agent_name}
Action: {action}
"""
        
        if metadata:
            prompt += f"\nContext:\n"
            for key, value in metadata.items():
                if key in ['test_passed', 'review_rating', 'fix_attempt', 'iteration']:
                    prompt += f"- {key}: {value}\n"
        
        if diff:
            prompt += f"\nChanges:\n{diff[:800]}\n"
        
        prompt += """
Generate a commit message in this format:
[Agent] Brief summary (50 chars max)

Optional detailed description if needed.

Requirements:
- First line: [AgentName] action verb + what changed
- Keep first line under 50 characters
- Be specific and technical
- No fluff or unnecessary words
- Example: "[CodeWriter] Add Flask routes for image upload"
- Example: "[TestRunner] Fix import errors in commentary_agent.py"

Generate ONLY the commit message, no explanations."""
        
        try:
            ai_message = await self.ai_agent.generate_response(prompt)
            # Clean up the message
            ai_message = ai_message.strip()
            if ai_message.startswith('```'):
                # Remove markdown code blocks if present
                lines = ai_message.split('\n')
                ai_message = '\n'.join(line for line in lines if not line.startswith('```'))
                ai_message = ai_message.strip()
            
            return ai_message if ai_message else self._generate_default_message(file_path, agent_name, action, metadata)
        except Exception as e:
            print(f"⚠️  AI commit message generation failed: {e}", flush=True)
            return self._generate_default_message(file_path, agent_name, action, metadata)
    
    def _generate_default_message(
        self,
        file_path: str,
        agent_name: str,
        action: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Generate a default commit message when AI is not available."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{agent_name}] {action.capitalize()}: {file_path}\n\n"
        message += f"Timestamp: {timestamp}\n"
        message += f"Agent: {agent_name}\n"
        message += f"Action: {action}\n"
        
        if metadata:
            message += "\nMetadata:\n"
            for key, value in metadata.items():
                message += f"- {key}: {value}\n"
        
        return message
    
    async def commit_file(
        self,
        file_path: str,
        agent_name: str,
        action: str = "generated",
        metadata: Optional[Dict] = None,
        code_preview: Optional[str] = None
    ) -> bool:
        """
        Commit a single file with AI-generated message.
        
        Args:
            file_path: Path to file relative to repo root
            agent_name: Name of agent that created/modified the file
            action: Action taken (generated, fixed, improved, reviewed)
            metadata: Additional context (test_results, review_feedback, etc.)
            code_preview: Preview of code for new files
        """
        if not self.initialized:
            if not self.init_repo():
                return False
        
        try:
            # Add the file
            subprocess.run(
                ['git', 'add', file_path],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            
            # Generate commit message (AI or default)
            if self.use_ai_messages:
                print(f"🤖 AI generating commit message for {file_path}...", flush=True)
                message = await self._generate_ai_commit_message(
                    file_path, agent_name, action, metadata, code_preview
                )
            else:
                message = self._generate_default_message(file_path, agent_name, action, metadata)
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            
            # Show first line of commit message
            first_line = message.split('\n')[0]
            print(f"📝 Committed: {first_line}", flush=True)
            return True
            
        except subprocess.CalledProcessError as e:
            # File might not have changes
            if "nothing to commit" in str(e.stderr):
                return True
            print(f"⚠️  Git commit failed for {file_path}: {e}", flush=True)
            return False
    
    async def commit_multiple(
        self,
        files: list,
        agent_name: str,
        action: str,
        summary: Optional[str] = None
    ) -> bool:
        """Commit multiple files at once with AI-generated message."""
        if not self.initialized:
            if not self.init_repo():
                return False
        
        try:
            # Add all files
            for file_path in files:
                subprocess.run(
                    ['git', 'add', file_path],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=True
                )
            
            # Generate message
            if self.use_ai_messages and self.ai_agent:
                print(f"🤖 AI generating batch commit message for {len(files)} files...", flush=True)
                
                prompt = f"""Generate a concise git commit message for a batch commit.

Agent: {agent_name}
Action: {action}
Files ({len(files)}): {', '.join(files[:5])}{'...' if len(files) > 5 else ''}
"""
                if summary:
                    prompt += f"\nSummary: {summary}\n"
                
                prompt += """
Generate a commit message in format:
[Agent] Brief summary of batch change

Optional details about the changes.

Requirements:
- First line under 72 characters
- Be specific about what the batch accomplishes
- Example: "[BuildPipeline] Complete MVP - 8 files generated and tested"
- Example: "[CodeWriter] Add all frontend components (HTML, CSS, JS)"

Generate ONLY the commit message."""
                
                try:
                    message = await self.ai_agent.generate_response(prompt)
                    message = message.strip()
                    if message.startswith('```'):
                        lines = message.split('\n')
                        message = '\n'.join(line for line in lines if not line.startswith('```')).strip()
                except:
                    message = f"[{agent_name}] {action}: {len(files)} files\n\nBatch commit by AI agent"
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"[{agent_name}] {action}: {len(files)} files\n\nTimestamp: {timestamp}"
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            
            first_line = message.split('\n')[0]
            print(f"📝 Batch committed: {first_line}", flush=True)
            return True
            
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in str(e.stderr):
                return True
            print(f"⚠️  Git batch commit failed: {e}", flush=True)
            return False
    
    def get_history(self, file_path: Optional[str] = None, limit: int = 10) -> list:
        """Get commit history for a file or entire repo."""
        if not self.initialized:
            return []
        
        try:
            cmd = ['git', 'log', f'--max-count={limit}', '--pretty=format:%h|%an|%s|%ad', '--date=short']
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            history = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        history.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'message': parts[2],
                            'date': parts[3]
                        })
            
            return history
            
        except subprocess.CalledProcessError:
            return []
    
    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch for experimental changes."""
        if not self.initialized:
            return False
        
        try:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            print(f"🌿 Created branch: {branch_name}", flush=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Branch creation failed: {e}", flush=True)
            return False
    
    def get_diff(self, file_path: str) -> str:
        """Get diff for a file."""
        if not self.initialized:
            return ""
        
        try:
            result = subprocess.run(
                ['git', 'diff', 'HEAD', file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""


def ensure_git_available() -> bool:
    """Check if git is available on the system."""
    try:
        subprocess.run(
            ['git', '--version'],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

