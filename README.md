# Build My Startup

**A Fully Automated Open-Source AI-Powered Agentic Framework**

Build your startup with AI Employees like a real company. Multiple specialized AI agents communicate asynchronously to generate complete applications - from planning to code to deployment.

## Features

- **Direct Agent-to-Agent Communication**: Agents can send messages directly to each other
- **Message Bus**: Centralized communication hub for managing multiple agents
- **Topic-Based Pub/Sub**: Publish-subscribe pattern for event-driven communication
- **Asynchronous Processing**: All communication happens asynchronously using Python's asyncio
- **AI Agent Integration**: Built-in support for OpenAI-powered agents with API key configured

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key (required for AI agents)
export OPENAI_API_KEY='your-api-key-here'

# Run examples
python examples/cursor_agents_example.py

# Or build an app using the standard pipeline
python apps/face_detection_app/scripts/build_app.py
```

**Note:** The OpenAI API key can be set via:
1. Environment variable: `export OPENAI_API_KEY='your-key'` (recommended)
2. Or directly in `build_my_startup/config.py`

## 🚀 Adaptive Build Pipeline (NEW!)

**Describe your startup in plain English - AI agents figure out the rest!**

The Adaptive Build Pipeline uses AI agents to automatically infer what needs to be built from a high-level description. No need to specify exact files or architectures - just describe your idea.

```python
from build_my_startup.pipelines.adaptive_build import build_adaptive_sync

# Just describe what you want to build!
result = build_adaptive_sync(
    description="""
    I want to build an AI-powered image commentary generator.
    Users upload images and get intelligent commentary using OpenAI Vision API.
    Should have a beautiful web UI and run on Mac.
    """,
    output_dir="./generated",
    target_platform="macOS",
    tech_preferences={"framework": "Flask"}
)
```

**What happens automatically:**
1. 🧠 **IdeationAgent** analyzes your description and identifies components needed
2. 🏗️ **CodeWriter** generates code for each component
3. 🔍 **CodeReviewer** reviews the generated code
4. 🧪 **TestGenerator** creates tests for validation
5. ✅ **TestRunner** executes tests and ensures everything works
6. 📋 **PlannerAgent** creates project documentation

**Examples:**
- `examples/simple_adaptive_build.py` - Simple CLI tool from description
- `apps/commentary_app/scripts/build_app.py` - Full web app from high-level idea
- `apps/face_detection_app/scripts/build_app.py` - Structured build with explicit tasks

## Components

### 1. Agent (`agent.py`)
- Individual agents with unique IDs
- Async message queues
- Customizable message handlers
- Async communication methods

### 2. Message Bus (`message_bus.py`)
- Central registry for all agents
- Broadcast messaging
- Direct agent-to-agent routing
- Topic-based pub/sub system

### 3. AI Agents (`ai_agent.py`)
- OpenAI-integrated agents for AI-powered communication
- Specialized agent types (CodeWriter, CodeReviewer, TestWriter)
- Conversation history and context management
- Uses API key from `config.py` automatically

### 4. Configuration (`config.py`)
- Model and temperature settings
- API key defaults (set via environment variable `OPENAI_API_KEY`)
- Configurable model: default is `gpt-4o-mini`

### 5. Examples
- **`example_conversation.py`**: Basic agent communication patterns
- **`cursor_agents_example.py`**: AI agents collaborating like Cursor agents would

## How Cursor Agents Use This

This system enables multiple AI agents (like Cursor's coding assistants) to collaborate asynchronously:

### Use Case 1: Multi-Agent Code Development
```python
from build_my_startup.ai_agent import CodeWriterAgent, CodeReviewAgent
from build_my_startup.message_bus import MessageBus

bus = MessageBus()
writer = CodeWriterAgent(name="Writer", message_bus=bus)
reviewer = CodeReviewAgent(name="Reviewer", message_bus=bus)

# Writer generates code → automatically sends to Reviewer
# Reviewer provides feedback asynchronously
# Both agents work concurrently without blocking
```

### Use Case 2: Parallel Task Processing
Multiple agents work on different parts simultaneously:
- Frontend agent → UI components
- Backend agent → API endpoints  
- DevOps agent → Infrastructure setup

All communicate through the message bus without blocking each other.

### Use Case 3: Agent Brainstorming
Agents discuss and refine solutions together asynchronously:
- One agent proposes architecture
- Another suggests optimizations
- Third considers UX implications
- All exchange ideas in parallel

## Usage

### Basic Agent Communication

```python
import asyncio
from build_my_startup.agent import Agent

async def main():
    alice = Agent(name="Alice")
    bob = Agent(name="Bob")
    
    alice.running = True
    bob.running = True
    
    tasks = [alice.receive_messages(), bob.receive_messages()]
    
    async def chat():
        await alice.send_message(bob, "Hello!")
        await asyncio.sleep(1)
        alice.running = False
        bob.running = False
    
    await asyncio.gather(*tasks, chat())

asyncio.run(main())
```

### AI Agents (Ready to Use)

```python
from build_my_startup.ai_agent import CodeWriterAgent, CodeReviewAgent
from build_my_startup.message_bus import MessageBus

bus = MessageBus()

# API key is automatically loaded from config.py
writer = CodeWriterAgent(name="CodeWriter", message_bus=bus)
reviewer = CodeReviewAgent(name="Reviewer", message_bus=bus)

# Agents communicate asynchronously
await bus.send_to_agent(
    writer.agent_id,
    reviewer.agent_id,
    "Review this code: ...",
    "code_review_request"
)
```

## Running Examples

```bash
# Basic agent communication
python example_conversation.py

# AI agent collaboration (uses OpenAI API with configured key)
python cursor_agents_example.py
```

The API key is already configured in `config.py`, so agents will use real OpenAI API calls.

## Configuration

The OpenAI API key is stored in `config.py`. The system will:
1. Use the key from `config.py` (already set)
2. Override with `OPENAI_API_KEY` environment variable if set
3. Fall back to mock responses if no key available

To use a different key, either:
- Edit `config.py` directly
- Set `OPENAI_API_KEY` environment variable
- Pass `api_key` parameter when creating agents

## Architecture

- **Asyncio-based**: Uses Python's built-in asyncio for truly asynchronous communication
- **Queue-based messaging**: Each agent has an async queue for incoming messages
- **Non-blocking**: All operations are non-blocking and concurrent
- **Scalable**: Can handle many agents communicating simultaneously

## Key Benefits for Cursor Agents

1. **Non-blocking**: Agents never wait for each other - true async communication
2. **Role Specialization**: Each agent can have a different AI prompt/role
3. **Scalability**: Add more agents without performance issues
4. **Flexibility**: Agents can broadcast, send directly, or use pub/sub
5. **Context Preservation**: Each agent maintains conversation history
6. **Ready to Use**: API key pre-configured, works out of the box

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# That's it! API key is already in config.py
# Run examples immediately
python cursor_agents_example.py
```

## Extending the System

1. **Custom Message Handlers**: Override `message_handler` in Agent class
2. **Message Types**: Use `message_type` field for routing different message categories
3. **Persistent Storage**: Add database or file storage for message history
4. **Network Communication**: Extend to support agents across different processes/machines using websockets or HTTP

## Security Note

The `config.py` file contains the API key and is included in `.gitignore` to prevent accidental commits. If you need to share this project, make sure to:
- Keep `config.py` out of version control
- Use `config.py.template` as a guide for others
- Or use environment variables for deployment
