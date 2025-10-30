"""
AI Integration Tools - Support for latest models from OpenAI, Claude, and AWS.

All tools follow rigid JSON contracts with structured inputs/outputs.
"""
import os
import json
from typing import Dict, List, Optional, Any
from .tool_system import ToolResult, ToolSchema, ToolParameter, ToolCategory, TOOL_REGISTRY


# ============================================================================
# LATEST MODEL CONFIGURATIONS
# ============================================================================

LATEST_MODELS = {
    "openai": {
        "gpt-4o": {
            "description": "GPT-4o - Latest multimodal model (text + vision)",
            "max_tokens": 128000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015
        },
        "gpt-4o-mini": {
            "description": "GPT-4o Mini - Fast and affordable",
            "max_tokens": 128000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.00015,
            "cost_per_1k_output": 0.0006
        },
        "gpt-4-turbo": {
            "description": "GPT-4 Turbo - Latest GPT-4 with 128K context",
            "max_tokens": 128000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.01,
            "cost_per_1k_output": 0.03
        },
        "o1-preview": {
            "description": "O1 Preview - Advanced reasoning model",
            "max_tokens": 128000,
            "supports_vision": False,
            "supports_function_calling": False,
            "cost_per_1k_input": 0.015,
            "cost_per_1k_output": 0.06
        },
        "o1-mini": {
            "description": "O1 Mini - Efficient reasoning model",
            "max_tokens": 128000,
            "supports_vision": False,
            "supports_function_calling": False,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.012
        }
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "description": "Claude 3.5 Sonnet - Latest, most capable",
            "max_tokens": 200000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015
        },
        "claude-3-opus-20240229": {
            "description": "Claude 3 Opus - Most intelligent",
            "max_tokens": 200000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.015,
            "cost_per_1k_output": 0.075
        },
        "claude-3-sonnet-20240229": {
            "description": "Claude 3 Sonnet - Balanced performance",
            "max_tokens": 200000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015
        },
        "claude-3-haiku-20240307": {
            "description": "Claude 3 Haiku - Fast and affordable",
            "max_tokens": 200000,
            "supports_vision": True,
            "supports_function_calling": True,
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125
        }
    },
    "aws": {
        "bedrock-claude-3-5-sonnet": {
            "description": "Claude 3.5 Sonnet via AWS Bedrock",
            "max_tokens": 200000,
            "supports_vision": True,
            "supports_function_calling": True,
            "region": "us-east-1"
        },
        "bedrock-claude-3-opus": {
            "description": "Claude 3 Opus via AWS Bedrock",
            "max_tokens": 200000,
            "supports_vision": True,
            "supports_function_calling": True,
            "region": "us-east-1"
        },
        "bedrock-titan-text": {
            "description": "Amazon Titan Text via AWS Bedrock",
            "max_tokens": 32000,
            "supports_vision": False,
            "supports_function_calling": False,
            "region": "us-east-1"
        }
    }
}


# ============================================================================
# OPENAI INTEGRATION
# ============================================================================

def call_openai_chat(
    prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None
) -> ToolResult:
    """Call OpenAI Chat Completion API with latest models."""
    
    try:
        import openai
        from build_my_startup.config import OPENAI_API_KEY
        
        # Use provided API key or config
        api_key = api_key or os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if not api_key:
            return ToolResult(
                success=False,
                data={},
                errors=["OpenAI API key not found"],
                warnings=[],
                metadata={"model": model}
            )
        
        openai.api_key = api_key
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Call API
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        return ToolResult(
            success=True,
            data={
                "content": content,
                "model": model,
                "tokens_used": usage.total_tokens,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "finish_reason": response.choices[0].finish_reason
            },
            errors=[],
            warnings=[],
            metadata={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model_info": LATEST_MODELS["openai"].get(model, {})
            }
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"OpenAI API call failed: {str(e)}"],
            warnings=[],
            metadata={"model": model}
        )


def call_openai_vision(
    prompt: str,
    image_url: str,
    model: str = "gpt-4o",
    max_tokens: int = 4096,
    api_key: Optional[str] = None
) -> ToolResult:
    """Call OpenAI Vision API for image analysis."""
    
    try:
        import openai
        from build_my_startup.config import OPENAI_API_KEY
        
        api_key = api_key or os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if not api_key:
            return ToolResult(
                success=False,
                data={},
                errors=["OpenAI API key not found"],
                warnings=[],
                metadata={"model": model}
            )
        
        openai.api_key = api_key
        
        # Vision API call
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        return ToolResult(
            success=True,
            data={
                "content": content,
                "model": model,
                "tokens_used": usage.total_tokens,
                "image_url": image_url
            },
            errors=[],
            warnings=[],
            metadata={"supports_vision": True}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"OpenAI Vision API call failed: {str(e)}"],
            warnings=[],
            metadata={"model": model}
        )


# ============================================================================
# CLAUDE (ANTHROPIC) INTEGRATION
# ============================================================================

def call_claude_chat(
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096,
    temperature: float = 0.3,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None
) -> ToolResult:
    """Call Claude API with latest models."""
    
    try:
        import anthropic
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                data={},
                errors=["Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."],
                warnings=[],
                metadata={"model": model}
            )
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build message
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        # Call API
        response = client.messages.create(**kwargs)
        
        content = response.content[0].text
        usage = response.usage
        
        return ToolResult(
            success=True,
            data={
                "content": content,
                "model": model,
                "tokens_used": usage.input_tokens + usage.output_tokens,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "stop_reason": response.stop_reason
            },
            errors=[],
            warnings=[],
            metadata={
                "temperature": temperature,
                "model_info": LATEST_MODELS["anthropic"].get(model, {})
            }
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Claude API call failed: {str(e)}"],
            warnings=["Install anthropic package: pip install anthropic"],
            metadata={"model": model}
        )


def call_claude_vision(
    prompt: str,
    image_base64: str,
    media_type: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096,
    api_key: Optional[str] = None
) -> ToolResult:
    """Call Claude Vision API for image analysis."""
    
    try:
        import anthropic
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                data={},
                errors=["Anthropic API key not found"],
                warnings=[],
                metadata={"model": model}
            )
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Vision API call
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        content = response.content[0].text
        usage = response.usage
        
        return ToolResult(
            success=True,
            data={
                "content": content,
                "model": model,
                "tokens_used": usage.input_tokens + usage.output_tokens,
                "media_type": media_type
            },
            errors=[],
            warnings=[],
            metadata={"supports_vision": True}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Claude Vision API call failed: {str(e)}"],
            warnings=[],
            metadata={"model": model}
        )


# ============================================================================
# AWS BEDROCK INTEGRATION
# ============================================================================

def call_aws_bedrock(
    prompt: str,
    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
    max_tokens: int = 4096,
    temperature: float = 0.3,
    region: str = "us-east-1",
    system_prompt: Optional[str] = None
) -> ToolResult:
    """Call AWS Bedrock with Claude or other models."""
    
    try:
        import boto3
        
        # Create Bedrock client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
        
        # Build request body (format varies by model)
        if "claude" in model_id:
            # Claude format
            messages = [{"role": "user", "content": prompt}]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                body["system"] = system_prompt
            
        else:
            # Generic format
            body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        
        # Call API
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract content (format varies by model)
        if "claude" in model_id:
            content = response_body['content'][0]['text']
            usage = response_body.get('usage', {})
        else:
            content = response_body.get('completion', response_body.get('output', ''))
            usage = {}
        
        return ToolResult(
            success=True,
            data={
                "content": content,
                "model_id": model_id,
                "region": region,
                "usage": usage
            },
            errors=[],
            warnings=[],
            metadata={"temperature": temperature}
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            errors=[f"AWS Bedrock call failed: {str(e)}"],
            warnings=["Ensure AWS credentials are configured: aws configure"],
            metadata={"model_id": model_id, "region": region}
        )


# ============================================================================
# MODEL SELECTION & ROUTING
# ============================================================================

def select_best_model(
    task_type: str,
    budget: str = "medium",
    requires_vision: bool = False,
    requires_function_calling: bool = False,
    provider_preference: Optional[str] = None
) -> ToolResult:
    """Select the best AI model for a task based on requirements."""
    
    task_recommendations = {
        "code_generation": {
            "low_budget": "gpt-4o-mini",
            "medium_budget": "gpt-4o",
            "high_budget": "claude-3-5-sonnet-20241022"
        },
        "code_review": {
            "low_budget": "gpt-4o-mini",
            "medium_budget": "claude-3-5-sonnet-20241022",
            "high_budget": "claude-3-opus-20240229"
        },
        "reasoning": {
            "low_budget": "o1-mini",
            "medium_budget": "o1-preview",
            "high_budget": "claude-3-opus-20240229"
        },
        "vision": {
            "low_budget": "gpt-4o-mini",
            "medium_budget": "gpt-4o",
            "high_budget": "claude-3-5-sonnet-20241022"
        },
        "general": {
            "low_budget": "gpt-4o-mini",
            "medium_budget": "gpt-4o",
            "high_budget": "claude-3-5-sonnet-20241022"
        }
    }
    
    recommendations = task_recommendations.get(task_type, task_recommendations["general"])
    recommended_model = recommendations.get(budget, recommendations["medium_budget"])
    
    # Check vision requirement
    if requires_vision:
        provider = "openai" if "gpt" in recommended_model or "o1" in recommended_model else "anthropic"
        model_info = LATEST_MODELS[provider].get(recommended_model, {})
        if not model_info.get("supports_vision"):
            # Switch to vision-capable model
            if budget == "low_budget":
                recommended_model = "gpt-4o-mini"
            else:
                recommended_model = "gpt-4o"
    
    # Determine provider
    if "gpt" in recommended_model or "o1" in recommended_model:
        provider = "openai"
    elif "claude" in recommended_model:
        provider = "anthropic"
    elif "bedrock" in recommended_model:
        provider = "aws"
    else:
        provider = "openai"
    
    if provider_preference and provider_preference != provider:
        # Try to find alternative in preferred provider
        if provider_preference == "anthropic" and budget in ["medium_budget", "high_budget"]:
            recommended_model = "claude-3-5-sonnet-20241022"
            provider = "anthropic"
        elif provider_preference == "openai":
            recommended_model = "gpt-4o" if budget != "low_budget" else "gpt-4o-mini"
            provider = "openai"
    
    model_info = LATEST_MODELS[provider].get(recommended_model, {})
    
    return ToolResult(
        success=True,
        data={
            "recommended_model": recommended_model,
            "provider": provider,
            "model_info": model_info,
            "task_type": task_type,
            "budget": budget
        },
        errors=[],
        warnings=[],
        metadata={
            "requires_vision": requires_vision,
            "requires_function_calling": requires_function_calling
        }
    )


def get_model_info(model_name: str) -> ToolResult:
    """Get detailed information about a model."""
    
    for provider, models in LATEST_MODELS.items():
        if model_name in models:
            model_info = models[model_name]
            return ToolResult(
                success=True,
                data={
                    "model": model_name,
                    "provider": provider,
                    "description": model_info.get("description", ""),
                    "max_tokens": model_info.get("max_tokens", 0),
                    "supports_vision": model_info.get("supports_vision", False),
                    "supports_function_calling": model_info.get("supports_function_calling", False),
                    "cost_per_1k_input": model_info.get("cost_per_1k_input"),
                    "cost_per_1k_output": model_info.get("cost_per_1k_output")
                },
                errors=[],
                warnings=[],
                metadata={"provider": provider}
            )
    
    return ToolResult(
        success=False,
        data={},
        errors=[f"Model '{model_name}' not found in registry"],
        warnings=[],
        metadata={"searched_providers": list(LATEST_MODELS.keys())}
    )


def list_available_models(
    provider: Optional[str] = None,
    supports_vision: Optional[bool] = None,
    max_budget_per_1k: Optional[float] = None
) -> ToolResult:
    """List all available AI models with optional filtering."""
    
    models_list = []
    
    providers_to_check = [provider] if provider else list(LATEST_MODELS.keys())
    
    for prov in providers_to_check:
        if prov not in LATEST_MODELS:
            continue
        
        for model_name, model_info in LATEST_MODELS[prov].items():
            # Apply filters
            if supports_vision is not None:
                if model_info.get("supports_vision") != supports_vision:
                    continue
            
            if max_budget_per_1k is not None:
                cost = model_info.get("cost_per_1k_output", float('inf'))
                if cost > max_budget_per_1k:
                    continue
            
            models_list.append({
                "model": model_name,
                "provider": prov,
                "description": model_info.get("description", ""),
                "max_tokens": model_info.get("max_tokens", 0),
                "supports_vision": model_info.get("supports_vision", False),
                "cost_per_1k_output": model_info.get("cost_per_1k_output")
            })
    
    return ToolResult(
        success=True,
        data={
            "models": models_list,
            "count": len(models_list),
            "providers": list(set(m["provider"] for m in models_list))
        },
        errors=[],
        warnings=[],
        metadata={
            "filtered_by": {
                "provider": provider,
                "supports_vision": supports_vision,
                "max_budget": max_budget_per_1k
            }
        }
    )


# ============================================================================
# REGISTER AI TOOLS
# ============================================================================

TOOL_REGISTRY.register(
    ToolSchema(
        name="call_openai_chat",
        category=ToolCategory.AI_INTEGRATION,
        description="Call OpenAI Chat Completion API (latest models: gpt-4o, gpt-4o-mini, o1-preview, o1-mini)",
        parameters=[
            ToolParameter("prompt", "string", "User prompt/question"),
            ToolParameter("model", "string", "Model to use", required=False, default="gpt-4o-mini", 
                         enum=list(LATEST_MODELS["openai"].keys())),
            ToolParameter("temperature", "number", "Sampling temperature 0-2", required=False, default=0.3),
            ToolParameter("max_tokens", "number", "Maximum tokens to generate", required=False, default=4096),
            ToolParameter("system_prompt", "string", "System prompt (optional)", required=False),
            ToolParameter("api_key", "string", "OpenAI API key (optional, uses config if not provided)", required=False)
        ],
        returns={
            "success": "Whether API call succeeded",
            "data": "Response content, tokens used, model info",
            "errors": "API errors"
        },
        examples=['{"prompt": "Explain async in Python", "model": "gpt-4o-mini"}']
    ),
    call_openai_chat
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="call_openai_vision",
        category=ToolCategory.AI_INTEGRATION,
        description="Call OpenAI Vision API for image analysis (gpt-4o, gpt-4o-mini, gpt-4-turbo)",
        parameters=[
            ToolParameter("prompt", "string", "Question about the image"),
            ToolParameter("image_url", "string", "URL or base64 data URL of image"),
            ToolParameter("model", "string", "Vision model to use", required=False, default="gpt-4o"),
            ToolParameter("max_tokens", "number", "Maximum tokens", required=False, default=4096),
            ToolParameter("api_key", "string", "OpenAI API key (optional)", required=False)
        ],
        returns={
            "success": "Whether vision analysis succeeded",
            "data": "Analysis content, tokens used, image info",
            "errors": "API errors"
        },
        examples=['{"prompt": "What is in this image?", "image_url": "https://example.com/image.jpg", "model": "gpt-4o"}']
    ),
    call_openai_vision
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="call_claude_chat",
        category=ToolCategory.AI_INTEGRATION,
        description="Call Claude API (latest: claude-3-5-sonnet-20241022, claude-3-opus, claude-3-haiku)",
        parameters=[
            ToolParameter("prompt", "string", "User prompt/question"),
            ToolParameter("model", "string", "Claude model to use", required=False, default="claude-3-5-sonnet-20241022",
                         enum=list(LATEST_MODELS["anthropic"].keys())),
            ToolParameter("max_tokens", "number", "Maximum tokens", required=False, default=4096),
            ToolParameter("temperature", "number", "Sampling temperature", required=False, default=0.3),
            ToolParameter("system_prompt", "string", "System prompt (optional)", required=False),
            ToolParameter("api_key", "string", "Anthropic API key (optional)", required=False)
        ],
        returns={
            "success": "Whether API call succeeded",
            "data": "Response content, tokens used, stop reason",
            "errors": "API errors",
            "warnings": "Setup instructions if needed"
        },
        examples=['{"prompt": "Explain async in Python", "model": "claude-3-5-sonnet-20241022"}']
    ),
    call_claude_chat
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="call_claude_vision",
        category=ToolCategory.AI_INTEGRATION,
        description="Call Claude Vision API for image analysis",
        parameters=[
            ToolParameter("prompt", "string", "Question about the image"),
            ToolParameter("image_base64", "string", "Base64-encoded image data"),
            ToolParameter("media_type", "string", "Image media type (image/jpeg, image/png, etc.)"),
            ToolParameter("model", "string", "Claude vision model", required=False, default="claude-3-5-sonnet-20241022"),
            ToolParameter("max_tokens", "number", "Maximum tokens", required=False, default=4096),
            ToolParameter("api_key", "string", "Anthropic API key (optional)", required=False)
        ],
        returns={
            "success": "Whether vision analysis succeeded",
            "data": "Analysis content, tokens used",
            "errors": "API errors"
        },
        examples=['{"prompt": "Describe this image", "image_base64": "iVBORw0KGgo...", "media_type": "image/png"}']
    ),
    call_claude_vision
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="call_aws_bedrock",
        category=ToolCategory.AI_INTEGRATION,
        description="Call AWS Bedrock with Claude or Amazon models",
        parameters=[
            ToolParameter("prompt", "string", "User prompt"),
            ToolParameter("model_id", "string", "Bedrock model ID", required=False, default="anthropic.claude-3-5-sonnet-20241022-v2:0"),
            ToolParameter("max_tokens", "number", "Maximum tokens", required=False, default=4096),
            ToolParameter("temperature", "number", "Sampling temperature", required=False, default=0.3),
            ToolParameter("region", "string", "AWS region", required=False, default="us-east-1"),
            ToolParameter("system_prompt", "string", "System prompt (optional)", required=False)
        ],
        returns={
            "success": "Whether Bedrock call succeeded",
            "data": "Response content, model info, usage",
            "errors": "API errors",
            "warnings": "AWS setup instructions if needed"
        },
        examples=['{"prompt": "Explain Python decorators", "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"}']
    ),
    call_aws_bedrock
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="select_best_model",
        category=ToolCategory.AI_INTEGRATION,
        description="Automatically select the best AI model for a task based on requirements and budget",
        parameters=[
            ToolParameter("task_type", "string", "Type of task", enum=["code_generation", "code_review", "reasoning", "vision", "general"]),
            ToolParameter("budget", "string", "Budget level", required=False, default="medium", enum=["low_budget", "medium_budget", "high_budget"]),
            ToolParameter("requires_vision", "boolean", "Needs vision capabilities", required=False, default=False),
            ToolParameter("requires_function_calling", "boolean", "Needs function calling", required=False, default=False),
            ToolParameter("provider_preference", "string", "Preferred provider", required=False, enum=["openai", "anthropic", "aws"])
        ],
        returns={
            "success": "Always true",
            "data": "Recommended model, provider, model info, task info",
            "metadata": "Requirements used for selection"
        },
        examples=['{"task_type": "code_generation", "budget": "medium_budget", "requires_vision": false}']
    ),
    select_best_model
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="get_model_info",
        category=ToolCategory.AI_INTEGRATION,
        description="Get detailed information about a specific AI model",
        parameters=[
            ToolParameter("model_name", "string", "Full model name")
        ],
        returns={
            "success": "Whether model was found",
            "data": "Model details (provider, capabilities, costs, context length)",
            "errors": "Model not found error if applicable"
        },
        examples=['{"model_name": "gpt-4o"}']
    ),
    get_model_info
)

TOOL_REGISTRY.register(
    ToolSchema(
        name="list_available_models",
        category=ToolCategory.AI_INTEGRATION,
        description="List all available AI models with optional filtering",
        parameters=[
            ToolParameter("provider", "string", "Filter by provider", required=False, enum=["openai", "anthropic", "aws"]),
            ToolParameter("supports_vision", "boolean", "Filter by vision support", required=False),
            ToolParameter("max_budget_per_1k", "number", "Maximum cost per 1K tokens", required=False)
        ],
        returns={
            "success": "Always true",
            "data": "List of models with details, count, providers",
            "metadata": "Filters applied"
        },
        examples=['{"provider": "openai", "supports_vision": true}']
    ),
    list_available_models
)


# ============================================================================
# MODEL COMPARISON & COST ESTIMATION
# ============================================================================

def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str
) -> ToolResult:
    """Estimate cost for an AI API call."""
    
    # Find model
    provider = None
    model_info = None
    
    for prov, models in LATEST_MODELS.items():
        if model in models:
            provider = prov
            model_info = models[model]
            break
    
    if not model_info:
        return ToolResult(
            success=False,
            data={},
            errors=[f"Model '{model}' not found"],
            warnings=[],
            metadata={}
        )
    
    input_cost_per_1k = model_info.get("cost_per_1k_input", 0)
    output_cost_per_1k = model_info.get("cost_per_1k_output", 0)
    
    input_cost = (prompt_tokens / 1000) * input_cost_per_1k
    output_cost = (completion_tokens / 1000) * output_cost_per_1k
    total_cost = input_cost + output_cost
    
    return ToolResult(
        success=True,
        data={
            "total_cost": round(total_cost, 6),
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "model": model,
            "provider": provider
        },
        errors=[],
        warnings=[],
        metadata={
            "cost_per_1k_input": input_cost_per_1k,
            "cost_per_1k_output": output_cost_per_1k
        }
    )


TOOL_REGISTRY.register(
    ToolSchema(
        name="estimate_cost",
        category=ToolCategory.AI_INTEGRATION,
        description="Estimate cost for AI API call based on token usage",
        parameters=[
            ToolParameter("prompt_tokens", "number", "Number of input tokens"),
            ToolParameter("completion_tokens", "number", "Number of output tokens"),
            ToolParameter("model", "string", "Model name")
        ],
        returns={
            "success": "Whether cost was calculated",
            "data": "Total cost, input/output breakdown, token counts",
            "metadata": "Cost rates used"
        },
        examples=['{"prompt_tokens": 1000, "completion_tokens": 500, "model": "gpt-4o-mini"}']
    ),
    estimate_cost
)

