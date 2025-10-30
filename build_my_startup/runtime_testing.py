"""
Runtime Testing - Actually execute applications to catch real errors.

Tests that static analysis misses.
"""
import subprocess
import os
import signal
import time
from typing import Dict, Tuple


def test_cli_app_execution(
    app_file: str,
    working_dir: str,
    test_inputs: list = None,
    timeout: int = 5
) -> Tuple[bool, str, str]:
    """
    Test CLI app by running it with test inputs.
    
    Returns: (success, stdout, stderr)
    """
    test_inputs = test_inputs or ['exit\n']
    input_str = '\n'.join(test_inputs)
    
    try:
        proc = subprocess.Popen(
            ['python', app_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
            text=True
        )
        
        stdout, stderr = proc.communicate(input=input_str, timeout=timeout)
        
        success = proc.returncode == 0 or proc.returncode is None
        return success, stdout, stderr
        
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "", "Process timed out"
    except Exception as e:
        return False, "", str(e)


def test_flask_app_startup(
    app_file: str,
    working_dir: str,
    timeout: int = 3
) -> Tuple[bool, str]:
    """
    Test Flask app can start without errors.
    
    Returns: (can_start, error_message)
    """
    try:
        # Try to import and check for syntax errors
        proc = subprocess.Popen(
            ['python', '-c', f'import sys; sys.path.insert(0, "{working_dir}"); import {app_file.replace(".py", "")}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir
        )
        
        stdout, stderr = proc.communicate(timeout=timeout)
        
        if proc.returncode != 0:
            return False, stderr
        
        return True, ""
        
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "Import timeout"
    except Exception as e:
        return False, str(e)


def validate_data_file_at_runtime(file_path: str) -> Tuple[bool, str]:
    """
    Validate data files by trying to load them.
    
    Returns: (is_valid, error_message)
    """
    ext = file_path.split('.')[-1].lower()
    
    try:
        if ext == 'json':
            import json
            with open(file_path, 'r') as f:
                json.load(f)
            return True, ""
        
        elif ext == 'csv':
            import csv
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                list(reader)
            return True, ""
        
        elif ext == 'yaml' or ext == 'yml':
            try:
                import yaml
                with open(file_path, 'r') as f:
                    yaml.safe_load(f)
                return True, ""
            except ImportError:
                return True, "yaml not installed, skipping validation"
        
        else:
            return True, ""
    
    except Exception as e:
        return False, str(e)


def smart_runtime_test(file_path: str, working_dir: str) -> Dict:
    """
    Smart runtime testing based on file type.
    
    Returns structured test result.
    """
    filename = os.path.basename(file_path)
    ext = filename.split('.')[-1].lower()
    
    result = {
        "tested": False,
        "passed": False,
        "runtime_errors": [],
        "can_execute": False
    }
    
    # Data files
    if ext in ['json', 'csv', 'yaml', 'yml']:
        is_valid, error = validate_data_file_at_runtime(file_path)
        result["tested"] = True
        result["passed"] = is_valid
        if error:
            result["runtime_errors"].append(error)
        return result
    
    # Python files
    if ext == 'py':
        # Check if it's a Flask app
        with open(file_path, 'r') as f:
            content = f.read()
        
        if 'Flask' in content or 'flask' in content:
            can_start, error = test_flask_app_startup(filename, working_dir)
            result["tested"] = True
            result["can_execute"] = can_start
            result["passed"] = can_start
            if error:
                result["runtime_errors"].append(error)
        
        # Check if it has CLI main()
        elif 'if __name__' in content and 'main()' in content:
            success, stdout, stderr = test_cli_app_execution(filename, working_dir)
            result["tested"] = True
            result["can_execute"] = success
            result["passed"] = success
            if stderr:
                result["runtime_errors"].append(stderr)
        
        else:
            # Library module - just check imports
            can_start, error = test_flask_app_startup(filename, working_dir)
            result["tested"] = True
            result["passed"] = can_start
            if error:
                result["runtime_errors"].append(error)
        
        return result
    
    # Other files don't need runtime testing
    result["tested"] = False
    result["passed"] = True
    return result

