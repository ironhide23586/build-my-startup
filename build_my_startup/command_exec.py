import os
import subprocess
from typing import Dict


DANGEROUS_PATTERNS = [
    "rm -rf /", "sudo rm", "format", "dd if=",
    "mkfs", "fdisk", ":(){ :|:& };:", "> /dev/sd", "shutdown", "reboot"
]


def execute_command_safe(command: str, cwd: str, allow_dangerous: bool = False, timeout: int = 60) -> Dict:
    result = {
        "command": command,
        "success": False,
        "output": "",
        "error": "",
        "return_code": None,
    }

    if not allow_dangerous:
        lower = command.lower()
        if any(p in lower for p in DANGEROUS_PATTERNS):
            result["error"] = "Dangerous command blocked for safety"
            return result

    shell = "/bin/zsh" if os.path.exists("/bin/zsh") else "/bin/bash"
    try:
        proc = subprocess.run(
            command,
            shell=True,
            executable=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        result["output"] = proc.stdout
        result["error"] = proc.stderr
        result["return_code"] = proc.returncode
        result["success"] = proc.returncode == 0
        return result
    except subprocess.TimeoutExpired:
        result["error"] = f"Command execution timeout (>{timeout}s)"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


