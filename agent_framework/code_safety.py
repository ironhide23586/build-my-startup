from typing import List, Tuple


DEFAULT_BANNED_SNIPPETS: List[str] = [
    "import os",  # allowed in general but risky with execs; checked below for specific calls
    "import subprocess",
    "from subprocess import",
    "os.system(",
    "subprocess.run(",
    "subprocess.Popen(",
    "import shlex",
    "import socket",
    "import paramiko",
    "shutil.rmtree(",
    "open('/etc",
    "open(\"/etc",
    "import ctypes",
    "ctypes.CDLL(",
    "eval(",
    "exec(",
]


def is_safe_code(filename: str, code: str, extra_banned: List[str] | None = None) -> Tuple[bool, List[str]]:
    """Heuristic scan for dangerous code patterns in generated content.

    Returns (is_safe, violations)
    """
    if not code:
        return True, []
    violations: List[str] = []
    banned = set(DEFAULT_BANNED_SNIPPETS)
    if extra_banned:
        banned.update(extra_banned)
    lower = code.lower()
    for snippet in banned:
        if snippet.lower() in lower:
            violations.append(f"found '{snippet}'")

    # Very simple guard on writing files outside working tree
    if "open(" in code and ("/tmp/" in lower or ".." in code):
        violations.append("suspicious file access (open with /tmp or parent traversal)")

    # Networking ban for app code
    if filename.endswith('.py') and any(x in lower for x in ["requests.", "httpx.", "urllib."]):
        violations.append("networking libraries used in app code")

    return (len(violations) == 0), violations


