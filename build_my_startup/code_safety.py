from typing import List, Tuple


def is_bypass_enabled() -> bool:
    """Check if safety bypass is enabled in config."""
    try:
        from .config_manager import get_config
        return get_config("safety.bypass_all_safety_checks", False)
    except:
        return False


DEFAULT_BANNED_SNIPPETS: List[str] = [
    # Only block actually dangerous patterns, not normal Python
    "os.system(",
    "subprocess.run(",
    "subprocess.Popen(",
    "subprocess.call(",
    "shutil.rmtree('/",  # Block absolute path deletes only
    "open('/etc",
    "open(\"/etc",
    "ctypes.CDLL(",
    "eval(",
    "exec(",
    "rm -rf /",  # Block in shell commands
    "__import__(",
]


def is_safe_code(filename: str, code: str, extra_banned: List[str] | None = None) -> Tuple[bool, List[str]]:
    """Heuristic scan for dangerous code patterns in generated content.

    Returns (is_safe, violations)
    """
    # Check bypass flag first
    if is_bypass_enabled():
        return True, []
    
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

    # Guard against dangerous file writes only (not normal file operations)
    if "open(" in code and ("open('/etc" in lower or "open(\"/etc" in lower):
        violations.append("suspicious system file access")

    # Allow networking libraries - they're needed for APIs!
    # No longer blocking requests, urllib, etc.

    return (len(violations) == 0), violations


