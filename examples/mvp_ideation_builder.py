"""
MVP Ideation and Builder - Use AI agents to ideate, plan, build, and deliver an MVP quickly.
"""
import asyncio
from build_my_startup.message_bus import MessageBus
from build_my_startup.ai_agent import AIAgent, CodeWriterAgent, CodeReviewAgent
from build_my_startup.agent import Message
from build_my_startup.workflow_utils import TaskTracker, wait_for_completion


async def build_mvp():
    """
    Complete workflow: Ideate → Plan → Build → Review → Deliver
    """
    print("=" * 70)
    print("🚀 MVP IDEATION & BUILD SYSTEM")
    print("=" * 70)
    print("\nUsing AI agents to ideate, plan, build, and deliver an MVP\n")
    
    bus = MessageBus()
    
    # Create specialized agents
    ideator = AIAgent(
        name="Ideator",
        role="product_innovator",
        message_bus=bus,
        system_prompt="""You are a creative product innovator. Generate exciting, 
        feasible MVP ideas that can be built quickly. Think simple but impactful."""
    )
    
    architect = AIAgent(
        name="Architect",
        role="technical_architect",
        message_bus=bus,
        system_prompt="""You are a technical architect. Design simple, elegant 
        architectures for MVPs. Focus on minimal viable product - what's the simplest 
        that works?"""
    )
    
    builder = CodeWriterAgent(
        name="Builder",
        message_bus=bus,
        system_prompt="""You are an expert full-stack developer. Write clean, 
        working code quickly. Prioritize getting it working over perfection."""
    )
    
    reviewer = CodeReviewAgent(
        name="Reviewer",
        message_bus=bus,
        system_prompt="""You are a pragmatic code reviewer. Focus on critical issues 
        and quick wins. Be concise and actionable."""
    )
    
    coordinator = AIAgent(
        name="Coordinator",
        role="project_manager",
        message_bus=bus,
        system_prompt="""You coordinate the MVP workflow and ensure deliverables are ready."""
    )
    
    # Register all agents
    all_agents = [ideator, architect, builder, reviewer, coordinator]
    for agent in all_agents:
        bus.register_agent(agent)
        agent.running = True
    
    # Task tracker
    tracker = TaskTracker()
    tracker.create_task("ideation_done")
    tracker.create_task("architecture_done")
    tracker.create_task("code_built")
    tracker.create_task("code_reviewed")
    
    # Store outputs
    mvp_idea = {"content": None}
    architecture = {"content": None}
    code_output = {"content": None}
    review_output = {"content": None}
    
    # Handlers
    async def ideator_handler(message: Message):
        if message.message_type == "ideate_request":
            try:
                print(f"\n💡 [{ideator.name}] Brainstorming MVP ideas...")
                idea = await ideator.generate_response(
                    "Generate a cool, simple MVP idea that can be built in under 100 lines of code. "
                    "Make it practical and useful. Format as: Name: [name] | Description: [description] | "
                    "Features: [3-5 bullet points] | Tech: [technologies]"
                )
                mvp_idea["content"] = idea
                print(f"✅ [{ideator.name}] Generated MVP idea")
                print(f"\n{'='*70}")
                print("💡 MVP IDEA:")
                print(f"{'='*70}")
                print(idea)
                print(f"{'='*70}\n")
                
                tracker.complete_task("ideation_done")
                # Send to architect
                await bus.send_to_agent(
                    ideator.agent_id,
                    architect.agent_id,
                    idea,
                    "design_request"
                )
            except Exception as e:
                print(f"❌ [{ideator.name}] Error: {e}")
                mvp_idea["content"] = f"Error generating idea: {e}"
    
    async def architect_handler(message: Message):
        if message.message_type == "design_request":
            print(f"🏗️  [{architect.name}] Designing architecture...")
            design = await architect.generate_response(
                f"Design a simple architecture for this MVP idea:\n\n{mvp_idea['content']}\n\n"
                "Provide: 1) Component breakdown, 2) Tech stack, 3) File structure, 4) Quick implementation steps."
            )
            architecture["content"] = design
            print(f"✅ [{architect.name}] Architecture designed")
            print(f"\n{'='*70}")
            print("🏗️  ARCHITECTURE:")
            print(f"{'='*70}")
            print(design)
            print(f"{'='*70}\n")
            
            tracker.complete_task("architecture_done")
            # Extract implementation request
            await bus.send_to_agent(
                architect.agent_id,
                builder.agent_id,
                f"Build the MVP based on:\nIdea: {mvp_idea['content']}\n\nArchitecture: {design}",
                "build_request"
            )
    
    async def builder_handler(message: Message):
        if message.message_type == "build_request":
            print(f"🔨 [{builder.name}] Building MVP...")
            code = await builder.write_code(
                f"Build a complete, working MVP based on:\n\nIdea: {mvp_idea['content']}\n\n"
                f"Architecture: {architecture['content']}\n\n"
                "Provide complete, runnable code with any necessary setup instructions."
            )
            code_output["content"] = code
            print(f"✅ [{builder.name}] Code generated ({len(code)} chars)")
            print(f"\n{'='*70}")
            print("🔨 CODE:")
            print(f"{'='*70}")
            print(code[:1000] + ("..." if len(code) > 1000 else ""))
            if len(code) > 1000:
                print(f"\n... ({len(code) - 1000} more chars)")
            print(f"{'='*70}\n")
            
            tracker.complete_task("code_built")
            # Send to reviewer
            await bus.send_to_agent(
                builder.agent_id,
                reviewer.agent_id,
                code,
                "code_review_request"
            )
    
    async def reviewer_handler(message: Message):
        if message.message_type == "code_review_request":
            print(f"🔍 [{reviewer.name}] Reviewing code...")
            review = await reviewer.review_code(str(message.content), builder.agent_id)
            review_output["content"] = review
            print(f"✅ [{reviewer.name}] Review completed ({len(review)} chars)")
            print(f"\n{'='*70}")
            print("🔍 CODE REVIEW:")
            print(f"{'='*70}")
            print(review[:800] + ("..." if len(review) > 800 else ""))
            if len(review) > 800:
                print(f"\n... ({len(review) - 800} more chars)")
            print(f"{'='*70}\n")
            
            tracker.complete_task("code_reviewed")
    
    # Assign handlers
    ideator.message_handler = ideator_handler
    architect.message_handler = architect_handler
    builder.message_handler = builder_handler
    reviewer.message_handler = reviewer_handler
    
    # Start message processing
    agent_tasks = [agent.receive_messages() for agent in all_agents]
    message_processing = asyncio.gather(*agent_tasks)
    
    # Run workflow
    async def run_mvp_workflow():
        await asyncio.sleep(0.3)  # Let agents initialize
        
        print("📋 Starting MVP ideation workflow...\n")
        
        # Step 1: Ideate
        await bus.send_to_agent(
            coordinator.agent_id,
            ideator.agent_id,
            "Generate a cool MVP idea",
            "ideate_request"
        )
        
        # Wait for completion
        print("\n⏳ Waiting for MVP workflow to complete...")
        completed = await wait_for_completion(
            all_agents,
            task_tracker=tracker,
            task_ids=["ideation_done", "architecture_done", "code_built", "code_reviewed"],
            timeout=120.0,
            poll_interval=0.5,
            show_progress=True
        )
        
        if completed:
            # Give a moment for any final processing
            await asyncio.sleep(1)
            
            print("\n" + "=" * 70)
            print("✅ MVP WORKFLOW COMPLETED!")
            print("=" * 70)
            
            # Wait a bit more if content is still missing
            if not mvp_idea["content"] or not architecture["content"] or not code_output["content"]:
                print("\n⏳ Waiting for final content...")
                for _ in range(30):  # Wait up to 15 more seconds
                    await asyncio.sleep(0.5)
                    if mvp_idea["content"] and (not code_output["content"] or architecture["content"]):
                        break
            
            # Save deliverables
            await save_deliverables(mvp_idea["content"], architecture["content"], 
                                  code_output["content"], review_output["content"])
            
            print("\n📦 Deliverables saved to:")
            print("  - mvp_idea.md")
            print("  - mvp_architecture.md")
            print("  - mvp_code.py")
            print("  - mvp_review.md")
            print("\n🎉 MVP ready to deploy!")
        else:
            print("\n⚠️  Workflow timed out (partial results may be available)")
        
        # Stop agents
        for agent in all_agents:
            agent.running = False
    
    await asyncio.gather(message_processing, run_mvp_workflow())


async def save_deliverables(idea, architecture, code, review):
    """Save MVP deliverables to files."""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save idea
    with open("mvp_idea.md", "w") as f:
        f.write(f"# MVP Idea\n\n")
        f.write(f"Generated: {timestamp}\n\n")
        f.write(idea if idea else "Idea generation in progress...")
    
    # Save architecture
    with open("mvp_architecture.md", "w") as f:
        f.write(f"# MVP Architecture\n\n")
        f.write(f"Generated: {timestamp}\n\n")
        f.write(architecture if architecture else "Architecture design in progress...")
    
    # Save code
    with open("mvp_code.py", "w") as f:
        idea_name = idea.split("|")[0] if idea and "|" in idea else "MVP"
        f.write(f'"""\nMVP Code\nGenerated: {timestamp}\n')
        f.write(f'Idea: {idea_name if idea else "MVP"}\n"""\n\n')
        if code:
            # Extract code blocks if present
            if "```" in code:
                # Try to extract Python code
                parts = code.split("```")
                for i, part in enumerate(parts):
                    if "python" in part.lower() or i > 0:
                        code_block = parts[i].split("\n", 1)[-1] if "\n" in parts[i] else parts[i]
                        if code_block.strip():
                            f.write(code_block)
                            break
                else:
                    f.write(code)
            else:
                f.write(code)
    
    # Save review
    with open("mvp_review.md", "w") as f:
        f.write(f"# Code Review\n\n")
        f.write(f"Generated: {timestamp}\n\n")
        f.write(review if review else "Code review in progress...")


if __name__ == "__main__":
    print("Starting MVP ideation and build system...\n")
    asyncio.run(build_mvp())

