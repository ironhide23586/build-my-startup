"""
Failure Recovery System - Handle build failures gracefully and recover.

Capabilities:
- Checkpoint saves after each successful file
- Rollback to last working state
- Retry failed operations
- Save partial builds
- Resume from interruption
"""
import json
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Checkpoint:
    """Checkpoint state for recovery."""
    timestamp: float
    files_completed: List[str]
    files_pending: List[str]
    test_results: Dict[str, Any]
    generated_files: Dict[str, str]
    current_phase: str
    metadata: Dict[str, Any]


class RecoveryManager:
    """Manages checkpoints and recovery for build processes."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.checkpoint_file = os.path.join(output_dir, ".build_checkpoint.json")
        self.checkpoints: List[Checkpoint] = []
    
    def create_checkpoint(
        self,
        files_completed: List[str],
        files_pending: List[str],
        test_results: Dict[str, Any],
        generated_files: Dict[str, str],
        current_phase: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """Create a checkpoint of current build state."""
        checkpoint = Checkpoint(
            timestamp=time.time(),
            files_completed=files_completed,
            files_pending=files_pending,
            test_results=test_results,
            generated_files=generated_files,
            current_phase=current_phase,
            metadata=metadata or {}
        )
        
        self.checkpoints.append(checkpoint)
        self._save_checkpoint(checkpoint)
        
        print(f"💾 Checkpoint created: {len(files_completed)} files complete, {len(files_pending)} pending", flush=True)
        
        return checkpoint
    
    def _save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to disk."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Save as JSON
            checkpoint_data = asdict(checkpoint)
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}", flush=True)
    
    def load_checkpoint(self) -> Optional[Checkpoint]:
        """Load the most recent checkpoint."""
        if not os.path.exists(self.checkpoint_file):
            return None
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
            
            checkpoint = Checkpoint(**data)
            print(f"📂 Loaded checkpoint: {len(checkpoint.files_completed)} files completed", flush=True)
            return checkpoint
        
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}", flush=True)
            return None
    
    def can_resume(self) -> bool:
        """Check if we can resume from a checkpoint."""
        return os.path.exists(self.checkpoint_file)
    
    def clear_checkpoint(self):
        """Clear checkpoint file after successful completion."""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                print("🗑️  Checkpoint cleared (build completed)", flush=True)
        except Exception as e:
            print(f"⚠️  Failed to clear checkpoint: {e}", flush=True)
    
    def get_recovery_summary(self) -> Dict[str, Any]:
        """Get summary of what can be recovered."""
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return {"can_recover": False}
        
        return {
            "can_recover": True,
            "files_completed": len(checkpoint.files_completed),
            "files_pending": len(checkpoint.files_pending),
            "current_phase": checkpoint.current_phase,
            "age_seconds": time.time() - checkpoint.timestamp,
            "checkpoint_file": self.checkpoint_file
        }


def retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiply delay by this each retry
        exceptions: Tuple of exceptions to catch
    """
    async def wrapper(*args, **kwargs):
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            
            except exceptions as e:
                if attempt >= max_retries - 1:
                    print(f"❌ Failed after {max_retries} attempts: {e}", flush=True)
                    raise
                
                print(f"⚠️  Attempt {attempt + 1} failed: {e}", flush=True)
                print(f"🔄 Retrying in {delay}s...", flush=True)
                
                import asyncio
                await asyncio.sleep(delay)
                delay *= backoff_factor
        
        return None
    
    return wrapper


class PartialBuildSaver:
    """Save partial builds even if full build fails."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.partial_dir = os.path.join(output_dir, ".partial_build")
    
    def save_partial(self, files: Dict[str, str], metadata: Dict[str, Any]):
        """Save partial build for inspection."""
        try:
            os.makedirs(self.partial_dir, exist_ok=True)
            
            # Save each file
            for filename, content in files.items():
                file_path = os.path.join(self.partial_dir, filename)
                file_dir = os.path.dirname(file_path)
                if file_dir:
                    os.makedirs(file_dir, exist_ok=True)
                
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Save metadata
            meta_path = os.path.join(self.partial_dir, "metadata.json")
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 Partial build saved to {self.partial_dir}", flush=True)
            print(f"   Files: {len(files)}", flush=True)
            
            return True
        
        except Exception as e:
            print(f"⚠️  Failed to save partial build: {e}", flush=True)
            return False

