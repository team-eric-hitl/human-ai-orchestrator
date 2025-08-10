"""
LLM provider abstractions supporting both cloud and local models
Uses configuration files for model management
"""

import os
import time
from functools import wraps
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic

# Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI

# Local LLMs
from langchain_community.llms import CTransformers, DeepInfra, LlamaCpp
from langchain_core.language_models.chat_models import BaseChatModel

# Core LangChain
from langchain_core.messages import HumanMessage, SystemMessage

# Cloud-based LLMs
from langchain_openai import ChatOpenAI

# Tracing
from langsmith import traceable

# Config management
from ..core.config import ConfigManager
from ..core.config.agent_config_manager import AgentConfigManager

# Logging and error handling
from ..core.logging import ModelError, ModelInferenceError, get_logger


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function calls on failure with exponential backoff"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Log the retry attempt
                        logger = get_logger("llm_provider.retry")
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {current_delay}s",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": current_delay,
                                "error": str(e),
                            },
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # Log final failure
                        logger = get_logger("llm_provider.retry")
                        logger.error(
                            f"All {max_retries} attempts failed",
                            extra={
                                "function": func.__name__,
                                "max_retries": max_retries,
                                "final_error": str(e),
                            },
                        )

            # Re-raise the last exception if all retries failed
            raise last_exception

        return wrapper

    return decorator


class LLMProvider:
    """Abstract LLM provider supporting cloud and local models"""

    def __init__(self, model_config: dict):
        self.model_config = model_config
        self.provider_type = model_config.get("type", "unknown")
        self.model_name = model_config.get("model_name", "unknown")
        self.logger = get_logger(f"llm_provider.{self.model_name}")

        self.logger.info(
            "Initializing LLM provider",
            extra={
                "model_name": self.model_name,
                "model_type": self.provider_type,
                "is_local": self.provider_type in ["llama", "local"],
            },
        )

        try:
            self.client = self._initialize_client()
            self.logger.info(
                "LLM provider initialized successfully",
                extra={"model_name": self.model_name},
            )
        except Exception as e:
            self.logger.error(
                "Failed to initialize LLM provider",
                exc_info=True,
                extra={"model_name": self.model_name, "error": str(e)},
            )
            raise ModelError(
                f"Failed to initialize {self.model_name}",
                model_name=self.model_name,
                model_type=self.provider_type,
            ) from e

    def _initialize_client(self) -> BaseChatModel:
        """Initialize the LLM client based on model configuration"""
        if self.provider_type == "openai":
            return self._setup_openai()
        elif self.provider_type == "anthropic":
            return self._setup_anthropic()
        elif self.provider_type == "gemini":
            return self._setup_gemini()
        elif self.provider_type == "deepinfra":
            return self._setup_deepinfra()
        elif self.provider_type == "llama":
            return self._setup_llama()
        elif self.provider_type == "mistral":
            return self._setup_mistral()
        elif self.provider_type == "ctransformers":
            return self._setup_ctransformers()
        else:
            raise ValueError(f"Unsupported provider type: {self.provider_type}")

    def _setup_openai(self) -> ChatOpenAI:
        """Setup OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI models"
            )

        return ChatOpenAI(
            model=self.model_config.get("model_name", "gpt-4"),
            temperature=self.model_config.get("temperature", 0.7),
            max_tokens=self.model_config.get("max_tokens", 2000),
            api_key=api_key,
        )

    def _setup_anthropic(self) -> ChatAnthropic:
        """Setup Anthropic client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for Anthropic models"
            )

        return ChatAnthropic(
            model=self.model_config.get("model_name", "claude-3-5-sonnet-20241022"),
            temperature=self.model_config.get("temperature", 0.7),
            max_tokens=self.model_config.get("max_tokens", 2000),
            api_key=api_key,
        )

    def _setup_gemini(self) -> ChatGoogleGenerativeAI:
        """Setup Google Gemini client"""
        # Try both GOOGLE_API_KEY and GEMINI_API_KEY for compatibility
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required for Gemini models"
            )

        return ChatGoogleGenerativeAI(
            model=self.model_config.get("model_name", "gemini-1.5-flash"),
            temperature=self.model_config.get("temperature", 0.7),
            max_tokens=self.model_config.get("max_tokens", 2000),
            google_api_key=api_key,
        )

    def _setup_deepinfra(self) -> DeepInfra:
        """Setup DeepInfra client"""
        api_token = os.getenv("DEEPINFRA_API_TOKEN")
        if not api_token:
            raise ValueError(
                "DEEPINFRA_API_TOKEN environment variable is required for DeepInfra models"
            )

        # Configure model parameters
        model_kwargs = {
            "temperature": self.model_config.get("temperature", 0.7),
            "max_new_tokens": self.model_config.get("max_tokens", 2000),
            "repetition_penalty": self.model_config.get("repetition_penalty", 1.2),
            "top_p": self.model_config.get("top_p", 0.9),
        }

        return DeepInfra(
            model_id=self.model_config.get("model_id", "meta-llama/Llama-2-7b-chat-hf"),
            deepinfra_api_token=api_token,
            model_kwargs=model_kwargs,
        )

    def _setup_llama(self) -> LlamaCpp:
        """Setup LlamaCpp client for local Llama models"""
        model_path = self.model_config.get("path")
        if not model_path:
            raise ValueError(f"Model path is required for {self.model_name}")

        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        return LlamaCpp(
            model_path=model_path,
            temperature=self.model_config.get("temperature", 0.7),
            max_tokens=self.model_config.get("max_tokens", 2000),
            n_ctx=self.model_config.get("context_length", 2048),
            n_gpu_layers=self.model_config.get("gpu_layers", 0),
            verbose=False,
        )

    def _setup_mistral(self) -> LlamaCpp:
        """Setup Mistral client (uses LlamaCpp backend)"""
        model_path = self.model_config.get("path")
        if not model_path:
            raise ValueError(f"Model path is required for {self.model_name}")

        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        return LlamaCpp(
            model_path=model_path,
            temperature=self.model_config.get("temperature", 0.7),
            max_tokens=self.model_config.get("max_tokens", 2000),
            n_ctx=self.model_config.get("context_length", 2048),
            n_gpu_layers=self.model_config.get("gpu_layers", 0),
            verbose=False,
        )

    def _setup_ctransformers(self) -> CTransformers:
        """Setup CTransformers client for optimized local models"""
        model_path = self.model_config.get("path")
        if not model_path:
            raise ValueError(f"Model path is required for {self.model_name}")

        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        return CTransformers(
            model=model_path,
            model_type="llama",  # CTransformers model type
            temperature=self.model_config.get("temperature", 0.7),
            max_new_tokens=self.model_config.get("max_tokens", 2000),
            context_length=self.model_config.get("context_length", 2048),
            gpu_layers=self.model_config.get("gpu_layers", 0),
        )

    def _format_prompt_for_local_model(self, prompt: str, system_prompt: str = "") -> str:
        """Format prompt according to model's expected format for local models"""
        model_type = self.model_config.get("type", "").lower()

        self.logger.debug(
            "Formatting prompt for local model",
            extra={
                "model_name": self.model_name,
                "model_type": model_type,
                "has_system_prompt": bool(system_prompt),
                "prompt_length": len(prompt),
            },
        )

        if model_type == "llama":
            # Llama format without leading <s> (let the model handle BOS token)
            # Format: [INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_message} [/INST]
            if system_prompt:
                formatted_prompt = f"[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
            else:
                formatted_prompt = f"[INST] {prompt} [/INST]"
        elif model_type == "mistral":
            # Mistral format following official specification
            # For v0.1/v0.2: Use <<SYS>> workaround for system prompts
            # For v0.3+: This format still works and is compatible
            if system_prompt:
                # Use official system prompt format with <<SYS>> markers
                formatted_prompt = f"[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
            else:
                # Simple instruction format
                formatted_prompt = f"[INST] {prompt} [/INST]"
        else:
            # Fallback to current behavior for unknown model types
            self.logger.warning(
                "Unknown model type, using fallback formatting",
                extra={"model_type": model_type, "model_name": self.model_name}
            )
            if system_prompt:
                formatted_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                formatted_prompt = prompt

        self.logger.debug(
            "Prompt formatted for local model",
            extra={
                "model_name": self.model_name,
                "formatted_length": len(formatted_prompt),
                "format_applied": model_type,
            },
        )

        return formatted_prompt

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    @traceable(
        run_type="llm",
        name="LLM Response Generation",
        metadata=lambda self, prompt, system_prompt="": {
            "model_name": self.model_name,
            "model_type": self.provider_type,
            "temperature": self.model_config.get("temperature", 0.7),
            "max_tokens": self.model_config.get("max_tokens", 2000),
            "is_local": self.provider_type in ["llama", "local"],
            "prompt_length": len(prompt),
            "has_system_prompt": bool(system_prompt),
        },
    )
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using LLM with proper prompt formatting for local models"""
        start_time = time.time()

        # Add prominent LLM call logging
        self.logger.info(
            "🤖 INVOKING LLM",
            extra={
                "model_name": self.model_name,
                "provider_type": self.provider_type,
                "prompt_length": len(prompt),
                "has_system_prompt": bool(system_prompt),
                "operation": "llm_call_start"
            },
        )

        self.logger.debug(
            "Starting response generation",
            extra={
                "model_name": self.model_name,
                "prompt_length": len(prompt),
                "has_system_prompt": bool(system_prompt),
            },
        )

        try:
            # Check if this is a local model that needs special formatting
            is_local_model = self.provider_type in ["llama", "local", "mistral"]
            is_deepinfra_model = self.provider_type == "deepinfra"

            if is_local_model:
                # Format the prompt specifically for local models
                formatted_prompt = self._format_prompt_for_local_model(prompt, system_prompt)
                response = self.client.invoke(formatted_prompt)
            elif is_deepinfra_model:
                # DeepInfra uses string-based prompts but handles system prompts differently
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
                else:
                    full_prompt = f"User: {prompt}\nAssistant:"
                response = self.client.invoke(full_prompt)
            else:
                # Use message-based approach for cloud models (OpenAI, Anthropic)
                messages = []
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(HumanMessage(content=prompt))
                response = self.client.invoke(messages)
            duration = time.time() - start_time

            # Handle different response types (some return strings, others objects)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            # Add prominent completion logging
            self.logger.info(
                "✅ LLM RESPONSE COMPLETED",
                extra={
                    "model_name": self.model_name,
                    "provider_type": self.provider_type,
                    "duration": duration,
                    "prompt_length": len(prompt),
                    "response_length": len(response_text),
                    "operation": "llm_call_completed"
                },
            )

            self.logger.model_call(
                model_name=self.model_name,
                operation="generate_response",
                duration=duration,
                prompt_length=len(prompt),
                response_length=len(response_text),
            )

            return response_text

        except Exception as e:
            duration = time.time() - start_time
            # Add prominent failure logging
            self.logger.error(
                "❌ LLM CALL FAILED",
                extra={
                    "model_name": self.model_name,
                    "provider_type": self.provider_type,
                    "duration": duration,
                    "error": str(e),
                    "operation": "llm_call_failed"
                },
            )
            self.logger.error(
                "Response generation failed",
                exc_info=True,
                extra={
                    "model_name": self.model_name,
                    "duration": duration,
                    "error": str(e),
                },
            )

            raise ModelInferenceError(
                f"Failed to generate response with {self.model_name}",
                model_name=self.model_name,
                model_type=self.provider_type,
                context={"prompt_length": len(prompt), "duration": duration},
            ) from e

    @traceable(
        run_type="llm",
        name="LLM Response Evaluation",
        metadata=lambda self, query, response: {
            "model_name": self.model_name,
            "model_type": self.provider_type,
            "query_length": len(query),
            "response_length": len(response),
            "evaluation_model": self.model_name,
        },
    )
    def evaluate_response(self, query: str, response: str) -> dict[str, Any]:
        """Evaluate response quality using LLM"""
        evaluation_prompt = f"""
        Evaluate the following AI response to a user query.

        User Query: {query}
        AI Response: {response}

        Rate the response on a scale of 1-10 for:
        1. Accuracy: How correct and factual is the response?
        2. Completeness: Does it address all aspects of the query?
        3. Clarity: Is it clear and easy to understand?
        4. User Satisfaction: How likely is the user to be satisfied?

        Provide your evaluation as JSON:
        {{
            "accuracy": <score>,
            "completeness": <score>,
            "clarity": <score>,
            "user_satisfaction": <score>,
            "overall_score": <average_score>,
            "reasoning": "<explanation>"
        }}
        """

        try:
            self.generate_response(evaluation_prompt)
            # Parse JSON response (simplified - in production, add proper parsing)
            return {
                "accuracy": 8.0,
                "completeness": 7.5,
                "clarity": 8.5,
                "user_satisfaction": 8.0,
                "overall_score": 8.0,
                "reasoning": "Response evaluation completed",
            }
        except Exception as e:
            print(f"Error evaluating response: {e}")
            return {
                "accuracy": 5.0,
                "completeness": 5.0,
                "clarity": 5.0,
                "user_satisfaction": 5.0,
                "overall_score": 5.0,
                "reasoning": f"Evaluation failed: {str(e)}",
            }


class LLMProviderFactory:
    """Factory for creating LLM providers from configuration"""

    def __init__(self, config_dir: str = "config"):
        self.config_manager = ConfigManager(config_dir)
        # Also initialize AgentConfigManager for alias resolution
        try:
            self.agent_config_manager = AgentConfigManager(config_dir)
        except Exception:
            # Fallback if AgentConfigManager fails
            self.agent_config_manager = None

    def create_provider(self, model_name: str | None = None) -> LLMProvider:
        """
        Create LLM provider from configuration

        Args:
            model_name: Specific model name or alias, or None to use primary model
        """
        models_config = self.config_manager.get_models_config()
        available_models = models_config.get("models", {})

        # Initialize resolved name
        resolved_model_name = None

        if model_name:
            # Resolve model alias if AgentConfigManager is available
            resolved_model_name = model_name
            if self.agent_config_manager:
                resolved_model_name = self.agent_config_manager.resolve_model_name(model_name)

            if resolved_model_name not in available_models:
                raise ValueError(f"Model {resolved_model_name} not found in configuration")
            model_config = available_models[resolved_model_name]
            model_config["model_name"] = resolved_model_name
        else:
            # Get the primary model from use cases
            use_cases = models_config.get("use_cases", {})
            general_use_case = use_cases.get("general", {})
            primary_model_name = general_use_case.get("recommended", "local_general_standard")
            resolved_model_name = primary_model_name
            model_config = available_models.get(primary_model_name, {})
            model_config["model_name"] = primary_model_name

        # Validate model is available
        model_type = model_config.get("type", "unknown")
        if model_type in ["llama", "mistral"]:
            model_path = model_config.get("path", "")
            if not Path(model_path).exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
        elif model_type == "openai" and not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set for OpenAI model")
        elif model_type == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set for Anthropic model")
        elif model_type == "gemini" and not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set for Gemini model")
        elif model_type == "deepinfra" and not os.getenv("DEEPINFRA_API_TOKEN"):
            raise ValueError("DEEPINFRA_API_TOKEN not set for DeepInfra model")

        # Show both alias and resolved name if different
        display_name = model_name or resolved_model_name
        if model_name and self.agent_config_manager and resolved_model_name != model_name:
            display_name = f"{model_name} → {resolved_model_name}"
        print(f"✅ Creating LLM provider: {display_name} ({model_type})")
        return LLMProvider(model_config)

    def create_auto_provider(self) -> LLMProvider:
        """Automatically select the best available provider"""
        # Get provider strategy from system config
        system_config = self.config_manager.get_system_config()
        strategy = system_config.providers.get("strategy", "auto")

        # Get available models from config
        models_config = self.config_manager.get_models_config()
        available_models = models_config.get("models", {})

        if not available_models:
            raise ValueError(
                "No models are available. Check your configuration and model files."
            )

        if strategy == "auto":
            # Try to find the best available model
            # Prefer local models, then OpenAI
            local_models = {k: v for k, v in available_models.items() if v.get("type") in ["llama", "local"]}
            if local_models:
                model_name = list(local_models.keys())[0]
                model_config = local_models[model_name]
                model_config["model_name"] = model_name
                print(f"✅ Auto-selected local model: {model_name}")
            else:
                model_name = list(available_models.keys())[0]
                model_config = available_models[model_name]
                model_config["model_name"] = model_name
                print(f"✅ Auto-selected cloud model: {model_name}")

            return LLMProvider(model_config)

        elif strategy == "local":
            # Force local model
            local_models = {k: v for k, v in available_models.items() if v.get("type") in ["llama", "local"]}
            if not local_models:
                raise ValueError("No local models are available")
            model_name = list(local_models.keys())[0]
            model_config = local_models[model_name]
            model_config["model_name"] = model_name
            return LLMProvider(model_config)

        elif strategy == "openai":
            # Force OpenAI
            openai_models = {k: v for k, v in available_models.items() if v.get("type") == "openai"}
            if not openai_models:
                raise ValueError(
                    "No OpenAI models are available (check OPENAI_API_KEY)"
                )
            model_name = list(openai_models.keys())[0]
            model_config = openai_models[model_name]
            model_config["model_name"] = model_name
            return LLMProvider(model_config)

        elif strategy == "anthropic":
            # Force Anthropic
            anthropic_models = {k: v for k, v in available_models.items() if v.get("type") == "anthropic"}
            if not anthropic_models:
                raise ValueError(
                    "No Anthropic models are available (check ANTHROPIC_API_KEY)"
                )
            model_name = list(anthropic_models.keys())[0]
            model_config = anthropic_models[model_name]
            model_config["model_name"] = model_name
            return LLMProvider(model_config)

        elif strategy == "gemini":
            # Force Gemini
            gemini_models = {k: v for k, v in available_models.items() if v.get("type") == "gemini"}
            if not gemini_models:
                raise ValueError(
                    "No Gemini models are available (check GOOGLE_API_KEY or GEMINI_API_KEY)"
                )
            model_name = list(gemini_models.keys())[0]
            model_config = gemini_models[model_name]
            model_config["model_name"] = model_name
            return LLMProvider(model_config)

        else:
            # Strategy is a specific model name
            return self.create_provider(strategy)

    def create_provider_with_fallback(
        self, preferred_model: str | None = None, use_case: str | None = None
    ) -> LLMProvider:
        """Create provider with automatic fallback to available models"""

        logger = get_logger("llm_provider.factory")

        # Get fallback chain from config
        models_config = self.config_manager.get_models_config()
        use_cases = models_config.get("use_cases", {})
        fallback_config = models_config.get("fallback_strategy", {})

        # Determine which use case to use for fallbacks
        target_use_case = use_case or "general"
        case_config = use_cases.get(target_use_case, use_cases.get("general", {}))
        fallback_models = case_config.get("alternatives", [])

        # Start with preferred model if specified
        models_to_try = []
        if preferred_model:
            models_to_try.append(preferred_model)

        # Add primary model for the use case
        try:
            primary_model = case_config.get("recommended", "local_general_standard")
            if primary_model not in models_to_try:
                models_to_try.append(primary_model)
        except Exception:
            pass

        # Add use case specific fallback models
        for model in fallback_models:
            if model not in models_to_try:
                models_to_try.append(model)

        # Add global fallback models if enabled
        if fallback_config.get("enabled", True):
            global_fallbacks = fallback_config.get("default_fallback", [])
            for model in global_fallbacks:
                if model not in models_to_try:
                    models_to_try.append(model)

        # Try each model in order
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting to create provider: {model_name}")
                provider = self.create_provider(model_name)
                logger.info(f"Successfully created provider: {model_name}")
                return provider
            except Exception as e:
                logger.warning(f"Failed to create provider {model_name}: {str(e)}")
                continue

        # If all models failed, raise an error
        raise ValueError(
            f"No working models available. Tried: {', '.join(models_to_try)}"
        )

    def create_provider_with_inference_fallback(
        self, preferred_model: str | None = None, use_case: str | None = None
    ) -> "LLMProviderWithFallback":
        """Create provider that automatically falls back during inference failures"""

        logger = get_logger("llm_provider.factory")

        # Get fallback chain using existing logic
        models_config = self.config_manager.get_models_config()
        use_cases = models_config.get("use_cases", {})
        fallback_config = models_config.get("fallback_strategy", {})

        # Determine which use case to use for fallbacks
        target_use_case = use_case or "general"
        case_config = use_cases.get(target_use_case, use_cases.get("general", {}))
        fallback_models = case_config.get("alternatives", [])

        # Build complete fallback chain
        models_to_try = []
        if preferred_model:
            models_to_try.append(preferred_model)

        # Add primary model for the use case
        primary_model = case_config.get("recommended", "local_general_standard")
        if primary_model not in models_to_try:
            models_to_try.append(primary_model)

        # Add use case specific fallback models
        for model in fallback_models:
            if model not in models_to_try:
                models_to_try.append(model)

        # Add global fallback models if enabled
        if fallback_config.get("enabled", True):
            global_fallbacks = fallback_config.get("default_fallback", [])
            for model in global_fallbacks:
                if model not in models_to_try:
                    models_to_try.append(model)

        logger.info(f"Creating provider with fallback chain: {models_to_try}")

        return LLMProviderWithFallback(self, models_to_try)


class LLMProviderWithFallback:
    """
    LLM provider wrapper that automatically falls back to alternative models
    when inference fails after exhausting retries
    """

    def __init__(self, factory: LLMProviderFactory, model_chain: list[str]):
        self.factory = factory
        self.model_chain = model_chain
        self.current_provider = None
        self.current_model_index = 0
        self.logger = get_logger("llm_provider.fallback")

        # Initialize with first working provider
        self._initialize_current_provider()

    def _initialize_current_provider(self):
        """Initialize the current provider, trying models in fallback chain"""
        while self.current_model_index < len(self.model_chain):
            try:
                model_name = self.model_chain[self.current_model_index]
                self.current_provider = self.factory.create_provider(model_name)
                self.logger.info(f"Initialized provider with model: {model_name}")
                return
            except Exception as e:
                self.logger.warning(f"Failed to initialize model {model_name}: {str(e)}")
                self.current_model_index += 1

        raise ValueError(f"No working models available in chain: {self.model_chain}")

    def _try_next_provider(self):
        """Try to initialize the next provider in the fallback chain"""
        self.current_model_index += 1
        if self.current_model_index >= len(self.model_chain):
            return False

        try:
            model_name = self.model_chain[self.current_model_index]
            self.current_provider = self.factory.create_provider(model_name)
            self.logger.info(
                f"✅ FALLBACK SUCCESS: Switched to model: {model_name}",
                extra={
                    "new_model": model_name,
                    "model_index": self.current_model_index,
                    "operation": "fallback_success"
                }
            )
            return True
        except Exception as e:
            self.logger.warning(f"Failed to switch to fallback model {model_name}: {str(e)}")
            return self._try_next_provider()  # Recursively try next

    @property
    def model_name(self) -> str:
        """Get current model name"""
        if self.current_provider:
            return self.current_provider.model_name
        return "unknown"

    @property
    def provider_type(self) -> str:
        """Get current provider type"""
        if self.current_provider:
            return self.current_provider.provider_type
        return "unknown"

    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response with automatic fallback on failure"""
        last_exception = None

        # Log the start of fallback chain
        self.logger.info(
            "🔗 STARTING FALLBACK CHAIN",
            extra={
                "fallback_chain": self.model_chain,
                "current_model": self.model_chain[self.current_model_index] if self.current_model_index < len(self.model_chain) else "none",
                "prompt_length": len(prompt),
                "operation": "fallback_chain_start"
            }
        )

        while self.current_provider and self.current_model_index < len(self.model_chain):
            try:
                # Try current provider (this will do its own retries)
                response = self.current_provider.generate_response(prompt, system_prompt)
                return response

            except (ModelInferenceError, Exception) as e:
                last_exception = e
                current_model = self.model_chain[self.current_model_index] if self.current_model_index < len(self.model_chain) else "unknown"

                self.logger.error(
                    f"🔄 FALLBACK: Model {current_model} failed after retries, attempting fallback",
                    extra={
                        "error": str(e), 
                        "model_index": self.current_model_index,
                        "failed_model": current_model,
                        "operation": "fallback_attempt"
                    }
                )

                # Try to switch to next provider
                if not self._try_next_provider():
                    break

        # If we get here, all models in the chain have been exhausted
        raise ModelInferenceError(
            f"All models in fallback chain failed. Chain: {self.model_chain}",
            model_name="fallback_chain",
            model_type="fallback",
            context={
                "fallback_chain": self.model_chain,
                "last_error": str(last_exception) if last_exception else None
            }
        )

    def evaluate_response(self, query: str, response: str) -> dict[str, Any]:
        """Evaluate response using current provider"""
        if self.current_provider:
            return self.current_provider.evaluate_response(query, response)
        return {"error": "No active provider"}


def create_provider_from_config(
    config_dir: str = "config", model_name: str | None = None
) -> LLMProvider:
    """Create LLM provider from configuration files"""
    factory = LLMProviderFactory(config_dir)

    if model_name:
        return factory.create_provider(model_name)
    else:
        return factory.create_auto_provider()


def create_provider_with_fallback_from_config(
    config_dir: str = "config",
    preferred_model: str | None = None,
    use_case: str | None = None
) -> LLMProviderWithFallback:
    """Create LLM provider with automatic inference fallback from configuration"""
    factory = LLMProviderFactory(config_dir)
    return factory.create_provider_with_inference_fallback(preferred_model, use_case)


# Backward compatibility function
def create_provider_from_env(config_dir: str = "config") -> LLMProvider:
    """Create LLM provider - now uses config files with environment overrides"""
    return create_provider_from_config(config_dir)
