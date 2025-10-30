"""
Enhanced testing utilities for frontend and backend code.
Provides iterative debugging capabilities.
"""
import os
import subprocess
import json
from typing import Dict, List, Optional, Tuple


def test_python_file(file_path: str, sandbox_dir: str, timeout: int = 30) -> Dict:
    """
    Test a Python file with multiple validation strategies.
    
    Returns:
        Dict with keys: passed, syntax_valid, imports_valid, runs_without_error, output, errors
    """
    result = {
        "passed": False,
        "syntax_valid": False,
        "imports_valid": False,
        "runs_without_error": False,
        "output": "",
        "errors": "",
        "fixes_needed": []
    }
    
    # 1. Check syntax
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        result["syntax_valid"] = True
    except SyntaxError as e:
        result["errors"] += f"Syntax Error: {e}\n"
        result["fixes_needed"].append("fix_syntax")
        return result
    
    # 2. Check imports
    try:
        proc = subprocess.run(
            ['python', '-c', f'import py_compile; py_compile.compile("{file_path}", doraise=True)'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode == 0:
            result["imports_valid"] = True
        else:
            result["errors"] += f"Import/Compilation Error: {proc.stderr}\n"
            result["fixes_needed"].append("fix_imports")
            return result
    except subprocess.TimeoutExpired:
        result["errors"] += "Import check timed out\n"
        return result
    
    # 3. Try to run (if it's not just a library module)
    if '__name__' in code and '__main__' in code:
        try:
            proc = subprocess.run(
                ['python', file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=sandbox_dir
            )
            result["output"] = proc.stdout
            result["errors"] += proc.stderr
            result["runs_without_error"] = proc.returncode == 0
        except subprocess.TimeoutExpired:
            result["errors"] += "Execution timed out\n"
            result["fixes_needed"].append("optimize_performance")
    else:
        # It's a library module, just check if it imports
        result["runs_without_error"] = result["imports_valid"]
    
    result["passed"] = result["syntax_valid"] and result["imports_valid"]
    return result


def test_html_file(file_path: str) -> Dict:
    """
    Test an HTML file for validity.
    
    Returns:
        Dict with keys: passed, valid_html, has_required_structure, errors, fixes_needed
    """
    result = {
        "passed": False,
        "valid_html": False,
        "has_required_structure": False,
        "errors": "",
        "fixes_needed": []
    }
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic HTML validation
        required = ['<html', '</html>', '<head', '</head>', '<body', '</body>']
        missing = [tag for tag in required if tag not in content.lower()]
        
        if missing:
            result["errors"] = f"Missing required HTML tags: {', '.join(missing)}\n"
            result["fixes_needed"].append("add_missing_html_structure")
        else:
            result["has_required_structure"] = True
        
        # Check for common issues
        if '<script>' in content and '</script>' not in content:
            result["errors"] += "Unclosed <script> tag\n"
            result["fixes_needed"].append("close_script_tags")
        
        if content.count('<') != content.count('>'):
            result["errors"] += "Mismatched HTML tags\n"
            result["fixes_needed"].append("balance_html_tags")
        
        result["valid_html"] = result["has_required_structure"] and not result["errors"]
        result["passed"] = result["valid_html"]
        
    except Exception as e:
        result["errors"] = f"Error reading HTML: {e}\n"
    
    return result


def test_javascript_file(file_path: str) -> Dict:
    """
    Test a JavaScript file for basic validity.
    
    Returns:
        Dict with keys: passed, syntax_valid, errors, fixes_needed
    """
    result = {
        "passed": False,
        "syntax_valid": False,
        "errors": "",
        "fixes_needed": []
    }
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for common syntax issues
        issues = []
        
        # Unclosed brackets/parens
        if content.count('{') != content.count('}'):
            issues.append("Mismatched curly braces")
            result["fixes_needed"].append("balance_braces")
        
        if content.count('(') != content.count(')'):
            issues.append("Mismatched parentheses")
            result["fixes_needed"].append("balance_parentheses")
        
        if content.count('[') != content.count(']'):
            issues.append("Mismatched square brackets")
            result["fixes_needed"].append("balance_brackets")
        
        if issues:
            result["errors"] = "; ".join(issues)
        else:
            result["syntax_valid"] = True
            result["passed"] = True
        
    except Exception as e:
        result["errors"] = f"Error reading JavaScript: {e}\n"
    
    return result


def test_css_file(file_path: str) -> Dict:
    """
    Test a CSS file for basic validity.
    
    Returns:
        Dict with keys: passed, syntax_valid, errors, fixes_needed
    """
    result = {
        "passed": False,
        "syntax_valid": False,
        "errors": "",
        "fixes_needed": []
    }
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for common syntax issues
        issues = []
        
        if content.count('{') != content.count('}'):
            issues.append("Mismatched curly braces")
            result["fixes_needed"].append("balance_css_braces")
        
        # Check for unclosed property values
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if ':' in line and ';' not in line and '{' not in line and '}' not in line:
                if line.strip() and not line.strip().startswith('/*'):
                    issues.append(f"Line {i+1}: Missing semicolon")
                    result["fixes_needed"].append("add_semicolons")
                    break
        
        if issues:
            result["errors"] = "; ".join(issues)
        else:
            result["syntax_valid"] = True
            result["passed"] = True
        
    except Exception as e:
        result["errors"] = f"Error reading CSS: {e}\n"
    
    return result


def test_file_by_type(file_path: str, sandbox_dir: str) -> Dict:
    """
    Route to appropriate test function based on file type.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.py':
        return test_python_file(file_path, sandbox_dir)
    elif ext in ['.html', '.htm']:
        return test_html_file(file_path)
    elif ext == '.js':
        return test_javascript_file(file_path)
    elif ext == '.css':
        return test_css_file(file_path)
    elif ext in ['.json', '.txt', '.md']:
        # These don't need special testing
        return {"passed": True, "errors": "", "fixes_needed": []}
    else:
        return {"passed": True, "errors": "Unknown file type, skipping tests", "fixes_needed": []}


def generate_fix_prompt(file_path: str, test_result: Dict, original_code: str) -> str:
    """
    Generate a detailed fix prompt based on test results.
    """
    _, ext = os.path.splitext(file_path)
    file_type = ext[1:].upper() if ext else "file"
    
    prompt = f"""Fix the {file_type} file '{file_path}' based on test failures.

CRITICAL: Generate ONLY the corrected {file_type} code, NO explanations or markdown.

Test Results:
"""
    
    if not test_result.get("syntax_valid", True):
        prompt += f"❌ Syntax errors found\n"
    
    if not test_result.get("imports_valid", True):
        prompt += f"❌ Import/compilation errors\n"
    
    if not test_result.get("runs_without_error", True):
        prompt += f"❌ Runtime errors\n"
    
    if test_result.get("errors"):
        prompt += f"\nError Details:\n{test_result['errors'][:500]}\n"
    
    if test_result.get("fixes_needed"):
        prompt += f"\nFixes Needed:\n"
        for fix in test_result["fixes_needed"]:
            prompt += f"- {fix.replace('_', ' ').title()}\n"
    
    prompt += f"\nOriginal Code Preview:\n```\n{original_code[:1000]}\n```\n"
    prompt += f"\nGenerate the complete, corrected {file_type} code that fixes all issues."
    
    return prompt

