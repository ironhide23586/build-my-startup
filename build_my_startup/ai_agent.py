"""
AI Agent that integrates with OpenAI and uses the messaging system.
"""
import asyncio
import os
from typing import Optional, Dict, Any
from .agent import Agent, Message
from .message_bus import MessageBus
from .config import OPENAI_API_KEY, DEFAULT_MODEL, AGENT_DEFAULT_TEMPERATURE

# Try to import OpenAI - make it optional for basic usage
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not installed. Install with: pip install openai")


class AIAgent(Agent):
    """An AI-powered agent that uses OpenAI for generating responses."""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        role: str = "assistant",
        model: str = None,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        message_bus: Optional[MessageBus] = None
    ):
        super().__init__(agent_id=agent_id, name=name)
        self.role = role
        self.model = model or DEFAULT_MODEL
        # Use provided key, env var, or config default (in that order)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        self.system_prompt = system_prompt or f"You are a helpful {role} agent."
        self.message_bus = message_bus
        self.conversation_history: list = []
        
        if OPENAI_AVAILABLE and self.api_key:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            print(f"[{self.name}] OpenAI client not available (no API key or library)")
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a response using OpenAI."""
        if not self.client:
            return f"[Mock Response from {self.name}]: I would respond to: {prompt}"
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add context if provided
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        # Add conversation history
        messages.extend(self.conversation_history[-5:])  # Last 5 exchanges
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=AGENT_DEFAULT_TEMPERATURE
            )
            result = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": result})
            
            return result
        except Exception as e:
            return f"[Error generating response: {str(e)}]"
    
    async def handle_message_with_ai(self, message: Message) -> None:
        """Handle incoming message and generate AI response."""
        print(f"[{self.name}] 🤖 Processing message: {message.content}")
        
        # Generate response using AI
        context = f"Message from {message.sender_id} of type {message.message_type}"
        response = await self.generate_response(
            prompt=str(message.content),
            context=context
        )
        
        print(f"[{self.name}] 💭 Generated response: {response[:100]}...")
        
        # Respond back if it's a question/conversation
        if message.message_type in ["question", "query", "default"]:
            if self.message_bus:
                await self.message_bus.send_to_agent(
                    self.agent_id,
                    message.sender_id,
                    response,
                    "ai_response"
                )
            else:
                # Direct response if we have sender reference
                print(f"[{self.name}] Would respond to {message.sender_id}: {response[:50]}...")
    
    async def collaborate_task(self, task: str, collaborators: list) -> Dict[str, Any]:
        """Work on a task by coordinating with other agents."""
        print(f"[{self.name}] 📋 Starting collaboration on: {task}")
        
        # Generate initial plan
        planning_prompt = f"Create a plan for: {task}. Consider collaboration with other agents."
        plan = await self.generate_response(planning_prompt)
        
        # Broadcast plan to collaborators
        if self.message_bus:
            await self.message_bus.broadcast_message(
                self.agent_id,
                {"type": "plan", "content": plan, "task": task},
                "collaboration_plan"
            )
        
        return {
            "agent": self.name,
            "task": task,
            "plan": plan,
            "collaborators": [c.name for c in collaborators]
        }


class CodeReviewAgent(AIAgent):
    """Specialized agent for code review."""
    
    def __init__(self, **kwargs):
        # Allow system_prompt to be overridden via kwargs
        default_system_prompt = """You are an expert code reviewer. 
        Review code carefully, identify bugs, suggest improvements, and check for best practices.
        Provide clear, actionable feedback."""
        system_prompt = kwargs.pop('system_prompt', default_system_prompt)
        super().__init__(
            role="code_reviewer",
            system_prompt=system_prompt,
            **kwargs
        )
    
    async def review_code(self, code: str, author_id: str) -> str:
        """Review code and provide feedback."""
        prompt = f"Please review this code and provide feedback:\n\n```\n{code}\n```"
        review = await self.generate_response(prompt)
        
        if self.message_bus:
            await self.message_bus.send_to_agent(
                self.agent_id,
                author_id,
                review,
                "code_review"
            )
        
        return review


class CodeWriterAgent(AIAgent):
    """Specialized agent for writing code."""
    
    def __init__(self, **kwargs):
        # Allow system_prompt to be overridden via kwargs
        default_system_prompt = """You are an expert software developer. 
        Write clean, efficient, well-documented code.
        Follow best practices and coding standards."""
        system_prompt = kwargs.pop('system_prompt', default_system_prompt)
        super().__init__(
            role="developer",
            system_prompt=system_prompt,
            **kwargs
        )
    
    async def write_code(self, requirement: str) -> str:
        """Generate code based on requirements."""
        prompt = f"Write code for: {requirement}\n\nProvide complete, working code."
        code = await self.generate_response(prompt)
        return code


class TestWriterAgent(AIAgent):
    """Specialized agent for writing tests."""
    
    def __init__(self, **kwargs):
        # Allow system_prompt to be overridden via kwargs
        default_system_prompt = """You are an expert QA engineer. 
        Write comprehensive test cases, including edge cases and error handling."""
        system_prompt = kwargs.pop('system_prompt', default_system_prompt)
        super().__init__(
            role="qa_engineer",
            system_prompt=system_prompt,
            **kwargs
        )
    
    async def write_tests(self, code: str, language: str = "python") -> str:
        """Generate tests for given code."""
        prompt = f"Write comprehensive tests for this {language} code:\n\n```\n{code}\n```"
        tests = await self.generate_response(prompt)
        return tests

