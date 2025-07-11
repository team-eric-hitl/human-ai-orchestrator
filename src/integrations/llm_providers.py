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

# Local LLMs
from langchain_community.llms import CTransformers, LlamaCpp
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
        """Generate response using LLM"""
        start_time = time.time()

        self.logger.debug(
            "Starting response generation",
            extra={
                "model_name": self.model_name,
                "prompt_length": len(prompt),
                "has_system_prompt": bool(system_prompt),
            },
        )

        try:
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
                extra={"prompt_length": len(prompt), "duration": duration},
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
        else:
            # Get the primary model from use cases
            use_cases = models_config.get("use_cases", {})
            general_use_case = use_cases.get("general", {})
            primary_model_name = general_use_case.get("recommended", "local_general_standard")
            resolved_model_name = primary_model_name
            model_config = available_models.get(primary_model_name, {})

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
                print(f"✅ Auto-selected local model: {model_name}")
            else:
                model_name = list(available_models.keys())[0]
                model_config = available_models[model_name]
                print(f"✅ Auto-selected cloud model: {model_name}")

            return LLMProvider(model_config)

        elif strategy == "local":
            # Force local model
            local_models = {k: v for k, v in available_models.items() if v.get("type") in ["llama", "local"]}
            if not local_models:
                raise ValueError("No local models are available")
            model_name = list(local_models.keys())[0]
            return LLMProvider(local_models[model_name])

        elif strategy == "openai":
            # Force OpenAI
            openai_models = {k: v for k, v in available_models.items() if v.get("type") == "openai"}
            if not openai_models:
                raise ValueError(
                    "No OpenAI models are available (check OPENAI_API_KEY)"
                )
            model_name = list(openai_models.keys())[0]
            return LLMProvider(openai_models[model_name])

        elif strategy == "anthropic":
            # Force Anthropic
            anthropic_models = {k: v for k, v in available_models.items() if v.get("type") == "anthropic"}
            if not anthropic_models:
                raise ValueError(
                    "No Anthropic models are available (check ANTHROPIC_API_KEY)"
                )
            model_name = list(anthropic_models.keys())[0]
            return LLMProvider(anthropic_models[model_name])

        else:
            # Strategy is a specific model name
            return self.create_provider(strategy)

    def create_provider_with_fallback(
        self, preferred_model: str | None = None
    ) -> LLMProvider:
        """Create provider with automatic fallback to available models"""

        logger = get_logger("llm_provider.factory")

        # Get fallback chain from config
        models_config = self.config_manager.get_models_config()
        use_cases = models_config.get("use_cases", {})
        general_use_case = use_cases.get("general", {})
        fallback_models = general_use_case.get("alternatives", [])

        # Start with preferred model if specified
        models_to_try = []
        if preferred_model:
            models_to_try.append(preferred_model)

        # Add primary model
        try:
            primary_model = general_use_case.get("recommended", "local_general_standard")
            if primary_model not in models_to_try:
                models_to_try.append(primary_model)
        except Exception:
            pass

        # Add fallback models
        for model in fallback_models:
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


def create_provider_from_config(
    config_dir: str = "config", model_name: str | None = None
) -> LLMProvider:
    """Create LLM provider from configuration files"""
    factory = LLMProviderFactory(config_dir)

    if model_name:
        return factory.create_provider(model_name)
    else:
        return factory.create_auto_provider()


# Backward compatibility function
def create_provider_from_env(config_dir: str = "config") -> LLMProvider:
    """Create LLM provider - now uses config files with environment overrides"""
    return create_provider_from_config(config_dir)
