"""
Deployment Tools - Everything for Python packaging, Docker, and deployment.

All tools follow rigid JSON contracts with structured inputs/outputs.
"""
import subprocess
import os
import json
from typing import Dict, List, Optional
from .tool_system import ToolResult, ToolSchema, ToolParameter, ToolCategory, TOOL_REGISTRY


# ============================================================================
# PYTHON PACKAGING TOOLS
# ============================================================================

def create_setup_py(
    package_name: str,
    version: str,
    description: str,
    author: str,
    dependencies: List[str],
    output_dir: str
) -> ToolResult:
    """Generate setup.py for Python package."""
    
    setup_content = f"""from setuptools import setup, find_packages

setup(
    name="{package_name}",
    version="{version}",
    description="{description}",
    author="{author}",
    packages=find_packages(),
    install_requires={json.dumps(dependencies, indent=8)},
    python_requires='>=3.8',
    entry_points={{
        'console_scripts': [
            '{package_name}={package_name}.main:main',
        ],
    }},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
"""
    
    try:
        setup_path = os.path.join(output_dir, "setup.py")
        with open(setup_path, 'w') as f:
            f.write(setup_content)
        
        return ToolResult(
            success=True,
            data={
                "file_path": setup_path,
                "package_name": package_name,
                "version": version,
                "content": setup_content
            },
            errors=[],
            warnings=[],
            metadata={"dependencies_count": len(dependencies)}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Failed to create setup.py: {str(e)}"],
            warnings=[],
            metadata={}
        )


def create_pyproject_toml(
    package_name: str,
    version: str,
    description: str,
    dependencies: List[str],
    output_dir: str,
    build_system: str = "setuptools"
) -> ToolResult:
    """Generate pyproject.toml for modern Python packaging."""
    
    pyproject_content = f"""[build-system]
requires = ["{build_system}>=61.0", "wheel"]
build-backend = "{build_system}.build_meta"

[project]
name = "{package_name}"
version = "{version}"
description = "{description}"
readme = "README.md"
requires-python = ">=3.8"
dependencies = {json.dumps(dependencies, indent=4)}

[project.optional-dependencies]
dev = ["pytest>=7.0", "black>=22.0", "flake8>=4.0"]

[project.scripts]
{package_name} = "{package_name}.main:main"

[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""
    
    try:
        pyproject_path = os.path.join(output_dir, "pyproject.toml")
        with open(pyproject_path, 'w') as f:
            f.write(pyproject_content)
        
        return ToolResult(
            success=True,
            data={
                "file_path": pyproject_path,
                "package_name": package_name,
                "version": version,
                "build_system": build_system,
                "content": pyproject_content
            },
            errors=[],
            warnings=[],
            metadata={"dependencies_count": len(dependencies)}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Failed to create pyproject.toml: {str(e)}"],
            warnings=[],
            metadata={}
        )


def build_python_package(
    project_dir: str,
    build_type: str = "wheel"
) -> ToolResult:
    """Build Python package (wheel or sdist)."""
    
    valid_types = ["wheel", "sdist", "both"]
    if build_type not in valid_types:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Invalid build_type. Must be one of: {', '.join(valid_types)}"],
            warnings=[],
            metadata={"build_type": build_type}
        )
    
    try:
        # Use python -m build
        cmd = ["python", "-m", "build"]
        if build_type == "wheel":
            cmd.append("--wheel")
        elif build_type == "sdist":
            cmd.append("--sdist")
        # both = no flag
        
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Check dist directory
        dist_dir = os.path.join(project_dir, "dist")
        built_files = []
        if os.path.exists(dist_dir):
            built_files = os.listdir(dist_dir)
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "build_type": build_type,
                "dist_dir": dist_dir,
                "built_files": built_files,
                "output": result.stdout
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[result.stderr] if result.returncode == 0 and result.stderr else [],
            metadata={"project_dir": project_dir, "files_count": len(built_files)}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Package build failed: {str(e)}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )


def pip_freeze(venv_path: Optional[str] = None) -> ToolResult:
    """Get installed packages (pip freeze)."""
    try:
        pip_cmd = "pip" if not venv_path else os.path.join(venv_path, "bin", "pip")
        
        result = subprocess.run(
            [pip_cmd, "freeze"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        packages = []
        if result.returncode == 0:
            packages = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "packages": packages,
                "count": len(packages),
                "output": result.stdout
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={"venv_path": venv_path}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"pip freeze failed: {str(e)}"],
            warnings=[],
            metadata={}
        )


# ============================================================================
# DOCKER TOOLS
# ============================================================================

def create_dockerfile(
    project_type: str,
    python_version: str,
    app_file: str,
    port: int,
    dependencies_file: str,
    output_dir: str
) -> ToolResult:
    """Generate Dockerfile for the project."""
    
    # Templates for different project types
    if project_type == "flask":
        dockerfile_content = f"""FROM python:{python_version}-slim

WORKDIR /app

# Install dependencies
COPY {dependencies_file} .
RUN pip install --no-cache-dir -r {dependencies_file}

# Copy application code
COPY . .

# Expose port
EXPOSE {port}

# Set environment variables
ENV FLASK_APP={app_file}
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "{app_file}"]
"""
    
    elif project_type == "fastapi":
        dockerfile_content = f"""FROM python:{python_version}-slim

WORKDIR /app

# Install dependencies
COPY {dependencies_file} .
RUN pip install --no-cache-dir -r {dependencies_file}

# Copy application code
COPY . .

# Expose port
EXPOSE {port}

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "{port}"]
"""
    
    elif project_type == "cli":
        dockerfile_content = f"""FROM python:{python_version}-slim

WORKDIR /app

# Install dependencies
COPY {dependencies_file} .
RUN pip install --no-cache-dir -r {dependencies_file}

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set entrypoint
ENTRYPOINT ["python", "{app_file}"]
"""
    
    else:
        # Generic Python app
        dockerfile_content = f"""FROM python:{python_version}-slim

WORKDIR /app

# Install dependencies
COPY {dependencies_file} .
RUN pip install --no-cache-dir -r {dependencies_file}

# Copy application code
COPY . .

# Run the application
CMD ["python", "{app_file}"]
"""
    
    try:
        dockerfile_path = os.path.join(output_dir, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Also create .dockerignore
        dockerignore_content = """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.git
.gitignore
.pytest_cache
.coverage
htmlcov/
dist/
build/
*.egg-info/
.DS_Store
"""
        dockerignore_path = os.path.join(output_dir, ".dockerignore")
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content)
        
        return ToolResult(
            success=True,
            data={
                "dockerfile_path": dockerfile_path,
                "dockerignore_path": dockerignore_path,
                "project_type": project_type,
                "python_version": python_version,
                "port": port,
                "content": dockerfile_content
            },
            errors=[],
            warnings=[],
            metadata={"app_file": app_file}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Failed to create Dockerfile: {str(e)}"],
            warnings=[],
            metadata={}
        )


def docker_build(
    project_dir: str,
    image_name: str,
    tag: str = "latest",
    dockerfile: str = "Dockerfile"
) -> ToolResult:
    """Build Docker image."""
    
    if not os.path.exists(os.path.join(project_dir, dockerfile)):
        return ToolResult(
            success=False,
            data={},
            errors=[f"Dockerfile not found: {dockerfile}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )
    
    try:
        full_image_name = f"{image_name}:{tag}"
        cmd = ["docker", "build", "-t", full_image_name, "-f", dockerfile, "."]
        
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "image_name": full_image_name,
                "tag": tag,
                "output": result.stdout[-1000:],  # Last 1000 chars
                "built": result.returncode == 0
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={
                "project_dir": project_dir,
                "dockerfile": dockerfile,
                "return_code": result.returncode
            }
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Docker build failed: {str(e)}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )


def docker_run(
    image_name: str,
    tag: str = "latest",
    port_mapping: Optional[Dict[int, int]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    detach: bool = True
) -> ToolResult:
    """Run Docker container."""
    
    full_image_name = f"{image_name}:{tag}"
    cmd = ["docker", "run"]
    
    if detach:
        cmd.append("-d")
    
    if port_mapping:
        for host_port, container_port in port_mapping.items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])
    
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])
    
    cmd.append(full_image_name)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        container_id = result.stdout.strip() if result.returncode == 0 else None
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "container_id": container_id,
                "image": full_image_name,
                "port_mapping": port_mapping,
                "command": " ".join(cmd)
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={
                "detached": detach,
                "env_vars_count": len(env_vars) if env_vars else 0
            }
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Docker run failed: {str(e)}"],
            warnings=[],
            metadata={"image": full_image_name}
        )


def create_requirements_txt(
    packages: List[str],
    output_dir: str,
    include_versions: bool = True
) -> ToolResult:
    """Generate requirements.txt file."""
    
    try:
        # If include_versions, try to get current versions
        content_lines = []
        
        for package in packages:
            if include_versions:
                try:
                    # Try to get installed version
                    result = subprocess.run(
                        ["pip", "show", package],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.startswith('Version:'):
                                version = line.split(':')[1].strip()
                                content_lines.append(f"{package}=={version}")
                                break
                        else:
                            content_lines.append(package)
                    else:
                        content_lines.append(package)
                except:
                    content_lines.append(package)
            else:
                content_lines.append(package)
        
        content = '\n'.join(content_lines) + '\n'
        
        req_path = os.path.join(output_dir, "requirements.txt")
        with open(req_path, 'w') as f:
            f.write(content)
        
        return ToolResult(
            success=True,
            data={
                "file_path": req_path,
                "packages": content_lines,
                "count": len(content_lines),
                "content": content
            },
            errors=[],
            warnings=[],
            metadata={"include_versions": include_versions}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Failed to create requirements.txt: {str(e)}"],
            warnings=[],
            metadata={}
        )


def build_wheel(project_dir: str) -> ToolResult:
    """Build wheel distribution."""
    try:
        result = subprocess.run(
            ["python", "-m", "build", "--wheel"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        dist_dir = os.path.join(project_dir, "dist")
        wheels = []
        if os.path.exists(dist_dir):
            wheels = [f for f in os.listdir(dist_dir) if f.endswith('.whl')]
        
        return ToolResult(
            success=result.returncode == 0 and len(wheels) > 0,
            data={
                "wheels": wheels,
                "dist_dir": dist_dir,
                "output": result.stdout
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={"project_dir": project_dir}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Wheel build failed: {str(e)}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )


def build_sdist(project_dir: str) -> ToolResult:
    """Build source distribution."""
    try:
        result = subprocess.run(
            ["python", "-m", "build", "--sdist"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        dist_dir = os.path.join(project_dir, "dist")
        sdists = []
        if os.path.exists(dist_dir):
            sdists = [f for f in os.listdir(dist_dir) if f.endswith('.tar.gz')]
        
        return ToolResult(
            success=result.returncode == 0 and len(sdists) > 0,
            data={
                "sdists": sdists,
                "dist_dir": dist_dir,
                "output": result.stdout
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={"project_dir": project_dir}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Source dist build failed: {str(e)}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )


def pip_install_local(
    package_path: str,
    editable: bool = False,
    venv_path: Optional[str] = None
) -> ToolResult:
    """Install package locally (for testing)."""
    try:
        pip_cmd = "pip" if not venv_path else os.path.join(venv_path, "bin", "pip")
        cmd = [pip_cmd, "install"]
        
        if editable:
            cmd.append("-e")
        
        cmd.append(package_path)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "installed": result.returncode == 0,
                "editable": editable,
                "output": result.stdout
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={"package_path": package_path, "venv": venv_path}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Local install failed: {str(e)}"],
            warnings=[],
            metadata={"package_path": package_path}
        )


# ============================================================================
# DOCKER COMPOSE TOOLS
# ============================================================================

def create_docker_compose(
    services: Dict[str, Dict],
    output_dir: str,
    version: str = "3.8"
) -> ToolResult:
    """Generate docker-compose.yml file."""
    
    compose_dict = {
        "version": version,
        "services": services
    }
    
    try:
        import yaml
        compose_path = os.path.join(output_dir, "docker-compose.yml")
        
        with open(compose_path, 'w') as f:
            yaml.dump(compose_dict, f, default_flow_style=False)
        
        return ToolResult(
            success=True,
            data={
                "file_path": compose_path,
                "services": list(services.keys()),
                "service_count": len(services)
            },
            errors=[],
            warnings=[],
            metadata={"version": version}
        )
    
    except ImportError:
        # Fallback to manual YAML creation
        try:
            compose_content = f"version: '{version}'\n\nservices:\n"
            for service_name, service_config in services.items():
                compose_content += f"  {service_name}:\n"
                for key, value in service_config.items():
                    if isinstance(value, list):
                        compose_content += f"    {key}:\n"
                        for item in value:
                            compose_content += f"      - {item}\n"
                    elif isinstance(value, dict):
                        compose_content += f"    {key}:\n"
                        for k, v in value.items():
                            compose_content += f"      {k}: {v}\n"
                    else:
                        compose_content += f"    {key}: {value}\n"
            
            compose_path = os.path.join(output_dir, "docker-compose.yml")
            with open(compose_path, 'w') as f:
                f.write(compose_content)
            
            return ToolResult(
                success=True,
                data={
                    "file_path": compose_path,
                    "services": list(services.keys()),
                    "service_count": len(services),
                    "content": compose_content
                },
                errors=[],
                warnings=["PyYAML not installed, used manual formatting"],
                metadata={"version": version}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                errors=[f"Failed to create docker-compose.yml: {str(e)}"],
                warnings=[],
                metadata={}
            )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Failed to create docker-compose.yml: {str(e)}"],
            warnings=[],
            metadata={}
        )


def docker_compose_up(project_dir: str, detach: bool = True, build: bool = True) -> ToolResult:
    """Start services with docker-compose."""
    
    compose_file = os.path.join(project_dir, "docker-compose.yml")
    if not os.path.exists(compose_file):
        return ToolResult(
            success=False,
            data={},
            errors=["docker-compose.yml not found"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )
    
    try:
        cmd = ["docker-compose", "up"]
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "running": result.returncode == 0,
                "output": result.stdout,
                "command": " ".join(cmd)
            },
            errors=[result.stderr] if result.returncode != 0 else [],
            warnings=[],
            metadata={"project_dir": project_dir, "detached": detach}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"docker-compose up failed: {str(e)}"],
            warnings=[],
            metadata={"project_dir": project_dir}
        )


# ============================================================================
# REGISTER ALL TOOLS
# ============================================================================

# Python Packaging Tools
TOOL_REGISTRY.register(
    ToolSchema(
        name="create_setup_py",
        category=ToolCategory.BUILD,
        description="Generate setup.py for Python package distribution",
        parameters=[
            ToolParameter("package_name", "string", "Name of the package"),
            ToolParameter("version", "string", "Package version (e.g., '0.1.0')"),
            ToolParameter("description", "string", "Package description"),
            ToolParameter("author", "string", "Author name"),
            ToolParameter("dependencies", "array", "List of dependencies"),
            ToolParameter("output_dir", "string", "Directory to create setup.py in")
        ],
        returns={
            "success": "Whether setup.py was created",
            "data": "File path, package info, content",
            "errors": "Creation errors"
        },
        examples=['{"package_name": "myapp", "version": "0.1.0", "description": "My app", "author": "Me", "dependencies": ["flask"], "output_dir": "./"}']
    ),
    create_setup_py
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="create_pyproject_toml",
        category=ToolCategory.BUILD,
        description="Generate pyproject.toml for modern Python packaging",
        parameters=[
            ToolParameter("package_name", "string", "Name of the package"),
            ToolParameter("version", "string", "Package version"),
            ToolParameter("description", "string", "Package description"),
            ToolParameter("dependencies", "array", "List of dependencies"),
            ToolParameter("output_dir", "string", "Directory to create pyproject.toml in"),
            ToolParameter("build_system", "string", "Build system to use", required=False, default="setuptools")
        ],
        returns={
            "success": "Whether pyproject.toml was created",
            "data": "File path, package info, build system, content",
            "errors": "Creation errors"
        },
        examples=['{"package_name": "myapp", "version": "0.1.0", "description": "My app", "dependencies": ["flask>=2.0"], "output_dir": "./"}']
    ),
    create_pyproject_toml
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="build_python_package",
        category=ToolCategory.BUILD,
        description="Build Python package (wheel, sdist, or both)",
        parameters=[
            ToolParameter("project_dir", "string", "Project directory containing setup.py or pyproject.toml"),
            ToolParameter("build_type", "string", "Type of build", required=False, default="wheel", enum=["wheel", "sdist", "both"])
        ],
        returns={
            "success": "Whether build succeeded",
            "data": "Built files, dist directory, output",
            "errors": "Build errors"
        },
        examples=['{"project_dir": "./", "build_type": "wheel"}']
    ),
    build_python_package
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="build_wheel",
        category=ToolCategory.BUILD,
        description="Build wheel distribution (.whl file)",
        parameters=[
            ToolParameter("project_dir", "string", "Project directory")
        ],
        returns={
            "success": "Whether wheel was built",
            "data": "Wheel files, dist directory",
            "errors": "Build errors"
        },
        examples=['{"project_dir": "./"}']
    ),
    build_wheel
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="build_sdist",
        category=ToolCategory.BUILD,
        description="Build source distribution (.tar.gz file)",
        parameters=[
            ToolParameter("project_dir", "string", "Project directory")
        ],
        returns={
            "success": "Whether sdist was built",
            "data": "Source dist files, dist directory",
            "errors": "Build errors"
        },
        examples=['{"project_dir": "./"}']
    ),
    build_sdist
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="pip_freeze",
        category=ToolCategory.DEPENDENCY,
        description="Get list of all installed Python packages with versions",
        parameters=[
            ToolParameter("venv_path", "string", "Path to virtual environment (optional)", required=False)
        ],
        returns={
            "success": "Whether pip freeze succeeded",
            "data": "List of packages, count, raw output",
            "errors": "pip errors"
        },
        examples=['{"venv_path": "./venv"}']
    ),
    pip_freeze
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="pip_install_local",
        category=ToolCategory.DEPENDENCY,
        description="Install package locally (for testing before publishing)",
        parameters=[
            ToolParameter("package_path", "string", "Path to package directory or wheel"),
            ToolParameter("editable", "boolean", "Install in editable mode (-e)", required=False, default=False),
            ToolParameter("venv_path", "string", "Virtual environment path", required=False)
        ],
        returns={
            "success": "Whether installation succeeded",
            "data": "Installation status, output",
            "errors": "Installation errors"
        },
        examples=['{"package_path": "./", "editable": true}']
    ),
    pip_install_local
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="create_requirements_txt",
        category=ToolCategory.BUILD,
        description="Generate requirements.txt from package list",
        parameters=[
            ToolParameter("packages", "array", "List of package names"),
            ToolParameter("output_dir", "string", "Directory to create requirements.txt"),
            ToolParameter("include_versions", "boolean", "Include version pins", required=False, default=True)
        ],
        returns={
            "success": "Whether requirements.txt was created",
            "data": "File path, package list, content",
            "errors": "Creation errors"
        },
        examples=['{"packages": ["flask", "requests", "openai"], "output_dir": "./", "include_versions": true}']
    ),
    create_requirements_txt
)

# Docker Tools
TOOL_REGISTRY.register(
    ToolSchema(
        name="create_dockerfile",
        category=ToolCategory.DEPLOYMENT,
        description="Generate Dockerfile for Python project",
        parameters=[
            ToolParameter("project_type", "string", "Type of project", enum=["flask", "fastapi", "cli", "generic"]),
            ToolParameter("python_version", "string", "Python version (e.g., '3.11')"),
            ToolParameter("app_file", "string", "Main application file"),
            ToolParameter("port", "number", "Port to expose"),
            ToolParameter("dependencies_file", "string", "Requirements file name"),
            ToolParameter("output_dir", "string", "Directory to create Dockerfile")
        ],
        returns={
            "success": "Whether Dockerfile was created",
            "data": "Dockerfile path, .dockerignore path, project info, content",
            "errors": "Creation errors"
        },
        examples=['{"project_type": "flask", "python_version": "3.11", "app_file": "app.py", "port": 5000, "dependencies_file": "requirements.txt", "output_dir": "./"}']
    ),
    create_dockerfile
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="docker_build",
        category=ToolCategory.DEPLOYMENT,
        description="Build Docker image from Dockerfile",
        parameters=[
            ToolParameter("project_dir", "string", "Project directory containing Dockerfile"),
            ToolParameter("image_name", "string", "Name for Docker image"),
            ToolParameter("tag", "string", "Image tag", required=False, default="latest"),
            ToolParameter("dockerfile", "string", "Dockerfile name", required=False, default="Dockerfile")
        ],
        returns={
            "success": "Whether build succeeded",
            "data": "Image name, tag, build output",
            "errors": "Build errors"
        },
        examples=['{"project_dir": "./", "image_name": "myapp", "tag": "v1.0"}']
    ),
    docker_build
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="docker_run",
        category=ToolCategory.DEPLOYMENT,
        description="Run Docker container from image",
        parameters=[
            ToolParameter("image_name", "string", "Docker image name"),
            ToolParameter("tag", "string", "Image tag", required=False, default="latest"),
            ToolParameter("port_mapping", "object", "Port mappings {host_port: container_port}", required=False),
            ToolParameter("env_vars", "object", "Environment variables {KEY: value}", required=False),
            ToolParameter("detach", "boolean", "Run in detached mode", required=False, default=True)
        ],
        returns={
            "success": "Whether container started",
            "data": "Container ID, image, port mapping, command",
            "errors": "Runtime errors"
        },
        examples=['{"image_name": "myapp", "port_mapping": {"5000": 5000}, "env_vars": {"DEBUG": "true"}}']
    ),
    docker_run
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="create_docker_compose",
        category=ToolCategory.DEPLOYMENT,
        description="Generate docker-compose.yml for multi-service deployments",
        parameters=[
            ToolParameter("services", "object", "Service definitions"),
            ToolParameter("output_dir", "string", "Directory to create docker-compose.yml"),
            ToolParameter("version", "string", "Compose file version", required=False, default="3.8")
        ],
        returns={
            "success": "Whether docker-compose.yml was created",
            "data": "File path, service names, count",
            "errors": "Creation errors"
        },
        examples=['{"services": {"web": {"build": ".", "ports": ["5000:5000"]}}, "output_dir": "./"}']
    ),
    create_docker_compose
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="docker_compose_up",
        category=ToolCategory.DEPLOYMENT,
        description="Start all services defined in docker-compose.yml",
        parameters=[
            ToolParameter("project_dir", "string", "Directory containing docker-compose.yml"),
            ToolParameter("detach", "boolean", "Run in background", required=False, default=True),
            ToolParameter("build", "boolean", "Build images before starting", required=False, default=True)
        ],
        returns={
            "success": "Whether services started",
            "data": "Running status, output, command",
            "errors": "Startup errors"
        },
        examples=['{"project_dir": "./", "detach": true, "build": true}']
    ),
    docker_compose_up
)

