import os
import subprocess
import sys
from typing import Tuple


def prepend_test_setup(test_path: str, output_dir: str, sandbox_dir: str) -> None:
    setup_code = f"""
import sys
import os
sys.path.insert(0, '{os.path.dirname(output_dir)}')
sys.path.insert(0, '{output_dir}')
sys.path.insert(0, '{sandbox_dir}')
"""
    with open(test_path, 'r') as f:
        original = f.read()
    with open(test_path, 'w') as f:
        f.write(setup_code + original)


def run_python(path: str, cwd: str, timeout: int = 30) -> Tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, path],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )
    return proc.returncode, proc.stdout, proc.stderr


