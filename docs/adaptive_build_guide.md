# Adaptive Build Pipeline Guide

## Overview

The Adaptive Build Pipeline is a revolutionary approach to application development where you simply describe what you want to build in plain English, and AI agents automatically figure out the architecture, components, and implementation details.

## How It Works

### Phase 1: Ideation
The **IdeationAgent** analyzes your high-level description and:
- Identifies required components (backend, frontend, agents, utilities)
- Determines file structure and architecture
- Specifies technology stack
- Creates detailed requirements for each component

### Phase 2: Build
The standard build pipeline then:
- Generates code for each identified component
- Reviews code for quality and correctness
- Creates tests for validation
- Fixes issues automatically
- Saves working code to your output directory

## Usage

### Simple Example

```python
from build_my_startup.pipelines.adaptive_build import build_adaptive_sync

result = build_adaptive_sync(
    description="Build a CLI todo app with add, complete, and list commands",
    output_dir="./my_app",
    target_platform="macOS"
)
```

### With Preferences

```python
result = build_adaptive_sync(
    description="""
    Build a web app for tracking workouts.
    Users can log exercises, reps, and sets.
    Show progress over time with charts.
    """,
    output_dir="./workout_tracker",
    target_platform="macOS",
    tech_preferences={
        "backend": "Flask",
        "database": "SQLite",
        "frontend": "HTML/CSS/JS"
    },
    min_files=3,
    max_files=8
)
```

### Full Configuration

```python
from build_my_startup.pipelines.adaptive_build import (
    AdaptiveBuildPipeline, 
    AdaptiveBuildConfig
)

config = AdaptiveBuildConfig(
    output_dir="./generated",
    max_fix_attempts=3,
    timeout=300.0,
    generate_plan=True,
    ideation_timeout=60.0,
    min_files=2,
    max_files=10
)

pipeline = AdaptiveBuildPipeline(config)
result = await pipeline.run_adaptive_build(
    description="Your startup idea...",
    target_platform="macOS",
    tech_preferences={}
)
```

## Key Features

### Automatic Component Detection
The AI identifies:
- Backend files (API servers, handlers, agents)
- Frontend files (HTML, CSS, JavaScript)
- Configuration files (requirements.txt, config files)
- Utility modules (helpers, handlers, clients)
- Agent framework components
- Documentation

### Smart Architecture
The AI considers:
- Separation of concerns
- Integration patterns
- Error handling
- Testing strategies
- Cross-compatibility with the agent framework

### Technology Preferences
Guide the AI's decisions:
- `backend_framework`: Flask, FastAPI, Django
- `frontend`: vanilla_js, React, Vue
- `database`: SQLite, PostgreSQL, MongoDB
- `ai_provider`: OpenAI, local models
- `port`: Server port number
- `agent_framework`: Whether to use build_my_startup agents

## Cross-Compatibility

The Adaptive Build Pipeline is designed to work seamlessly with:

1. **StandardBuildPipeline**: Uses the same underlying agents and infrastructure
2. **Existing Apps**: All apps in `/apps/` use the same framework
3. **Agent Framework**: Generated code integrates with `build_my_startup` agents
4. **Testing Infrastructure**: Same testing and validation systems

### Example: Both Approaches Work

**Explicit Tasks (face_detection_app):**
```python
BUILD_TASKS = [
    {"task": "app.py", "description": "Create Flask app..."},
    {"task": "camera_handler.py", "description": "Handle camera..."}
]
pipeline.run_build(BUILD_TASKS, "Face Detection App")
```

**Adaptive (commentary_app):**
```python
STARTUP_IDEA = "Build an AI commentary generator for images..."
pipeline.run_adaptive_build(STARTUP_IDEA, "macOS", {})
```

Both produce working apps using the same framework!

## Best Practices

### 1. Be Specific About Core Features
❌ "Build a web app"
✅ "Build a web app where users upload photos and get AI-generated captions"

### 2. Mention Technical Constraints
Include platform, performance needs, integration requirements:
```
"Run locally on Mac, process images quickly, use OpenAI Vision API"
```

### 3. Describe User Experience
Help the AI understand the user flow:
```
"Users drag and drop images, see a preview, click 'Generate', 
and get commentary in a nice card layout"
```

### 4. Set Reasonable File Limits
- Small CLI tool: `min_files=2, max_files=4`
- Medium web app: `min_files=4, max_files=8`
- Complex system: `min_files=8, max_files=15`

### 5. Use Tech Preferences Strategically
Don't over-specify - let the AI make smart choices:
```python
tech_preferences={
    "framework": "Flask",  # Core choice
    "port": 5001          # Specific requirement
    # AI decides the rest
}
```

## Troubleshooting

### "Failed to infer build tasks"
- Make description more specific
- Include more details about features
- Mention technical requirements explicitly

### Long Build Times
- Reduce `max_files` count
- Increase `timeout` setting
- Check OpenAI API rate limits

### Integration Issues
- Ensure tech_preferences mention "agent_framework"
- Check that generated agents extend `Agent` class
- Verify imports from `build_my_startup`

## Examples

See working examples in:
- `/examples/simple_adaptive_build.py` - Minimal CLI tool
- `/apps/commentary_app/scripts/build_app.py` - Full web application
- `/apps/face_detection_app/scripts/build_app.py` - Traditional structured build

## Architecture

```
User Description
      ↓
IdeationAgent (analyzes & plans)
      ↓
Build Tasks (inferred)
      ↓
StandardBuildPipeline
      ↓
  CodeWriter → CodeReviewer → TestGenerator → TestRunner
      ↓
Generated Application
```

## Future Enhancements

Planned features:
- Multi-agent collaboration during ideation
- Learning from past builds
- Interactive refinement of build tasks
- Automatic dependency resolution
- Deployment automation

