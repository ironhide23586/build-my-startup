"""
File Type Validator - Ensures generated content matches file type.

Prevents issues like Python code in .json files.
"""
import json
from typing import Tuple, Dict, Any


def validate_file_content(filename: str, content: str) -> Tuple[bool, str, list]:
    """
    Validate that file content matches its type.
    
    Returns: (is_valid, corrected_content, issues)
    """
    ext = filename.split('.')[-1].lower()
    issues = []
    
    if ext == 'json':
        return validate_json_file(content)
    elif ext == 'py':
        return validate_python_file(content)
    elif ext in ['html', 'htm']:
        return validate_html_file(content)
    elif ext == 'css':
        return validate_css_file(content)
    elif ext == 'js':
        return validate_javascript_file(content)
    elif ext in ['md', 'txt']:
        return True, content, []
    else:
        return True, content, []


def validate_json_file(content: str) -> Tuple[bool, str, list]:
    """Ensure JSON file contains valid JSON data, not code."""
    issues = []
    
    # Check if content looks like Python code
    if 'import ' in content or 'def ' in content or 'class ' in content:
        issues.append("JSON file contains Python code instead of JSON data")
        # Try to extract JSON or return empty structure
        try:
            # Maybe it's wrapped in code block
            if '```json' in content:
                start = content.index('```json') + 7
                end = content.index('```', start)
                json_content = content[start:end].strip()
                json.loads(json_content)
                return True, json_content, ["Extracted JSON from code block"]
        except:
            pass
        
        # Default to empty array for data files
        return False, '[]', issues
    
    # Validate JSON syntax
    try:
        json.loads(content)
        return True, content, []
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON syntax: {e}")
        return False, '[]', issues


def validate_python_file(content: str) -> Tuple[bool, str, list]:
    """Ensure Python file contains code, not data."""
    issues = []
    
    # Check if it's just JSON data
    try:
        json.loads(content.strip())
        issues.append("Python file contains JSON data instead of code")
        return False, content, issues
    except:
        pass
    
    # Check for basic Python syntax
    try:
        compile(content, '<string>', 'exec')
        return True, content, []
    except SyntaxError as e:
        issues.append(f"Python syntax error: {e}")
        return False, content, issues


def validate_html_file(content: str) -> Tuple[bool, str, list]:
    """Ensure HTML file contains markup, not code."""
    issues = []
    
    if not any(tag in content.lower() for tag in ['<html', '<head', '<body', '<!doctype']):
        issues.append("HTML file missing basic structure")
        return False, content, issues
    
    return True, content, []


def validate_css_file(content: str) -> Tuple[bool, str, list]:
    """Ensure CSS file contains styles, not code."""
    issues = []
    
    # Check if looks like Python/JS code
    if 'import ' in content or 'def ' in content or 'function ' in content:
        issues.append("CSS file contains code instead of styles")
        return False, content, issues
    
    return True, content, []


def validate_javascript_file(content: str) -> Tuple[bool, str, list]:
    """Ensure JavaScript file contains JS code."""
    issues = []
    
    # Check if it's Python code
    if 'import ' in content and 'def ' in content:
        issues.append("JavaScript file contains Python code")
        return False, content, issues
    
    return True, content, []


def get_file_type_instructions(filename: str) -> str:
    """Get instructions for what content type should be generated."""
    ext = filename.split('.')[-1].lower()
    
    instructions = {
        'json': """
CRITICAL: This is a JSON DATA file.
- Generate ONLY valid JSON data (array [] or object {})
- NO Python code, NO imports, NO functions
- Example: [] or {"key": "value"}
- Start with [ or {
- Must be parseable by json.loads()
""",
        'py': """
CRITICAL: This is a PYTHON CODE file.
- Generate Python code with imports, classes, functions
- NO raw JSON data
- Start with imports or class/def
- Must be valid Python syntax
""",
        'html': """
CRITICAL: This is an HTML MARKUP file.
- Generate HTML with <!DOCTYPE html>, <html>, <head>, <body>
- NO Python code, NO JavaScript files (inline JS is ok)
- Valid HTML5 structure
""",
        'css': """
CRITICAL: This is a CSS STYLESHEET file.
- Generate CSS rules with selectors and properties
- NO Python code, NO JavaScript code
- Valid CSS syntax with braces and semicolons
""",
        'js': """
CRITICAL: This is a JAVASCRIPT CODE file.
- Generate JavaScript code (ES6+ ok)
- NO Python code
- Valid JavaScript syntax
""",
        'md': """
Generate Markdown documentation.
Use proper markdown syntax.
""",
        'txt': """
Generate plain text content.
"""
    }
    
    return instructions.get(ext, "")

