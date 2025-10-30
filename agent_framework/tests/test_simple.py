"""
Simple test - verify agents can generate responses with OpenAI.
"""
import asyncio
from agent_framework.ai_agent import AIAgent, CodeWriterAgent


async def test_agent_generation():
    """Test that an AI agent can generate responses."""
    print("=" * 60)
    print("Testing AI Agent Response Generation")
    print("=" * 60)
    
    # Create a simple agent
    agent = AIAgent(
        name="TestAgent",
        role="assistant",
        system_prompt="You are a helpful test agent. Answer briefly and clearly."
    )
    
    print(f"\nAgent created: {agent.name}")
    print(f"OpenAI client available: {agent.client is not None}")
    print(f"API key configured: {bool(agent.api_key)}")
    
    if agent.client:
        print("\nTesting OpenAI API call...")
        try:
            response = await agent.generate_response(
                "Say hello in one sentence and confirm you're working."
            )
            print(f"\n✅ Response received ({len(response)} chars):")
            print(f"   {response[:200]}...")
            print("\n✅ OpenAI integration working!")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    else:
        print("\n⚠️  No OpenAI client available")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_agent_generation())
    exit(0 if result else 1)

