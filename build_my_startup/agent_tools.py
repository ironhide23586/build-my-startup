"""
Tools and capabilities that agents can use to test, debug, and validate code.
Agents are given access to these tools with full context.
"""
import os
import json
from typing import Dict, List, Optional, Callable
from .testing_utils import (
    test_python_file,
    test_html_file,
    test_javascript_file,
    test_css_file,
    test_file_by_type,
    generate_fix_prompt
)


# Tool registry that agents can access
AGENT_TOOLS: Dict[str, Callable] = {}


def register_tool(name: str, func: Callable, description: str):
    """Register a tool that agents can use."""
    AGENT_TOOLS[name] = {
        "function": func,
        "description": description,
        "name": name
    }


def get_tools_documentation() -> str:
    """Get documentation for all available tools."""
    docs = "# Available Tools for AI Agents\n\n"
    docs += "You have access to the following testing and debugging tools:\n\n"
    
    for name, tool_info in AGENT_TOOLS.items():
        docs += f"## {name}\n"
        docs += f"{tool_info['description']}\n\n"
    
    return docs


# Register testing tools
register_tool(
    "test_python_file",
    test_python_file,
    """Test a Python file for syntax, imports, and runtime errors.
    
    Usage: test_python_file(file_path, sandbox_dir, timeout=30)
    
    Returns dict with:
    - passed: bool
    - syntax_valid: bool
    - imports_valid: bool
    - runs_without_error: bool
    - output: str
    - errors: str
    - fixes_needed: List[str]
    
    Use this to validate Python backend code."""
)

register_tool(
    "test_html_file",
    test_html_file,
    """Test an HTML file for valid structure and tags.
    
    Usage: test_html_file(file_path)
    
    Returns dict with:
    - passed: bool
    - valid_html: bool
    - has_required_structure: bool
    - errors: str
    - fixes_needed: List[str]
    
    Use this to validate HTML frontend files."""
)

register_tool(
    "test_javascript_file",
    test_javascript_file,
    """Test a JavaScript file for syntax errors.
    
    Usage: test_javascript_file(file_path)
    
    Returns dict with:
    - passed: bool
    - syntax_valid: bool
    - errors: str
    - fixes_needed: List[str]
    
    Use this to validate JavaScript frontend code."""
)

register_tool(
    "test_css_file",
    test_css_file,
    """Test a CSS file for syntax errors.
    
    Usage: test_css_file(file_path)
    
    Returns dict with:
    - passed: bool
    - syntax_valid: bool
    - errors: str
    - fixes_needed: List[str]
    
    Use this to validate CSS styling files."""
)


def create_agent_context(file_path: str, file_type: str, sandbox_dir: str) -> str:
    """Create context for agents about what tools they can use."""
    
    context = f"""# Testing Context for {file_path}

File Type: {file_type}
Sandbox Directory: {sandbox_dir}

## Your Capabilities

You are an AI agent with access to testing tools. Your job is to:
1. Test the file using appropriate tools
2. Identify issues and bugs
3. Generate fixes if tests fail
4. Iterate until tests pass

## Available Testing Tools

"""
    
    if file_type == "python":
        context += """### test_python_file(file_path, sandbox_dir)
Tests Python files for:
- Syntax errors
- Import errors
- Runtime errors
- Proper execution

Returns detailed test results with fixes_needed list.
"""
    
    elif file_type == "html":
        context += """### test_html_file(file_path)
Tests HTML files for:
- Valid HTML structure
- Required tags (html, head, body)
- Unclosed tags
- Proper nesting

Returns validation results with fixes_needed list.
"""
    
    elif file_type == "javascript":
        context += """### test_javascript_file(file_path)
Tests JavaScript files for:
- Syntax errors
- Bracket/brace matching
- Parentheses matching

Returns syntax validation with fixes_needed list.
"""
    
    elif file_type == "css":
        context += """### test_css_file(file_path)
Tests CSS files for:
- Syntax errors
- Brace matching
- Missing semicolons
- Proper structure

Returns validation results with fixes_needed list.
"""
    
    context += """
## Testing Workflow

1. Run the appropriate test function
2. Examine the results
3. If passed: Great! Move on.
4. If failed: 
   - Review the 'errors' field
   - Check 'fixes_needed' list
   - Generate corrected code
   - Test again

## Your Approach

Be methodical:
- Test thoroughly
- Read error messages carefully
- Fix one issue at a time if possible
- Verify fixes work
- Iterate until success

You have up to 3 fix attempts. Use them wisely.
"""
    
    return context


def create_test_execution_prompt(
    file_path: str,
    file_type: str,
    code: str,
    sandbox_dir: str,
    previous_results: Optional[Dict] = None
) -> str:
    """Create a prompt for agents to execute tests."""
    
    prompt = f"""# Test Execution Task

File: {file_path}
Type: {file_type}

## Code to Test

```{file_type}
{code[:1500]}
{'... (truncated)' if len(code) > 1500 else ''}
```

## Your Task

1. Analyze the code above
2. Identify potential issues
3. Predict what might fail
4. Recommend test strategy

"""
    
    if previous_results:
        prompt += f"""
## Previous Test Results

The code was tested before with these results:
- Passed: {previous_results.get('passed', False)}
- Errors: {previous_results.get('errors', 'None')[:500]}
- Fixes Needed: {', '.join(previous_results.get('fixes_needed', []))}

Based on these results, generate an improved version of the code.
"""
    
    prompt += """
## Response Format

Provide your analysis in this format:

**Predicted Issues:**
- [List potential problems]

**Testing Strategy:**
- [What to test first]
- [What edge cases to check]

**Expected Result:**
- [What you expect to happen]

Then, if this is a fix iteration, provide the corrected code.
"""
    
    return prompt

