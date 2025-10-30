# Configuration Guide

The Build My Startup framework uses a centralized `config.json` file for all settings.

## Quick Start

```bash
# 1. Copy the example config
cp build_my_startup/config.example.json build_my_startup/config.json

# 2. Edit config.json and add your API keys
nano build_my_startup/config.json

# 3. Run any app - it will use your config
python apps/recipe_manager_app/scripts/build_app.py
```

## Configuration Priority

Settings are loaded in this order (highest priority first):

1. **Environment Variables** (highest priority)
   ```bash
   export BUILD_MY_STARTUP_API_KEYS_OPENAI="sk-..."
   export BUILD_MY_STARTUP_BUILD_SETTINGS_TIMEOUT="300"
   ```

2. **config.json** (recommended)
   ```json
   {
     "api_keys": {
       "openai": "sk-..."
     }
   }
   ```

3. **Legacy config.py** (deprecated, for backward compatibility)

## Configuration Sections

### 1. API Keys

```json
"api_keys": {
  "openai": "sk-proj-...",
  "anthropic": "sk-ant-...",
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "...",
  "aws_region": "us-east-1"
}
```

**Environment Variable Alternative:**
```bash
export OPENAI_API_KEY="sk-proj-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
```

### 2. Model Selection

```json
"default_models": {
  "code_generation": "gpt-4o-mini",
  "code_review": "gpt-4o-mini",
  "test_generation": "gpt-4o-mini",
  "planning": "gpt-4o",
  "ideation": "gpt-4o",
  "git_commits": "gpt-4o-mini",
  "reasoning": "o1-mini",
  "vision": "gpt-4o"
}
```

**Available Models:**

**OpenAI:**
- `gpt-4o` - Latest multimodal (recommended for ideation)
- `gpt-4o-mini` - Fast and affordable (recommended for code generation)
- `gpt-4-turbo` - High performance
- `o1-preview` - Advanced reasoning
- `o1-mini` - Efficient reasoning

**Claude (Anthropic):**
- `claude-3-5-sonnet-20241022` - Latest, most capable
- `claude-3-opus-20240229` - Most intelligent
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fast and affordable

**AWS Bedrock:**
- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `anthropic.claude-3-opus-20240229-v1:0`

### 3. Build Settings

```json
"build_settings": {
  "max_fix_attempts": 3,
  "max_iterations_per_file": 5,
  "timeout": 600,
  "poll_interval": 1.0,
  "show_progress": true,
  "generate_plan": true,
  "enable_git": true,
  "use_ai_commit_messages": true
}
```

**What they control:**
- `max_fix_attempts`: How many times to try fixing a failing file
- `timeout`: Maximum time for entire build (seconds)
- `enable_git`: Auto-create git repo and commit changes
- `use_ai_commit_messages`: Use AI to generate commit messages

### 4. Testing Settings

```json
"testing_settings": {
  "run_frontend_tests": true,
  "run_backend_tests": true,
  "run_integration_tests": true,
  "test_timeout": 30,
  "use_specialized_agents": true
}
```

**Specialized Agents:**
- `FrontendTestAgent` - Tests HTML/CSS/JS
- `BackendTestAgent` - Tests Python code
- `IntegrationTestAgent` - Tests component integration

### 5. Deployment Settings

```json
"deployment_settings": {
  "python_version": "3.11",
  "default_port": 5000,
  "create_dockerfile": true,
  "create_docker_compose": false,
  "build_wheel": false,
  "build_sdist": false
}
```

**Auto-generation:**
- `create_dockerfile`: Generate Dockerfile for each app
- `create_docker_compose`: Generate docker-compose.yml
- `build_wheel`: Build Python wheel after generation
- `build_sdist`: Build source distribution

### 6. Git Settings

```json
"git_settings": {
  "auto_init": true,
  "commit_after_generation": true,
  "commit_after_testing": true,
  "commit_after_fixes": true,
  "batch_commit_at_end": true
}
```

**Commit Strategy:**
- After each file is generated
- After tests pass
- After fixes are applied
- Final batch commit at end

All commits use AI-generated messages!

## Using Config in Code

### Python API

```python
from build_my_startup.config_manager import config, get_config, get_api_key, get_model

# Get API key
openai_key = get_api_key("openai")

# Get model for task
model = get_model("code_generation")  # Returns "gpt-4o-mini"

# Get any config value with dot notation
timeout = get_config("build_settings.timeout", default=600)

# Validate configuration
validation = config.validate()
print(validation)
# {"valid": True, "issues": [], "warnings": []}
```

### In Build Scripts

```python
from build_my_startup.pipelines.adaptive_build import AdaptiveBuildConfig

# All settings loaded from config.json automatically
config = AdaptiveBuildConfig(
    output_dir="./generated"
    # Everything else loaded from config.json!
)

# Or override specific settings
config = AdaptiveBuildConfig(
    output_dir="./generated",
    max_fix_attempts=5,  # Override config.json
    timeout=1200  # Override config.json
    # Other settings from config.json
)
```

## Environment Variable Overrides

Any config value can be overridden with environment variables:

```bash
# Format: BUILD_MY_STARTUP_{SECTION}_{KEY}
export BUILD_MY_STARTUP_BUILD_SETTINGS_TIMEOUT="300"
export BUILD_MY_STARTUP_DEFAULT_MODELS_CODE_GENERATION="gpt-4o"
export BUILD_MY_STARTUP_IDEATION_SETTINGS_MAX_FILES="8"
```

## Budget Optimization

### Low Budget ($0.10-0.50 per app)
```json
"default_models": {
  "code_generation": "gpt-4o-mini",
  "code_review": "gpt-4o-mini",
  "test_generation": "gpt-4o-mini",
  "planning": "gpt-4o-mini",
  "ideation": "gpt-4o-mini"
}
```

### Medium Budget ($0.50-2.00 per app) - Recommended
```json
"default_models": {
  "code_generation": "gpt-4o-mini",
  "code_review": "gpt-4o-mini",
  "test_generation": "gpt-4o-mini",
  "planning": "gpt-4o",
  "ideation": "gpt-4o"
}
```

### High Budget ($2.00-5.00 per app)
```json
"default_models": {
  "code_generation": "gpt-4o",
  "code_review": "claude-3-5-sonnet-20241022",
  "test_generation": "gpt-4o",
  "planning": "claude-3-opus-20240229",
  "ideation": "claude-3-opus-20240229"
}
```

## Performance Tuning

### Fast Builds (2-3 minutes)
```json
"ideation_settings": {
  "min_files": 2,
  "max_files": 4
},
"build_settings": {
  "max_fix_attempts": 1,
  "max_iterations_per_file": 2
}
```

### Balanced (5-8 minutes) - Recommended
```json
"ideation_settings": {
  "min_files": 4,
  "max_files": 12
},
"build_settings": {
  "max_fix_attempts": 3,
  "max_iterations_per_file": 5
}
```

### Comprehensive (10-15 minutes)
```json
"ideation_settings": {
  "min_files": 8,
  "max_files": 20
},
"build_settings": {
  "max_fix_attempts": 5,
  "max_iterations_per_file": 10
}
```

## Validation

Check your configuration:

```python
from build_my_startup.config_manager import validate_config

result = validate_config()
print(result)
```

Output:
```json
{
  "valid": true,
  "issues": [],
  "warnings": ["Anthropic API key not configured"],
  "config_file": "/path/to/config.json",
  "config_exists": true
}
```

## Security Notes

1. **Never commit config.json** - It's in .gitignore
2. **Use environment variables** for CI/CD
3. **config.example.json** is safe to commit (no secrets)
4. **config.py is deprecated** but kept for backward compatibility

## Troubleshooting

### "OpenAI API key not found"
1. Check `config.json` has `api_keys.openai` set
2. Or set `OPENAI_API_KEY` environment variable
3. Or use legacy `config.py` (deprecated)

### "Configuration loaded from..."
This message shows where config was loaded from.

### Changes not taking effect
```python
from build_my_startup.config_manager import reload_config
reload_config()  # Reload config.json
```

## Best Practices

1. **Use config.json** for local development
2. **Use environment variables** for production/CI
3. **Keep config.example.json** updated
4. **Validate config** before long builds
5. **Use budget-appropriate models** to save costs

## Example: Complete Configuration

```json
{
  "api_keys": {
    "openai": "sk-proj-YOUR_KEY_HERE"
  },
  "default_models": {
    "code_generation": "gpt-4o-mini",
    "ideation": "gpt-4o"
  },
  "build_settings": {
    "max_fix_attempts": 3,
    "timeout": 600,
    "enable_git": true
  },
  "testing_settings": {
    "use_specialized_agents": true
  }
}
```

This enables:
- ✅ AI code generation with gpt-4o-mini
- ✅ Architecture inference with gpt-4o
- ✅ Git integration with AI commits
- ✅ Specialized testing agents
- ✅ Iterative debugging (3 attempts)
- ✅ 10-minute timeout

Perfect for most use cases!

