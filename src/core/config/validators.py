"""
Configuration validation logic

Provides comprehensive validation for all configuration objects to ensure
system integrity and catch configuration errors early.
"""

import os
from pathlib import Path

from .schemas import (
    ContextConfig,
    LangSmithConfig,
    LLMConfig,
    ModelConfig,
    ModelsConfig,
    PromptsConfig,
    SystemConfig,
    ThresholdsConfig,
)


class ValidationError(Exception):
    """Raised when configuration validation fails"""

    pass


class ConfigValidator:
    """Validates configuration objects and reports errors"""

    def __init__(self, strict: bool = False):
        """
        Initialize validator

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_system_config(
        self, config: SystemConfig
    ) -> tuple[list[str], list[str]]:
        """
        Validate complete system configuration

        Returns:
            Tuple of (errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()

        # Validate each component
        self._validate_models_config(config.models)
        self._validate_llm_config(config.llm, config.models)
        self._validate_thresholds_config(config.thresholds)
        self._validate_prompts_config(config.prompts)
        self._validate_langsmith_config(config.langsmith)
        self._validate_context_config(config.context)

        # Cross-component validation
        self._validate_cross_dependencies(config)

        return self.errors.copy(), self.warnings.copy()

    def _validate_models_config(self, config: ModelsConfig) -> None:
        """Validate models configuration"""
        if not config.models:
            self.errors.append("No models configured")
            return

        # Validate default model exists
        if config.default_model not in config.models:
            self.errors.append(
                f"Default model '{config.default_model}' not found in models"
            )

        # Validate each model
        for model_name, model_config in config.models.items():
            self._validate_model_config(model_config)

        # Validate fallback models exist
        for fallback_model in config.fallback_models:
            if fallback_model not in config.models:
                self.errors.append(
                    f"Fallback model '{fallback_model}' not found in models"
                )

        # Validate use cases reference valid models
        for use_case, case_config in config.use_cases.items():
            recommended = case_config.get("recommended")
            if recommended and recommended not in config.models:
                self.errors.append(
                    f"Use case '{use_case}' recommends unknown model '{recommended}'"
                )

            alternatives = case_config.get("alternatives", [])
            for alt_model in alternatives:
                if alt_model not in config.models:
                    self.errors.append(
                        f"Use case '{use_case}' lists unknown alternative model '{alt_model}'"
                    )

        # Check for available models
        available_models = config.get_available_models()
        if not available_models:
            self.warnings.append(
                "No models are currently available (check model files and API keys)"
            )

        # Warn about missing local model files
        for model_name, model_config in config.models.items():
            if model_config.is_local() and not model_config.is_available():
                self.warnings.append(f"Local model file not found: {model_config.path}")

    def _validate_model_config(self, config: ModelConfig) -> None:
        """Validate individual model configuration"""
        # Validate model type
        valid_types = ["llama", "mistral", "openai", "anthropic", "ctransformers"]
        if config.type not in valid_types:
            self.errors.append(
                f"Invalid model type '{config.type}' for model '{config.name}'. Valid types: {valid_types}"
            )

        # Validate local model requirements
        if config.is_local():
            if not config.path:
                self.errors.append(
                    f"Local model '{config.name}' missing required 'path' field"
                )
            elif not Path(config.path).exists():
                self.warnings.append(f"Model file not found: {config.path}")

        # Validate OpenAI model requirements
        if config.type == "openai":
            if not config.model_name:
                self.errors.append(
                    f"OpenAI model '{config.name}' missing required 'model_name' field"
                )
            if not os.getenv("OPENAI_API_KEY"):
                self.warnings.append(
                    f"OpenAI model '{config.name}' requires OPENAI_API_KEY environment variable"
                )

        # Validate Anthropic model requirements
        if config.type == "anthropic":
            if not config.model_name:
                self.errors.append(
                    f"Anthropic model '{config.name}' missing required 'model_name' field"
                )
            if not os.getenv("ANTHROPIC_API_KEY"):
                self.warnings.append(
                    f"Anthropic model '{config.name}' requires ANTHROPIC_API_KEY environment variable"
                )

        # Validate numeric parameters
        if config.context_length <= 0:
            self.errors.append(f"Model '{config.name}' context_length must be positive")

        if config.gpu_layers < 0:
            self.errors.append(f"Model '{config.name}' gpu_layers cannot be negative")

        if not (0.0 <= config.temperature <= 2.0):
            self.warnings.append(
                f"Model '{config.name}' temperature {config.temperature} outside typical range 0.0-2.0"
            )

        if config.max_tokens <= 0:
            self.errors.append(f"Model '{config.name}' max_tokens must be positive")

    def _validate_llm_config(
        self, config: LLMConfig, models_config: ModelsConfig
    ) -> None:
        """Validate LLM configuration"""
        # Validate provider strategy
        valid_providers = ["auto", "local", "openai", "anthropic"] + list(
            models_config.models.keys()
        )
        if config.provider not in valid_providers:
            self.errors.append(
                f"Invalid provider '{config.provider}'. Valid options: {valid_providers}"
            )

        # Validate primary model exists
        if config.primary_model not in models_config.models:
            self.errors.append(
                f"Primary model '{config.primary_model}' not found in models"
            )

        # Validate use case
        if config.use_case not in models_config.use_cases:
            self.warnings.append(
                f"Use case '{config.use_case}' not defined in models configuration"
            )

        # Validate performance settings
        if config.performance.cache_size <= 0:
            self.errors.append("Performance cache_size must be positive")

        if config.validation.loading_timeout <= 0:
            self.errors.append("Validation loading_timeout must be positive")

    def _validate_thresholds_config(self, config: ThresholdsConfig) -> None:
        """Validate thresholds configuration"""
        if not (0.0 <= config.escalation_score <= 10.0):
            self.errors.append("Escalation score must be between 0.0 and 10.0")

        if not (0.0 <= config.confidence_threshold <= 1.0):
            self.errors.append("Confidence threshold must be between 0.0 and 1.0")

        if config.repeat_query_threshold <= 0:
            self.errors.append("Repeat query threshold must be positive")

        if config.max_escalations_per_session <= 0:
            self.errors.append("Max escalations per session must be positive")

        if config.response_time_threshold <= 0:
            self.errors.append("Response time threshold must be positive")

    def _validate_prompts_config(self, config: PromptsConfig) -> None:
        """Validate prompts configuration"""
        # Check for required prompt templates
        required_prompts = {
            "answer_agent": ["system_prompt"],
            "evaluator_agent": ["evaluation_prompt"],
            "human_interface": ["escalation_message"],
        }

        for component, required in required_prompts.items():
            component_prompts = getattr(config, component, {})
            for prompt_name in required:
                if prompt_name not in component_prompts:
                    self.warnings.append(
                        f"Missing recommended prompt '{prompt_name}' for {component}"
                    )

    def _validate_langsmith_config(self, config: LangSmithConfig) -> None:
        """Validate LangSmith configuration"""
        if config.enabled and not os.getenv("LANGSMITH_API_KEY"):
            self.warnings.append("LangSmith enabled but LANGSMITH_API_KEY not set")

        if not config.project_name:
            self.errors.append("LangSmith project name cannot be empty")

        if not config.endpoint:
            self.errors.append("LangSmith endpoint cannot be empty")

    def _validate_context_config(self, config: ContextConfig) -> None:
        """Validate context configuration"""
        if not config.database_path:
            self.errors.append("Context database path cannot be empty")

        if config.max_context_entries <= 0:
            self.errors.append("Max context entries must be positive")

        if config.context_ttl_days <= 0:
            self.errors.append("Context TTL days must be positive")

        # Check if database directory is writable
        db_path = Path(config.database_path)
        db_dir = db_path.parent
        if db_dir.exists() and not os.access(db_dir, os.W_OK):
            self.warnings.append(f"Database directory may not be writable: {db_dir}")

    def _validate_cross_dependencies(self, config: SystemConfig) -> None:
        """Validate cross-component dependencies"""
        # Check if primary model is available
        try:
            primary_model = config.models.get_model(config.llm.primary_model)
            if not primary_model.is_available():
                self.warnings.append(
                    f"Primary model '{config.llm.primary_model}' is not currently available"
                )
        except ValueError:
            pass  # Already caught in individual validation

        # Check if fallback strategy makes sense
        if config.llm.enable_fallback and not config.models.fallback_models:
            self.warnings.append("Fallback enabled but no fallback models configured")

        # Check if any models are available for the configured provider strategy
        available_models = config.models.get_available_models()
        if config.llm.provider == "local":
            local_available = [m for m in available_models if m.is_local()]
            if not local_available:
                self.warnings.append(
                    "Provider strategy is 'local' but no local models are available"
                )
        elif config.llm.provider == "openai":
            openai_available = [m for m in available_models if m.type == "openai"]
            if not openai_available:
                self.warnings.append(
                    "Provider strategy is 'openai' but no OpenAI models are available"
                )

    def validate_and_raise(self, config: SystemConfig) -> None:
        """Validate configuration and raise exception if errors found"""
        errors, warnings = self.validate_system_config(config)

        if warnings:
            print("Configuration warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  ❌ {error}" for error in errors
            )
            raise ValidationError(error_msg)

        if self.strict and warnings:
            warning_msg = (
                "Configuration validation failed (strict mode):\n"
                + "\n".join(f"  ⚠️  {warning}" for warning in warnings)
            )
            raise ValidationError(warning_msg)
