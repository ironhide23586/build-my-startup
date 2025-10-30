# Framework Features Demonstration

This app demonstrates every feature of the build_my_startup framework.

## 1. Adaptive Build Pipeline

**Input**: High-level description
```
"Build a Recipe Manager web application. Users can add, view, search, and favorite recipes..."
```

**AI Output**: Complete architecture with 8-12 components
- Backend API (app.py, routes, handlers)
- Frontend UI (HTML, CSS, JavaScript)
- Data storage (JSON files)
- Agent integration (recipe recommendation agent)
- Documentation (README, requirements)

## 2. Git Integration with AI Commit Messages

**Every file generation triggers:**
```python
# AI analyzes the code and generates commit message
await git_manager.commit_file(
    "app.py",
    agent_name="CodeWriter",
    action="generated",
    metadata={"safe": True, "size": 2456},
    code_preview=code[:500]
)
```

**AI generates messages like:**
- `[CodeWriter] Add Flask API with recipe CRUD endpoints`
- `[TestRunner] Validate recipe storage and retrieval logic`
- `[FrontendTestAgent] Fix HTML form validation issues`

## 3. Specialized Testing Agents

### BackendTestAgent
```python
# Agent has access to testing tools
test_result = test_python_file("app.py", sandbox_dir)

# Agent analyzes results
if not test_result["imports_valid"]:
    # Agent generates fix
    fix_code = await agent.write_code(
        "Fix import errors in app.py..."
    )
```

### FrontendTestAgent  
```python
# Agent tests HTML/CSS/JS
html_result = test_html_file("templates/index.html")
js_result = test_javascript_file("static/script.js")
css_result = test_css_file("static/styles.css")

# Agent fixes issues automatically
if not html_result["has_required_structure"]:
    # Generate corrected HTML
```

### IntegrationTestAgent
```python
# Agent validates frontend-backend integration
# - API endpoints match frontend requests
# - Data formats are consistent
# - Error handling works end-to-end
```

## 4. Iterative Debugging Workflow

```
Generate app.py
  ↓
Test app.py → ❌ Import error
  ↓
BackendTestAgent analyzes error
  ↓
Generate fix (attempt 1)
  ↓
Test again → ❌ Runtime error
  ↓
BackendTestAgent analyzes error
  ↓
Generate fix (attempt 2)
  ↓
Test again → ✅ PASSED!
  ↓
Git commit with AI message
```

## 5. Progress Indicators

**Thread-safe, real-time updates:**
```
⠋ Writing app.py...
⠙ Reviewing app.py...
⠹ Creating tests for app.py...
⠸ Testing app.py...
✅ Tests PASSED for: app.py
📝 Committed: [CodeWriter] Add Flask backend
```

**Progress tracking:**
```
📦 Component 3/8: static/styles.css
──────────────────────────────────────
   └─ 🤖 Generating code
   └─ 🔍 Reviewing code
   └─ 🧪 Testing
   └─ ✅ Complete
```

## 6. Agent Framework Integration

**Generated code uses framework:**
```python
# Generated agent extends framework Agent class
from build_my_startup.agent import Agent, Message

class RecipeRecommendationAgent(Agent):
    def __init__(self):
        super().__init__()
        # Uses MessageBus for communication
        # Integrates with other agents
    
    async def process_message(self, message: Message):
        if message.message_type == "recommend_pairing":
            # Agent logic here
            pass
```

## 7. Complete Testing Pipeline

```
Code Generation
  ↓
Code Review by CodeReviewer
  ↓
Test Generation by TestGenerator
  ↓
Test Execution by TestRunner
  ↓
┌─ PASSED → Git Commit → Done
└─ FAILED ↓
   Issue Analysis by Testing Agent
   ↓
   Fix Generation by CodeWriter
   ↓
   Re-test → (iterate up to 3 times)
```

## 8. Cross-Component Coordination

**Multiple agents work together:**
```
IdeationAgent → identifies components
CodeWriter → generates each file
CodeReviewer → reviews code quality
FrontendTestAgent → tests HTML/CSS/JS
BackendTestAgent → tests Python code
IntegrationTestAgent → validates integration
TestRunner → executes all tests
GitManager → commits with AI messages
BuildPipeline → coordinates everything
```

## The Magic

**You provide:**
- 5-10 sentences describing your app

**AI generates:**
- Complete architecture
- 8-12 working files
- All tests
- Full documentation
- Git commit history
- Working MVP

**Time:**
- Manual development: Days/weeks
- Framework build: 5-10 minutes

## How It Works

```python
# The ONLY code you write:
STARTUP_IDEA = "Build a recipe manager with search and favorites..."

# Everything else is automatic:
result = pipeline.run_adaptive_build(STARTUP_IDEA)

# You get:
# - Generated code
# - Tested code  
# - Fixed code
# - Committed code
# - Working app
```

## Philosophy

**Traditional Development:**
1. Design architecture manually
2. Write code manually
3. Test manually
4. Debug manually
5. Commit manually
6. Repeat for each feature

**Adaptive Framework:**
1. Describe what you want
2. AI agents do everything else
3. Get working app

This is the future of software development.

