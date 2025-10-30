"""
Tool System - Rigid contracts and structured tool calls for AI agents.

Agents can call tools with JSON schemas, and outputs are always structured.
"""
import json
import subprocess
import os
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class ToolCategory(Enum):
    """Categories of tools available to agents."""
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    DEPENDENCY = "dependency"
    ENVIRONMENT = "environment"
    AI_INTEGRATION = "ai_integration"
    GIT = "git"
    BUILD = "build"


@dataclass
class ToolParameter:
    """Structured parameter definition for tools."""
    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolSchema:
    """JSON schema for tool definition."""
    name: str
    category: ToolCategory
    description: str
    parameters: List[ToolParameter]
    returns: Dict[str, str]  # {field_name: description}
    examples: List[str]


@dataclass
class ToolResult:
    """Structured result from tool execution."""
    success: bool
    data: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class ToolRegistry:
    """Central registry of all tools available to agents."""
    
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
    
    def register(
        self,
        schema: ToolSchema,
        implementation: Callable
    ):
        """Register a tool with its schema and implementation."""
        self.tools[schema.name] = {
            "schema": schema,
            "implementation": implementation
        }
        self.categories[schema.category].append(schema.name)
    
    def get_tool(self, name: str) -> Optional[Dict]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get all tools in a category."""
        return self.categories.get(category, [])
    
    def get_tools_documentation(self, categories: Optional[List[ToolCategory]] = None) -> str:
        """Get formatted documentation for tools."""
        if categories is None:
            categories = list(ToolCategory)
        
        doc = "# Available Tools for AI Agents\n\n"
        doc += "You have access to structured tools with rigid JSON contracts.\n\n"
        
        for category in categories:
            tool_names = self.categories.get(category, [])
            if not tool_names:
                continue
            
            doc += f"\n## {category.value.upper()} Tools\n\n"
            
            for tool_name in tool_names:
                tool_info = self.tools.get(tool_name)
                if not tool_info:
                    continue
                
                schema = tool_info["schema"]
                doc += f"### {schema.name}\n\n"
                doc += f"{schema.description}\n\n"
                
                # Parameters
                doc += "**Parameters:**\n"
                for param in schema.parameters:
                    required_str = "required" if param.required else "optional"
                    default_str = f" (default: {param.default})" if param.default is not None else ""
                    enum_str = f" [options: {', '.join(param.enum)}]" if param.enum else ""
                    doc += f"- `{param.name}` ({param.type}, {required_str}){default_str}{enum_str}: {param.description}\n"
                
                # Returns
                doc += f"\n**Returns:**\n"
                doc += "```json\n{\n"
                for field, desc in schema.returns.items():
                    doc += f'  "{field}": "...  // {desc}"\n'
                doc += "}\n```\n\n"
                
                # Examples
                if schema.examples:
                    doc += "**Examples:**\n"
                    for example in schema.examples:
                        doc += f"```json\n{example}\n```\n"
                
                doc += "\n"
        
        return doc
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool with parameters and return structured result."""
        tool_info = self.tools.get(tool_name)
        
        if not tool_info:
            return ToolResult(
                success=False,
                data={},
                errors=[f"Tool '{tool_name}' not found"],
                warnings=[],
                metadata={"tool": tool_name}
            )
        
        schema = tool_info["schema"]
        implementation = tool_info["implementation"]
        
        # Validate required parameters
        errors = []
        for param in schema.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Missing required parameter: {param.name}")
        
        if errors:
            return ToolResult(
                success=False,
                data={},
                errors=errors,
                warnings=[],
                metadata={"tool": tool_name}
            )
        
        # Execute tool
        try:
            result = implementation(**parameters)
            
            # Ensure result is ToolResult
            if not isinstance(result, ToolResult):
                result = ToolResult(
                    success=True,
                    data=result if isinstance(result, dict) else {"result": result},
                    errors=[],
                    warnings=[],
                    metadata={"tool": tool_name}
                )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                errors=[f"Tool execution failed: {str(e)}"],
                warnings=[],
                metadata={"tool": tool_name, "exception": type(e).__name__}
            )


# Global registry instance
TOOL_REGISTRY = ToolRegistry()


# ============================================================================
# TESTING TOOLS
# ============================================================================

def test_python_backend(file_path: str, sandbox_dir: str, timeout: int = 30) -> ToolResult:
    """Test a Python backend file."""
    from .testing_utils import test_python_file
    
    result = test_python_file(file_path, sandbox_dir, timeout)
    
    return ToolResult(
        success=result.get("passed", False),
        data={
            "syntax_valid": result.get("syntax_valid", False),
            "imports_valid": result.get("imports_valid", False),
            "runs_without_error": result.get("runs_without_error", False)
        },
        errors=[result.get("errors", "")] if result.get("errors") else [],
        warnings=[],
        metadata={
            "file": file_path,
            "fixes_needed": result.get("fixes_needed", [])
        }
    )


def test_html_frontend(file_path: str) -> ToolResult:
    """Test an HTML frontend file."""
    from .testing_utils import test_html_file
    
    result = test_html_file(file_path)
    
    return ToolResult(
        success=result.get("passed", False),
        data={
            "valid_html": result.get("valid_html", False),
            "has_required_structure": result.get("has_required_structure", False)
        },
        errors=[result.get("errors", "")] if result.get("errors") else [],
        warnings=[],
        metadata={
            "file": file_path,
            "fixes_needed": result.get("fixes_needed", [])
        }
    )


def test_javascript_frontend(file_path: str) -> ToolResult:
    """Test a JavaScript frontend file."""
    from .testing_utils import test_javascript_file
    
    result = test_javascript_file(file_path)
    
    return ToolResult(
        success=result.get("passed", False),
        data={
            "syntax_valid": result.get("syntax_valid", False)
        },
        errors=[result.get("errors", "")] if result.get("errors") else [],
        warnings=[],
        metadata={
            "file": file_path,
            "fixes_needed": result.get("fixes_needed", [])
        }
    )


def test_css_frontend(file_path: str) -> ToolResult:
    """Test a CSS frontend file."""
    from .testing_utils import test_css_file
    
    result = test_css_file(file_path)
    
    return ToolResult(
        success=result.get("passed", False),
        data={
            "syntax_valid": result.get("syntax_valid", False)
        },
        errors=[result.get("errors", "")] if result.get("errors") else [],
        warnings=[],
        metadata={
            "file": file_path,
            "fixes_needed": result.get("fixes_needed", [])
        }
    )


# Register testing tools
TOOL_REGISTRY.register(
    ToolSchema(
        name="test_python_backend",
        category=ToolCategory.TESTING,
        description="Test Python backend code for syntax, imports, and runtime errors",
        parameters=[
            ToolParameter("file_path", "string", "Path to Python file to test"),
            ToolParameter("sandbox_dir", "string", "Sandbox directory for safe execution"),
            ToolParameter("timeout", "number", "Timeout in seconds", required=False, default=30)
        ],
        returns={
            "success": "Whether tests passed",
            "data": "Test results (syntax_valid, imports_valid, runs_without_error)",
            "errors": "List of errors encountered",
            "metadata": "Additional context including fixes_needed"
        },
        examples=[
            '{"file_path": "app.py", "sandbox_dir": "/tmp/sandbox", "timeout": 30}'
        ]
    ),
    test_python_backend
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="test_html_frontend",
        category=ToolCategory.TESTING,
        description="Test HTML frontend file for valid structure and required tags",
        parameters=[
            ToolParameter("file_path", "string", "Path to HTML file to test")
        ],
        returns={
            "success": "Whether HTML is valid",
            "data": "Validation results (valid_html, has_required_structure)",
            "errors": "List of HTML errors",
            "metadata": "Fixes needed"
        },
        examples=[
            '{"file_path": "templates/index.html"}'
        ]
    ),
    test_html_frontend
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="test_javascript_frontend",
        category=ToolCategory.TESTING,
        description="Test JavaScript frontend file for syntax errors",
        parameters=[
            ToolParameter("file_path", "string", "Path to JavaScript file to test")
        ],
        returns={
            "success": "Whether JavaScript is valid",
            "data": "Validation results (syntax_valid)",
            "errors": "List of syntax errors",
            "metadata": "Fixes needed"
        },
        examples=[
            '{"file_path": "static/script.js"}'
        ]
    ),
    test_javascript_frontend
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="test_css_frontend",
        category=ToolCategory.TESTING,
        description="Test CSS frontend file for syntax errors",
        parameters=[
            ToolParameter("file_path", "string", "Path to CSS file to test")
        ],
        returns={
            "success": "Whether CSS is valid",
            "data": "Validation results (syntax_valid)",
            "errors": "List of CSS errors",
            "metadata": "Fixes needed"
        },
        examples=[
            '{"file_path": "static/styles.css"}'
        ]
    ),
    test_css_frontend
)


# ============================================================================
# DEPENDENCY INSTALLATION TOOLS
# ============================================================================

def install_python_dependencies(requirements_file: str, venv_path: Optional[str] = None) -> ToolResult:
    """Install Python dependencies from requirements.txt."""
    errors = []
    warnings = []
    installed = []
    
    if not os.path.exists(requirements_file):
        return ToolResult(
            success=False,
            data={},
            errors=[f"Requirements file not found: {requirements_file}"],
            warnings=[],
            metadata={"file": requirements_file}
        )
    
    try:
        # Build pip command
        pip_cmd = ["pip", "install", "-r", requirements_file]
        if venv_path:
            pip_cmd = [os.path.join(venv_path, "bin", "pip")] + pip_cmd[1:]
        
        result = subprocess.run(
            pip_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            # Parse installed packages
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "Successfully installed" in line:
                    packages = line.split("Successfully installed")[1].strip()
                    installed = [p.strip() for p in packages.split()]
            
            return ToolResult(
                success=True,
                data={"installed": installed, "output": result.stdout},
                errors=[],
                warnings=[result.stderr] if result.stderr else [],
                metadata={"requirements_file": requirements_file, "venv": venv_path}
            )
        else:
            return ToolResult(
                success=False,
                data={"output": result.stdout},
                errors=[result.stderr],
                warnings=[],
                metadata={"requirements_file": requirements_file, "return_code": result.returncode}
            )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Installation failed: {str(e)}"],
            warnings=[],
            metadata={"requirements_file": requirements_file}
        )


def install_npm_dependencies(package_json: str, project_dir: str) -> ToolResult:
    """Install Node.js dependencies from package.json."""
    if not os.path.exists(package_json):
        return ToolResult(
            success=False,
            data={},
            errors=[f"package.json not found: {package_json}"],
            warnings=[],
            metadata={"file": package_json}
        )
    
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return ToolResult(
            success=result.returncode == 0,
            data={"output": result.stdout},
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[result.stderr] if result.returncode == 0 and result.stderr else [],
            metadata={"project_dir": project_dir}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"npm install failed: {str(e)}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )


# ============================================================================
# ENVIRONMENT SETUP TOOLS
# ============================================================================

def create_python_venv(venv_path: str, python_version: str = "python3") -> ToolResult:
    """Create a Python virtual environment."""
    try:
        result = subprocess.run(
            [python_version, "-m", "venv", venv_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return ToolResult(
                success=True,
                data={
                    "venv_path": venv_path,
                    "python_version": python_version,
                    "activate_cmd": f"source {venv_path}/bin/activate"
                },
                errors=[],
                warnings=[],
                metadata={"created_at": time.time()}
            )
        else:
            return ToolResult(
                success=False,
                data={},
                errors=[result.stderr],
                warnings=[],
                metadata={"python_version": python_version}
            )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"venv creation failed: {str(e)}"],
            warnings=[],
            metadata={}
        )


def setup_node_environment(project_dir: str, node_version: str = "18") -> ToolResult:
    """Setup Node.js environment with nvm if available."""
    try:
        # Check if nvm is available
        nvm_check = subprocess.run(
            ["which", "nvm"],
            capture_output=True,
            text=True
        )
        
        if nvm_check.returncode == 0:
            # Use nvm
            cmd = f"source ~/.nvm/nvm.sh && nvm use {node_version}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=project_dir
            )
        else:
            # Just check node version
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True
            )
        
        return ToolResult(
            success=result.returncode == 0,
            data={"output": result.stdout, "node_version": result.stdout.strip()},
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={"project_dir": project_dir}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Node.js setup failed: {str(e)}"],
            warnings=[],
            metadata={}
        )


# Register dependency and environment tools
TOOL_REGISTRY.register(
    ToolSchema(
        name="install_python_dependencies",
        category=ToolCategory.DEPENDENCY,
        description="Install Python dependencies from requirements.txt",
        parameters=[
            ToolParameter("requirements_file", "string", "Path to requirements.txt"),
            ToolParameter("venv_path", "string", "Path to virtual environment (optional)", required=False)
        ],
        returns={
            "success": "Whether installation succeeded",
            "data": "Installed packages and output",
            "errors": "Installation errors",
            "metadata": "File and environment info"
        },
        examples=['{"requirements_file": "requirements.txt"}']
    ),
    install_python_dependencies
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="install_npm_dependencies",
        category=ToolCategory.DEPENDENCY,
        description="Install Node.js dependencies from package.json",
        parameters=[
            ToolParameter("package_json", "string", "Path to package.json"),
            ToolParameter("project_dir", "string", "Project directory")
        ],
        returns={
            "success": "Whether npm install succeeded",
            "data": "Installation output",
            "errors": "npm errors",
            "metadata": "Project info"
        },
        examples=['{"package_json": "package.json", "project_dir": "./"}']
    ),
    install_npm_dependencies
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="create_python_venv",
        category=ToolCategory.ENVIRONMENT,
        description="Create a Python virtual environment",
        parameters=[
            ToolParameter("venv_path", "string", "Path where venv should be created"),
            ToolParameter("python_version", "string", "Python command (python3, python3.11, etc.)", required=False, default="python3")
        ],
        returns={
            "success": "Whether venv was created",
            "data": "venv_path, activate command, python version",
            "errors": "Creation errors",
            "metadata": "Timestamp"
        },
        examples=['{"venv_path": "./venv"}']
    ),
    create_python_venv
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="setup_node_environment",
        category=ToolCategory.ENVIRONMENT,
        description="Setup Node.js environment, optionally with nvm",
        parameters=[
            ToolParameter("project_dir", "string", "Project directory"),
            ToolParameter("node_version", "string", "Node version to use", required=False, default="18")
        ],
        returns={
            "success": "Whether Node.js is available",
            "data": "Node version and output",
            "errors": "Setup errors",
            "metadata": "Project info"
        },
        examples=['{"project_dir": "./", "node_version": "18"}']
    ),
    setup_node_environment
)


# ============================================================================
# DEPLOYMENT TOOLS  
# ============================================================================

def deploy_flask_local(app_file: str, host: str = "0.0.0.0", port: int = 5000) -> ToolResult:
    """Deploy Flask app locally."""
    if not os.path.exists(app_file):
        return ToolResult(
            success=False,
            data={},
            errors=[f"App file not found: {app_file}"],
            warnings=[],
            metadata={"file": app_file}
        )
    
    return ToolResult(
        success=True,
        data={
            "command": f"python {app_file}",
            "url": f"http://{host}:{port}",
            "host": host,
            "port": port
        },
        errors=[],
        warnings=["This returns the command to run - actual deployment should be done by user"],
        metadata={"app_file": app_file}
    )


TOOL_REGISTRY.register(
    ToolSchema(
        name="deploy_flask_local",
        category=ToolCategory.DEPLOYMENT,
        description="Prepare Flask app for local deployment",
        parameters=[
            ToolParameter("app_file", "string", "Path to Flask app.py"),
            ToolParameter("host", "string", "Host to bind to", required=False, default="0.0.0.0"),
            ToolParameter("port", "number", "Port to bind to", required=False, default=5000)
        ],
        returns={
            "success": "Whether deployment info was prepared",
            "data": "Command to run, URL, host, port",
            "warnings": "Deployment notes",
            "metadata": "App file info"
        },
        examples=['{"app_file": "app.py", "port": 5000}']
    ),
    deploy_flask_local
)


# ============================================================================
# AI INTEGRATION TOOLS
# ============================================================================

def test_openai_connection(api_key: str) -> ToolResult:
    """Test OpenAI API connection."""
    try:
        import openai
        openai.api_key = api_key
        
        # Test with a minimal call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        return ToolResult(
            success=True,
            data={"connected": True, "model": "gpt-3.5-turbo"},
            errors=[],
            warnings=[],
            metadata={"api_key_length": len(api_key)}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={"connected": False},
            errors=[f"OpenAI connection failed: {str(e)}"],
            warnings=[],
            metadata={}
        )


TOOL_REGISTRY.register(
    ToolSchema(
        name="test_openai_connection",
        category=ToolCategory.AI_INTEGRATION,
        description="Test OpenAI API connection and credentials",
        parameters=[
            ToolParameter("api_key", "string", "OpenAI API key to test")
        ],
        returns={
            "success": "Whether connection succeeded",
            "data": "Connection status and available model",
            "errors": "Connection errors",
            "metadata": "API key info (not the key itself)"
        },
        examples=['{"api_key": "sk-..."}']
    ),
    test_openai_connection
)


# ============================================================================
# MONITORING TOOLS
# ============================================================================

def check_flask_health(url: str, timeout: int = 5) -> ToolResult:
    """Check if Flask app is running and healthy."""
    try:
        import requests
        response = requests.get(url, timeout=timeout)
        
        return ToolResult(
            success=response.status_code == 200,
            data={
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "healthy": response.status_code == 200
            },
            errors=[f"HTTP {response.status_code}"] if response.status_code != 200 else [],
            warnings=[],
            metadata={"url": url}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={"healthy": False},
            errors=[f"Health check failed: {str(e)}"],
            warnings=[],
            metadata={"url": url}
        )


TOOL_REGISTRY.register(
    ToolSchema(
        name="check_flask_health",
        category=ToolCategory.MONITORING,
        description="Check if Flask application is running and responding",
        parameters=[
            ToolParameter("url", "string", "URL to check (e.g., http://localhost:5000)"),
            ToolParameter("timeout", "number", "Request timeout in seconds", required=False, default=5)
        ],
        returns={
            "success": "Whether app is healthy",
            "data": "Status code, response time, healthy flag",
            "errors": "Connection or HTTP errors",
            "metadata": "URL info"
        },
        examples=['{"url": "http://localhost:5000", "timeout": 5}']
    ),
    check_flask_health
)

