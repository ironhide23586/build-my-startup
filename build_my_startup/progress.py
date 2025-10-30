"""
Progress indicators for build pipelines.
Provides visual feedback so users know the system is working.
Thread-safe and async-safe.
"""
import sys
import time
import threading
import asyncio
from typing import Optional

# Global lock for thread-safe printing
_print_lock = threading.Lock()


class ProgressSpinner:
    """Animated spinner for long-running operations."""
    
    def __init__(self, message: str = "Working"):
        self.message = message
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.frame_idx = 0
    
    def start(self):
        """Start the spinner animation."""
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def _spin(self):
        """Run the spinner loop."""
        while self.running:
            with _print_lock:
                frame = self.frames[self.frame_idx % len(self.frames)]
                sys.stdout.write(f"\r{frame} {self.message}...")
                sys.stdout.flush()
            self.frame_idx += 1
            time.sleep(0.1)
    
    def stop(self, final_message: Optional[str] = None):
        """Stop the spinner."""
        self.running = False
        if self.thread:
            self.thread.join()
        with _print_lock:
            if final_message:
                sys.stdout.write(f"\r{final_message}\n")
            else:
                sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
            sys.stdout.flush()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()


class ProgressTracker:
    """Track progress through multiple steps."""
    
    def __init__(self, total_steps: int, description: str = "Progress"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.step_names = []
    
    def update(self, step_name: str, status: str = "in_progress"):
        """Update progress with current step."""
        self.current_step += 1
        self.step_names.append(step_name)
        
        # Progress bar
        filled = int(30 * self.current_step / self.total_steps)
        bar = "█" * filled + "░" * (30 - filled)
        percent = int(100 * self.current_step / self.total_steps)
        
        # Status icon
        icons = {
            "in_progress": "🔄",
            "success": "✅",
            "error": "❌",
            "skip": "⏭️"
        }
        icon = icons.get(status, "🔄")
        
        sys.stdout.write(f"\r{icon} [{bar}] {percent}% - {step_name}")
        sys.stdout.flush()
        
        if status in ["success", "error", "skip"]:
            print()  # New line after completion
    
    def complete(self, message: str = "Complete!"):
        """Mark progress as complete."""
        bar = "█" * 30
        print(f"\r✅ [{bar}] 100% - {message}")


def print_step(step: str, substep: bool = False):
    """Print a step with nice formatting. Thread-safe."""
    with _print_lock:
        prefix = "   └─" if substep else "▶"
        print(f"{prefix} {step}", flush=True)


def print_status(message: str, status: str = "info"):
    """Print a status message with icon. Thread-safe."""
    with _print_lock:
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "working": "🔄"
        }
        icon = icons.get(status, "ℹ️")
        print(f"{icon} {message}", flush=True)


def print_phase(phase_name: str):
    """Print a major phase header. Thread-safe."""
    with _print_lock:
        print("\n" + "─" * 70)
        print(f"📍 {phase_name}")
        print("─" * 70, flush=True)

