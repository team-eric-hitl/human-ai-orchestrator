"""
Agent-centric configuration manager

Handles loading and managing configuration for the new agent-centric structure
with support for shared configs, environment overrides, and hot reloading.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

import yaml


class ConfigLoadError(Exception):
    """Raised when configuration loading fails"""
    pass


@dataclass
class AgentConfig:
    """Configuration for a specific agent"""
    name: str
    description: str
    type: str
    version: str = "1.0.0"
    created: str = ""
    last_modified: str = ""
    models: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    prompts: dict[str, Any] = field(default_factory=dict)
    behavior: dict[str, Any] = field(default_factory=dict)
    escalation: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)
    routing: dict[str, Any] = field(default_factory=dict)

    def get_preferred_model(self, model_aliases: dict[str, str] = None) -> str:
        """Get the preferred model for this agent, resolving aliases if needed"""
        preferred = self.models.get('preferred', 'local_general_standard')
        return self._resolve_model_alias(preferred, model_aliases)

    def get_fallback_models(self, model_aliases: dict[str, str] = None) -> list[str]:
        """Get fallback models for this agent, resolving aliases if needed"""
        fallbacks = self.models.get('fallback', [])
        return [self._resolve_model_alias(model, model_aliases) for model in fallbacks]
    
    def _resolve_model_alias(self, model_name: str, model_aliases: dict[str, str] = None) -> str:
        """Resolve a model alias to its actual model name"""
        if model_aliases and model_name in model_aliases:
            return model_aliases[model_name]
        return model_name

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with dot notation support"""
        keys = key.split('.')

        # Try different config sections in order
        for config_section in [self.settings, self.evaluation, self.routing, self.behavior, self.escalation]:
            value = config_section
            found = True

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    found = False
                    break

            if found:
                return value

        return default

    def get_evaluation_setting(self, key: str, default: Any = None) -> Any:
        """Get an evaluation setting value with dot notation support"""
        keys = key.split('.')
        value = self.evaluation

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_prompt(self, prompt_type: str) -> str:
        """Get a prompt template for this agent"""
        if prompt_type == 'system':
            return self.prompts.get('system_prompt', f'You are a {self.name} assistant.')

        templates = self.prompts.get('templates', {})
        return templates.get(prompt_type, f'Default {prompt_type} prompt for {self.name}')


@dataclass
class SystemConfig:
    """Global system configuration"""
    name: str = "Modular LangGraph Hybrid System"
    version: str = "1.0.0"
    config_schema_version: str = "1.0.0"
    environment: str = "development"
    thresholds: dict[str, Any] = field(default_factory=dict)
    providers: dict[str, Any] = field(default_factory=dict)
    monitoring: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)
    versioning: dict[str, Any] = field(default_factory=dict)


class AgentConfigManager:
    """
    Agent-centric configuration manager

    Loads and manages configuration using the new agent-centric structure:
    - config/shared/ - Global configurations
    - config/agents/ - Agent-specific configurations
    - config/environments/ - Environment-specific overrides
    """

    def __init__(self, config_dir: str | Path, environment: str | None = None, validate_versions: bool = True):
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv('HYBRID_SYSTEM_ENV', 'development')
        self.validate_versions = validate_versions
        self._agents: dict[str, AgentConfig] = {}
        self._system_config: SystemConfig | None = None
        self._models_config: dict[str, Any] = {}
        self._providers_config: dict[str, Any] = {}
        self._model_aliases: dict[str, str] = {}
        self._versioning_config: dict[str, Any] = {}
        self._lock = Lock()

        self.logger = logging.getLogger(__name__)

        # Load all configurations
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """Load all configuration files"""
        try:
            # Load shared configurations first
            self._load_shared_configs()

            # Load agent configurations
            self._load_agent_configs()

            # Apply environment overrides
            self._apply_environment_overrides()

            self.logger.info(f"Configuration loaded successfully for environment: {self.environment}")

        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")
            raise ConfigLoadError(f"Configuration loading failed: {e}") from e

    def _load_shared_configs(self) -> None:
        """Load shared configuration files"""
        shared_dir = self.config_dir / "shared"

        # Load system config
        system_file = shared_dir / "system.yaml"
        if system_file.exists():
            with open(system_file) as f:
                system_data = yaml.safe_load(f) or {}
                self._system_config = SystemConfig(
                    name=system_data.get('system', {}).get('name', 'Modular LangGraph Hybrid System'),
                    version=system_data.get('system', {}).get('version', '1.0.0'),
                    environment=self.environment,
                    thresholds=system_data.get('thresholds', {}),
                    providers=system_data.get('providers', {}),
                    monitoring=system_data.get('monitoring', {}),
                    security=system_data.get('security', {}),
                    performance=system_data.get('performance', {})
                )
        else:
            self._system_config = SystemConfig(environment=self.environment)

        # Load models config
        models_file = shared_dir / "models.yaml"
        if models_file.exists():
            with open(models_file) as f:
                self._models_config = yaml.safe_load(f) or {}
                # Load model aliases
                self._model_aliases = self._models_config.get('model_aliases', {})

        # Load providers config
        providers_file = shared_dir / "providers.yaml"
        if providers_file.exists():
            with open(providers_file) as f:
                self._providers_config = yaml.safe_load(f) or {}

    def _load_agent_configs(self) -> None:
        """Load all agent configurations"""
        agents_dir = self.config_dir / "agents"

        if not agents_dir.exists():
            self.logger.warning(f"Agents directory not found: {agents_dir}")
            return

        # Find all agent directories
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                self._load_agent_config(agent_dir)

    def _load_agent_config(self, agent_dir: Path) -> None:
        """Load configuration for a specific agent"""
        agent_name = agent_dir.name

        try:
            # Load agent config files
            config_data = {}
            prompts_data = {}
            models_data = {}

            # Load main config
            config_file = agent_dir / "config.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    config_data = yaml.safe_load(f) or {}

            # Load prompts
            prompts_file = agent_dir / "prompts.yaml"
            if prompts_file.exists():
                with open(prompts_file) as f:
                    prompts_data = yaml.safe_load(f) or {}

            # Load models
            models_file = agent_dir / "models.yaml"
            if models_file.exists():
                with open(models_file) as f:
                    models_data = yaml.safe_load(f) or {}

            # Merge models from both config.yaml and models.yaml
            merged_models = {}
            merged_models.update(config_data.get('models', {}))
            merged_models.update(models_data)
            
            # Create agent config
            agent_section = config_data.get('agent', {})
            agent_config = AgentConfig(
                name=agent_section.get('name', agent_name),
                description=agent_section.get('description', ''),
                type=agent_section.get('type', 'agent'),
                version=agent_section.get('version', '1.0.0'),
                created=agent_section.get('created', ''),
                last_modified=agent_section.get('last_modified', ''),
                models=merged_models,
                settings=config_data.get('settings', {}),
                prompts=prompts_data,
                behavior=config_data.get('behavior', {}),
                escalation=config_data.get('escalation', {}),
                evaluation=config_data.get('evaluation', {}),
                routing=config_data.get('routing', {})
            )
            
            # Validate agent version if enabled
            if self.validate_versions:
                self._validate_agent_version(agent_config)

            self._agents[agent_name] = agent_config
            self.logger.debug(f"Loaded configuration for agent: {agent_name} (v{agent_config.version})")

        except Exception as e:
            self.logger.error(f"Failed to load agent config for {agent_name}: {e}")
            raise ConfigLoadError(f"Failed to load agent config for {agent_name}: {e}") from e

    def _validate_agent_version(self, agent_config: AgentConfig) -> None:
        """Validate agent version against system requirements"""
        if not agent_config.version:
            raise ConfigLoadError(f"Agent {agent_config.name} missing version field")
        
        # Validate version format (basic semantic versioning check)
        version_parts = agent_config.version.split('.')
        if len(version_parts) != 3 or not all(part.isdigit() for part in version_parts):
            raise ConfigLoadError(f"Agent {agent_config.name} has invalid version format: {agent_config.version}")
        
        self.logger.debug(f"Agent {agent_config.name} version {agent_config.version} validated")

    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides"""
        env_file = self.config_dir / "environments" / f"{self.environment}.yaml"

        if not env_file.exists():
            self.logger.debug(f"No environment file found for {self.environment}")
            return

        try:
            with open(env_file) as f:
                env_data = yaml.safe_load(f) or {}

            # Apply system-level overrides
            if 'system' in env_data and self._system_config:
                for key, value in env_data['system'].items():
                    if hasattr(self._system_config, key):
                        setattr(self._system_config, key, value)

            # Apply threshold overrides
            if 'thresholds' in env_data and self._system_config:
                self._system_config.thresholds.update(env_data['thresholds'])

            # Apply model overrides
            if 'models' in env_data:
                self._models_config.update(env_data['models'])

            self.logger.debug(f"Applied environment overrides for {self.environment}")

        except Exception as e:
            self.logger.error(f"Failed to apply environment overrides: {e}")

    def get_agent_config(self, agent_name: str) -> AgentConfig | None:
        """Get configuration for a specific agent"""
        return self._agents.get(agent_name)

    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        if not self._system_config:
            raise RuntimeError("System configuration not loaded")
        return self._system_config

    def get_models_config(self) -> dict[str, Any]:
        """Get global models configuration"""
        return self._models_config

    def get_providers_config(self) -> dict[str, Any]:
        """Get providers configuration"""
        return self._providers_config
    
    def get_model_aliases(self) -> dict[str, str]:
        """Get model aliases mapping"""
        return self._model_aliases
    
    def resolve_model_name(self, model_alias: str) -> str:
        """Resolve a model alias to its actual model name"""
        return self._model_aliases.get(model_alias, model_alias)
    
    def get_agent_preferred_model(self, agent_name: str) -> str:
        """Get the resolved preferred model for an agent"""
        agent = self.get_agent_config(agent_name)
        if agent:
            return agent.get_preferred_model(self._model_aliases)
        return 'local_general_standard'
    
    def get_agent_fallback_models(self, agent_name: str) -> list[str]:
        """Get the resolved fallback models for an agent"""
        agent = self.get_agent_config(agent_name)
        if agent:
            return agent.get_fallback_models(self._model_aliases)
        return []

    def get_available_agents(self) -> list[str]:
        """Get list of available agent names"""
        return list(self._agents.keys())

    def get_model_config(self, model_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific model"""
        models = self._models_config.get('models', {})
        return models.get(model_name)

    def get_primary_model_for_agent(self, agent_name: str) -> str:
        """Get the primary model for an agent with fallback to global default"""
        agent = self.get_agent_config(agent_name)
        if agent:
            return agent.get_preferred_model()

        # Fallback to global default
        return self._models_config.get('use_cases', {}).get('general', {}).get('recommended', 'llama-7b')

    def get_threshold(self, threshold_name: str, default: Any = None) -> Any:
        """Get a threshold value"""
        if self._system_config:
            return self._system_config.thresholds.get(threshold_name, default)
        return default

    def get_provider_config(self, provider_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific provider"""
        providers = self._providers_config.get('llm_providers', {})
        return providers.get(provider_name)

    def reload(self) -> None:
        """Reload all configurations"""
        with self._lock:
            self._agents.clear()
            self._system_config = None
            self._models_config = {}
            self._providers_config = {}
            self._load_all_configs()
            self.logger.info("Configuration reloaded successfully")

    def get_agent_version(self, agent_name: str) -> str | None:
        """Get version of a specific agent"""
        agent = self.get_agent_config(agent_name)
        return agent.version if agent else None

    def get_agent_versions(self) -> dict[str, str]:
        """Get versions of all loaded agents"""
        return {name: agent.version for name, agent in self._agents.items()}

    def validate_all_agent_versions(self) -> bool:
        """Validate versions for all loaded agents"""
        try:
            for agent in self._agents.values():
                self._validate_agent_version(agent)
            return True
        except ConfigLoadError:
            return False

    def get_summary(self) -> dict[str, Any]:
        """Get a comprehensive summary of the configuration"""
        return {
            "config_directory": str(self.config_dir),
            "environment": self.environment,
            "system_name": self._system_config.name if self._system_config else "Unknown",
            "system_version": self._system_config.version if self._system_config else "Unknown",
            "config_schema_version": self._system_config.config_schema_version if self._system_config else "Unknown",
            "agents_loaded": len(self._agents),
            "agent_names": list(self._agents.keys()),
            "agent_versions": {name: agent.version for name, agent in self._agents.items()},
            "models_configured": len(self._models_config.get('models', {})),
            "providers_configured": len(self._providers_config.get('llm_providers', {})),
            "thresholds": self._system_config.thresholds if self._system_config else {},
            "versioning_enabled": self.validate_versions,
            "config_files_structure": {
                "shared": (self.config_dir / "shared").exists(),
                "agents": (self.config_dir / "agents").exists(),
                "environments": (self.config_dir / "environments").exists(),
            }
        }
