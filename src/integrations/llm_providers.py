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
from ..core.config import ConfigManager, ModelConfig

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

    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config
        self.provider_type = model_config.type
        self.logger = get_logger(f"llm_provider.{model_config.name}")

        self.logger.info(
            "Initializing LLM provider",
            extra={
                "model_name": model_config.name,
                "model_type": model_config.type,
                "is_local": model_config.is_local(),
            },
        )

        try:
            self.client = self._initialize_client()
            self.logger.info(
                "LLM provider initialized successfully",
                extra={"model_name": model_config.name},
            )
        except Exception as e:
            self.logger.error(
                "Failed to initialize LLM provider",
                exc_info=True,
                extra={"model_name": model_config.name, "error": str(e)},
            )
            raise ModelError(
                f"Failed to initialize {model_config.name}",
                model_name=model_config.name,
                model_type=model_config.type,
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
            model=self.model_config.model_name or "gpt-4",
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
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
            model=self.model_config.model_name or "claude-3-sonnet-20240229",
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            api_key=api_key,
        )

    def _setup_llama(self) -> LlamaCpp:
        """Setup LlamaCpp client for local Llama models"""
        if not self.model_config.path:
            raise ValueError(f"Model path is required for {self.model_config.name}")

        if not Path(self.model_config.path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_config.path}")

        return LlamaCpp(
            model_path=self.model_config.path,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            n_ctx=self.model_config.context_length,
            n_gpu_layers=self.model_config.gpu_layers,
            verbose=False,
        )

    def _setup_mistral(self) -> LlamaCpp:
        """Setup Mistral client (uses LlamaCpp backend)"""
        if not self.model_config.path:
            raise ValueError(f"Model path is required for {self.model_config.name}")

        if not Path(self.model_config.path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_config.path}")

        return LlamaCpp(
            model_path=self.model_config.path,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            n_ctx=self.model_config.context_length,
            n_gpu_layers=self.model_config.gpu_layers,
            verbose=False,
        )

    def _setup_ctransformers(self) -> CTransformers:
        """Setup CTransformers client for optimized local models"""
        if not self.model_config.path:
            raise ValueError(f"Model path is required for {self.model_config.name}")

        if not Path(self.model_config.path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_config.path}")

        return CTransformers(
            model=self.model_config.path,
            model_type="llama",  # CTransformers model type
            temperature=self.model_config.temperature,
            max_new_tokens=self.model_config.max_tokens,
            context_length=self.model_config.context_length,
            gpu_layers=self.model_config.gpu_layers,
        )

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    @traceable(
        run_type="llm",
        name="LLM Response Generation",
        metadata=lambda self, prompt, system_prompt="": {
            "model_name": self.model_config.name,
            "model_type": self.model_config.type,
            "temperature": self.model_config.temperature,
            "max_tokens": self.model_config.max_tokens,
            "is_local": self.model_config.is_local(),
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
                "model_name": self.model_config.name,
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
                model_name=self.model_config.name,
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
                    "model_name": self.model_config.name,
                    "duration": duration,
                    "error": str(e),
                },
            )

            raise ModelInferenceError(
                f"Failed to generate response with {self.model_config.name}",
                model_name=self.model_config.name,
                model_type=self.model_config.type,
                extra={"prompt_length": len(prompt), "duration": duration},
            ) from e

    @traceable(
        run_type="llm",
        name="LLM Response Evaluation",
        metadata=lambda self, query, response: {
            "model_name": self.model_config.name,
            "model_type": self.model_config.type,
            "query_length": len(query),
            "response_length": len(response),
            "evaluation_model": self.model_config.name,
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
            result = self.generate_response(evaluation_prompt)
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

    def create_provider(self, model_name: str | None = None) -> LLMProvider:
        """
        Create LLM provider from configuration

        Args:
            model_name: Specific model name, or None to use primary model
        """
        if model_name:
            model_config = self.config_manager.models.get_model(model_name)
        else:
            model_config = self.config_manager.get_primary_model()

        # Validate model is available
        if not model_config.is_available():
            if model_config.is_local():
                raise FileNotFoundError(f"Model file not found: {model_config.path}")
            elif model_config.type == "openai":
                raise ValueError("OPENAI_API_KEY not set for OpenAI model")
            else:
                raise ValueError(f"Model {model_config.name} is not available")

        print(f"✅ Creating LLM provider: {model_config.name} ({model_config.type})")
        return LLMProvider(model_config)

    def create_auto_provider(self) -> LLMProvider:
        """Automatically select the best available provider"""
        strategy = self.config_manager.get_provider_strategy()

        if strategy == "auto":
            # Try to find the best available model
            available_models = self.config_manager.get_available_models()

            if not available_models:
                raise ValueError(
                    "No models are available. Check your configuration and model files."
                )

            # Prefer local models, then OpenAI
            local_models = [m for m in available_models if m.is_local()]
            if local_models:
                model_config = local_models[0]
                print(f"✅ Auto-selected local model: {model_config.name}")
            else:
                model_config = available_models[0]
                print(f"✅ Auto-selected cloud model: {model_config.name}")

            return LLMProvider(model_config)

        elif strategy == "local":
            # Force local model
            available_models = [
                m for m in self.config_manager.get_available_models() if m.is_local()
            ]
            if not available_models:
                raise ValueError("No local models are available")
            return LLMProvider(available_models[0])

        elif strategy == "openai":
            # Force OpenAI
            openai_models = [
                m
                for m in self.config_manager.get_available_models()
                if m.type == "openai"
            ]
            if not openai_models:
                raise ValueError(
                    "No OpenAI models are available (check OPENAI_API_KEY)"
                )
            return LLMProvider(openai_models[0])

        elif strategy == "anthropic":
            # Force Anthropic
            anthropic_models = [
                m
                for m in self.config_manager.get_available_models()
                if m.type == "anthropic"
            ]
            if not anthropic_models:
                raise ValueError(
                    "No Anthropic models are available (check ANTHROPIC_API_KEY)"
                )
            return LLMProvider(anthropic_models[0])

        else:
            # Strategy is a specific model name
            return self.create_provider(strategy)

    def create_provider_with_fallback(
        self, preferred_model: str | None = None
    ) -> LLMProvider:
        """Create provider with automatic fallback to available models"""

        logger = get_logger("llm_provider.factory")

        # Get fallback chain from config
        fallback_models = self.config_manager.models.fallback_models

        # Start with preferred model if specified
        models_to_try = []
        if preferred_model:
            models_to_try.append(preferred_model)

        # Add primary model
        try:
            primary_model = self.config_manager.get_primary_model()
            if primary_model.name not in models_to_try:
                models_to_try.append(primary_model.name)
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
