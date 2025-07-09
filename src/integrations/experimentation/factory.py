"""
Factory for creating experimentation providers

This module provides a factory pattern for creating experimentation providers
with support for different implementations (custom, DSPy, promptfoo, etc.)
"""

from typing import Dict, List, Optional, Type

from ...core.config import ConfigManager
from ...core.logging import get_logger
from ...core.session_tracker import SessionTracker
from ...integrations.llm_providers import LLMProviderFactory
from ...interfaces.experimentation import ExperimentationInterface
from .custom_experimenter import CustomExperimenter


class ExperimentationFactory:
    """Factory for creating experimentation providers
    
    This factory follows the same pattern as LLMProviderFactory, allowing
    easy swapping between different experimentation implementations.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        session_tracker: SessionTracker,
        llm_factory: LLMProviderFactory
    ):
        """Initialize the experimentation factory
        
        Args:
            config_manager: Configuration management instance
            session_tracker: Session tracking instance
            llm_factory: LLM provider factory
        """
        self.config_manager = config_manager
        self.session_tracker = session_tracker
        self.llm_factory = llm_factory
        self.logger = get_logger("experimentation.factory")
        
        # Registry of available experimenter implementations
        self._experimenters: Dict[str, Type[ExperimentationInterface]] = {
            "custom": CustomExperimenter,
            # Future implementations can be added here:
            # "dspy": DSPyExperimenter,
            # "promptfoo": PromptfooExperimenter,
        }
        
        self.logger.info(
            "Experimentation factory initialized",
            extra={
                "available_experimenters": list(self._experimenters.keys()),
                "config_dir": config_manager.config_dir
            }
        )
    
    def create_experimenter(
        self,
        provider_type: str = "custom",
        **kwargs
    ) -> ExperimentationInterface:
        """Create an experimentation provider
        
        Args:
            provider_type: Type of experimenter to create ("custom", "dspy", "promptfoo")
            **kwargs: Additional arguments for the experimenter
            
        Returns:
            ExperimentationInterface implementation
            
        Raises:
            ValueError: If provider_type is not supported
        """
        if provider_type not in self._experimenters:
            available = ", ".join(self._experimenters.keys())
            raise ValueError(
                f"Unsupported experimenter type: {provider_type}. "
                f"Available types: {available}"
            )
        
        experimenter_class = self._experimenters[provider_type]
        
        self.logger.info(
            f"Creating experimenter: {provider_type}",
            extra={
                "provider_type": provider_type,
                "experimenter_class": experimenter_class.__name__
            }
        )
        
        if provider_type == "custom":
            return experimenter_class(
                config_manager=self.config_manager,
                session_tracker=self.session_tracker,
                llm_factory=self.llm_factory,
                **kwargs
            )
        # Future implementations would have their own initialization logic
        # elif provider_type == "dspy":
        #     return experimenter_class(
        #         config_manager=self.config_manager,
        #         dspy_config=kwargs.get("dspy_config"),
        #         **kwargs
        #     )
        # elif provider_type == "promptfoo":
        #     return experimenter_class(
        #         config_manager=self.config_manager,
        #         promptfoo_config=kwargs.get("promptfoo_config"),
        #         **kwargs
        #     )
        else:
            # Default initialization
            return experimenter_class(
                config_manager=self.config_manager,
                session_tracker=self.session_tracker,
                llm_factory=self.llm_factory,
                **kwargs
            )
    
    def create_auto_experimenter(self) -> ExperimentationInterface:
        """Create experimenter using automatic selection
        
        Automatically selects the best available experimenter based on
        configuration and available implementations.
        
        Returns:
            ExperimentationInterface implementation
        """
        # Get preferred experimenter from config
        # Check system config for experimentation provider setting
        system_config = self.config_manager.get_system_config()
        preferred_experimenter = system_config.providers.get("experimentation", "custom")
        
        # Check if preferred experimenter is available
        if preferred_experimenter in self._experimenters:
            self.logger.info(
                f"Using preferred experimenter: {preferred_experimenter}",
                extra={"provider_type": preferred_experimenter}
            )
            return self.create_experimenter(preferred_experimenter)
        
        # Fallback to custom experimenter
        self.logger.warning(
            f"Preferred experimenter '{preferred_experimenter}' not available, "
            "falling back to custom experimenter",
            extra={
                "preferred": preferred_experimenter,
                "fallback": "custom"
            }
        )
        return self.create_experimenter("custom")
    
    def create_experimenter_with_fallback(
        self,
        preferred_type: str = "custom",
        fallback_types: Optional[List[str]] = None
    ) -> ExperimentationInterface:
        """Create experimenter with fallback options
        
        Attempts to create the preferred experimenter, falling back to
        alternatives if the preferred one is not available.
        
        Args:
            preferred_type: Preferred experimenter type
            fallback_types: List of fallback types to try
            
        Returns:
            ExperimentationInterface implementation
            
        Raises:
            ValueError: If no experimenters are available
        """
        if fallback_types is None:
            fallback_types = ["custom"]
        
        # Try preferred type first
        experimenters_to_try = [preferred_type] + fallback_types
        
        for experimenter_type in experimenters_to_try:
            if experimenter_type in self._experimenters:
                try:
                    self.logger.info(
                        f"Attempting to create experimenter: {experimenter_type}",
                        extra={"provider_type": experimenter_type}
                    )
                    return self.create_experimenter(experimenter_type)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to create experimenter {experimenter_type}: {str(e)}",
                        extra={
                            "provider_type": experimenter_type,
                            "error": str(e)
                        }
                    )
                    continue
        
        # If all experimenters failed
        raise ValueError(
            f"No working experimenters available. Tried: {experimenters_to_try}"
        )
    
    def register_experimenter(
        self,
        name: str,
        experimenter_class: Type[ExperimentationInterface]
    ):
        """Register a new experimenter implementation
        
        This allows for runtime registration of new experimenter types,
        enabling plugin-style extensibility.
        
        Args:
            name: Name for the experimenter type
            experimenter_class: Class implementing ExperimentationInterface
            
        Raises:
            ValueError: If name already exists or class is invalid
        """
        if name in self._experimenters:
            raise ValueError(f"Experimenter '{name}' already registered")
        
        if not issubclass(experimenter_class, ExperimentationInterface):
            raise ValueError(
                f"Experimenter class must implement ExperimentationInterface"
            )
        
        self._experimenters[name] = experimenter_class
        
        self.logger.info(
            f"Registered experimenter: {name}",
            extra={
                "name": name,
                "class": experimenter_class.__name__
            }
        )
    
    def get_available_experimenters(self) -> List[str]:
        """Get list of available experimenter types
        
        Returns:
            List of experimenter type names
        """
        return list(self._experimenters.keys())
    
    def get_experimenter_info(self, experimenter_type: str) -> Dict[str, any]:
        """Get information about a specific experimenter
        
        Args:
            experimenter_type: Type of experimenter to get info for
            
        Returns:
            Dictionary containing experimenter information
            
        Raises:
            ValueError: If experimenter type is not available
        """
        if experimenter_type not in self._experimenters:
            raise ValueError(f"Experimenter type '{experimenter_type}' not available")
        
        experimenter_class = self._experimenters[experimenter_type]
        
        return {
            "name": experimenter_type,
            "class": experimenter_class.__name__,
            "module": experimenter_class.__module__,
            "available": True
        }
    
    def validate_experimenter_config(self, experimenter_type: str) -> bool:
        """Validate configuration for a specific experimenter type
        
        Args:
            experimenter_type: Type of experimenter to validate
            
        Returns:
            True if configuration is valid
        """
        if experimenter_type not in self._experimenters:
            return False
        
        try:
            # Try to create a test instance
            experimenter = self.create_experimenter(experimenter_type)
            self.logger.info(
                f"Configuration validation passed for: {experimenter_type}",
                extra={"provider_type": experimenter_type}
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Configuration validation failed for: {experimenter_type}",
                extra={
                    "provider_type": experimenter_type,
                    "error": str(e)
                }
            )
            return False


def create_experimenter_from_config(
    config_manager: ConfigManager,
    session_tracker: SessionTracker,
    llm_factory: LLMProviderFactory,
    experimenter_type: Optional[str] = None
) -> ExperimentationInterface:
    """Create experimenter from configuration
    
    Convenience function for creating experimenters with minimal setup.
    
    Args:
        config_manager: Configuration management instance
        session_tracker: Session tracking instance
        llm_factory: LLM provider factory
        experimenter_type: Specific experimenter type, or None for auto-selection
        
    Returns:
        ExperimentationInterface implementation
    """
    factory = ExperimentationFactory(config_manager, session_tracker, llm_factory)
    
    if experimenter_type:
        return factory.create_experimenter(experimenter_type)
    else:
        return factory.create_auto_experimenter()


def create_experimenter_from_env(
    config_dir: str = "config",
    experimenter_type: Optional[str] = None
) -> ExperimentationInterface:
    """Create experimenter from environment configuration
    
    Convenience function that sets up all dependencies from environment.
    
    Args:
        config_dir: Configuration directory path
        experimenter_type: Specific experimenter type, or None for auto-selection
        
    Returns:
        ExperimentationInterface implementation
    """
    # Create dependencies
    config_manager = ConfigManager(config_dir)
    session_tracker = SessionTracker()
    llm_factory = LLMProviderFactory(config_dir)
    
    return create_experimenter_from_config(
        config_manager=config_manager,
        session_tracker=session_tracker,
        llm_factory=llm_factory,
        experimenter_type=experimenter_type
    )