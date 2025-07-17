#!/usr/bin/env python3
"""
Configuration Tutorial: Agent-Centric Configuration System

This tutorial demonstrates:
1. How to use the agent-centric configuration structure
2. Creating custom agents with their own configuration
3. Environment-specific configuration overrides
4. Best practices for configuration management
5. Model and prompt management per agent

Usage:
    python scripts/configuration_tutorial.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import ConfigManager, AgentConfig
from src.core.config.agent_config_manager import AgentConfigManager
from src.nodes.answer_agent import AnswerAgentNode
from src.nodes.evaluator_agent import EvaluatorAgentNode
from src.nodes.escalation_router import EscalationRouterNode

def demo_configuration_overview():
    """Demonstrate configuration system overview"""
    print("🔍 Agent-Centric Configuration System Overview")
    print("=" * 50)
    
    # Initialize the configuration manager
    config_manager = ConfigManager("config")
    
    print(f"Configuration manager type: {type(config_manager).__name__}")
    print("✅ Using agent-centric configuration structure")
    
    summary = config_manager.get_summary()
    print(f"   Environment: {summary['environment']}")
    print(f"   System version: {summary['system_version']}")
    print(f"   Schema version: {summary['config_schema_version']}")
    print(f"   Agents loaded: {summary['agents_loaded']}")
    print(f"   Agent names: {summary['agent_names']}")
    print(f"   Agent versions: {summary['agent_versions']}")
    print(f"   Models configured: {summary['models_configured']}")
    print(f"   Versioning enabled: {summary['versioning_enabled']}")
    
    print("\n" + "=" * 50)

def demo_agent_specific_configuration():
    """Demonstrate agent-specific configuration access"""
    print("⚙️ Agent-Specific Configuration Demo")
    print("=" * 50)
    
    config_manager = ConfigManager("config")
    
    # Access agent-specific configurations
    agents = ["answer_agent", "evaluator_agent", "escalation_router"]
    
    for agent_name in agents:
        agent_config = config_manager.get_agent_config(agent_name)
        
        if agent_config:
            print(f"\n🤖 {agent_name.title().replace('_', ' ')} Configuration:")
            print(f"   Name: {agent_config.name}")
            print(f"   Description: {agent_config.description}")
            print(f"   Type: {agent_config.type}")
            print(f"   Preferred Model: {agent_config.get_preferred_model()}")
            print(f"   Fallback Models: {agent_config.get_fallback_models()}")
            print(f"   Temperature: {agent_config.get_setting('temperature', 'N/A')}")
            print(f"   Max Tokens: {agent_config.get_setting('max_tokens', 'N/A')}")
            print(f"   System Prompt: {agent_config.get_prompt('system')[:100]}...")
        else:
            print(f"\n❌ {agent_name} configuration not found")
    
    print("\n" + "=" * 50)

def demo_environment_overrides():
    """Demonstrate environment-specific configuration overrides"""
    print("🌍 Environment Configuration Overrides Demo")
    print("=" * 50)
    
    # Test different environments
    environments = ["development", "testing", "production"]
    
    for env in environments:
        try:
            config_manager = ConfigManager("config", environment=env)
            system_config = config_manager.get_system_config()
            
            print(f"\n🔧 {env.title()} Environment:")
            print(f"   Environment: {system_config.environment}")
            print(f"   Debug Mode: {system_config.thresholds.get('debug_mode', 'N/A')}")
            print(f"   Log Level: {system_config.monitoring.get('log_level', 'N/A')}")
            print(f"   Escalation Score: {system_config.thresholds.get('escalation_score', 'N/A')}")
            print(f"   Max Retries: {system_config.thresholds.get('max_retries', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Failed to load {env} environment: {e}")
    
    print("\n" + "=" * 50)

def demo_agent_initialization():
    """Demonstrate initializing agents with configuration"""
    print("🚀 Agent Initialization Demo")
    print("=" * 50)
    
    config_manager = ConfigManager("config")
    
    # Initialize agents with configuration
    agents = {}
    
    try:
        # Note: Would need context_provider for full initialization
        print("✅ Configuration manager ready for agent initialization")
        print("   - Answer Agent: Uses agent-centric config")
        print("   - Evaluator Agent: Uses agent-centric config")
        print("   - Escalation Router: Uses agent-centric config")
        
        # Show agent configurations are available
        available_agents = config_manager.get_available_agents()
        print(f"\n📊 Available agent configurations: {len(available_agents)}")
        for agent_name in available_agents:
            agent_config = config_manager.get_agent_config(agent_name)
            print(f"   - {agent_name}: {agent_config.get_preferred_model()}")
            
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
    
    print("\n" + "=" * 50)

def demo_model_configuration():
    """Demonstrate model configuration management"""
    print("🧠 Model Configuration Demo")
    print("=" * 50)
    
    config_manager = ConfigManager("config")
    
    # Global models configuration
    models_config = config_manager.get_models_config()
    
    print("🌐 Global Models Configuration:")
    models = models_config.get('models', {})
    print(f"   Total Models: {len(models)}")
    
    for model_name, model_config in list(models.items())[:3]:  # Show first 3
        print(f"\n   📦 {model_name}:")
        print(f"      Type: {model_config.get('type', 'N/A')}")
        print(f"      Description: {model_config.get('description', 'N/A')}")
        print(f"      Temperature: {model_config.get('temperature', 'N/A')}")
        print(f"      Max Tokens: {model_config.get('max_tokens', 'N/A')}")
    
    # Agent-specific model preferences
    print("\n🤖 Agent Model Preferences:")
    for agent_name in ["answer_agent", "evaluator_agent", "escalation_router"]:
        primary_model = config_manager.get_primary_model_for_agent(agent_name)
        print(f"   {agent_name}: {primary_model}")
    
    print("\n" + "=" * 50)

def demo_configuration_validation():
    """Demonstrate configuration validation"""
    print("✅ Configuration Validation Demo")
    print("=" * 50)
    
    config_manager = ConfigManager("config")
    
    if isinstance(config_manager, AgentConfigManager):
        summary = config_manager.get_summary()
        
        print("📋 Configuration Summary:")
        print(f"   Config Directory: {summary['config_directory']}")
        print(f"   Environment: {summary['environment']}")
        print(f"   System Name: {summary['system_name']}")
        print(f"   System Version: {summary['system_version']}")
        print(f"   Agents Loaded: {summary['agents_loaded']}")
        print(f"   Models Configured: {summary['models_configured']}")
        print(f"   Providers Configured: {summary['providers_configured']}")
        
        # Check configuration file structure
        print("\n📁 Configuration File Structure:")
        structure = summary['config_files_structure']
        for component, exists in structure.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {component}")
        
        # Validate agent configurations
        print("\n🔍 Agent Configuration Validation:")
        for agent_name in summary['agent_names']:
            agent_config = config_manager.get_agent_config(agent_name)
            if agent_config:
                print(f"   ✅ {agent_name}: Valid configuration")
            else:
                print(f"   ❌ {agent_name}: Invalid or missing configuration")
    else:
        print("❌ Configuration validation demo requires agent-centric structure")
    
    print("\n" + "=" * 50)

def demo_creating_custom_agent():
    """Demonstrate creating a custom agent with its own configuration"""
    print("🛠️ Custom Agent Creation Demo")
    print("=" * 50)
    
    print("📝 Steps to create a custom agent:")
    print("1. Create agent directory: config/agents/my_custom_agent/")
    print("2. Add configuration files:")
    print("   - config.yaml (agent settings)")
    print("   - prompts.yaml (agent prompts)")
    print("   - models.yaml (preferred models)")
    print("3. Implement agent class that extends base functionality")
    print("4. Register agent in system")
    
    print("\n📄 Example configuration files:")
    
    # Example config.yaml
    config_yaml = """
# config/agents/my_custom_agent/config.yaml
agent:
  name: "my_custom_agent"
  description: "Custom agent for specialized tasks"
  type: "custom_agent"

models:
  preferred: "gpt-4"
  fallback: ["claude-3-sonnet", "llama-7b"]

settings:
  temperature: 0.3
  max_tokens: 1500
  specialized_mode: true
  
behavior:
  response_style: "detailed"
  include_examples: true
"""
    
    # Example prompts.yaml
    prompts_yaml = """
# config/agents/my_custom_agent/prompts.yaml
system_prompt: >
  You are a specialized assistant for custom tasks. 
  Provide detailed, accurate responses with examples.

templates:
  detailed_response: >
    Based on your request, here's a detailed explanation:
    
    {explanation}
    
    Example: {example}
    
  error_response: >
    I apologize, but I encountered an issue: {error}
    Please try rephrasing your request.
"""
    
    print("📄 config.yaml:")
    print(config_yaml)
    print("\n📄 prompts.yaml:")
    print(prompts_yaml)
    
    print("\n💡 After creating these files, the agent will be:")
    print("   - Automatically discovered by the configuration system")
    print("   - Available for initialization and use")
    print("   - Configurable per environment")
    
    print("\n" + "=" * 50)

def demo_configuration_structure():
    """Demonstrate the configuration directory structure"""
    print("📁 Configuration Directory Structure Demo")
    print("=" * 50)
    
    print("📋 Agent-Centric Configuration Structure:")
    print("config/")
    print("├── agents/                    # Agent-specific configurations")
    print("│   ├── answer_agent/")
    print("│   │   ├── config.yaml        # Agent settings & behavior")
    print("│   │   ├── prompts.yaml       # Agent prompts & templates")
    print("│   │   └── models.yaml        # Agent model preferences")
    print("│   ├── evaluator_agent/")
    print("│   ├── escalation_router/")
    print("│   └── human_interface/")
    print("├── shared/                    # Global configurations")
    print("│   ├── models.yaml            # Master model definitions")
    print("│   ├── system.yaml            # System-wide settings")
    print("│   └── providers.yaml         # Provider configurations")
    print("├── environments/              # Environment-specific overrides")
    print("│   ├── development.yaml")
    print("│   ├── testing.yaml")
    print("│   └── production.yaml")
    print("└── config.yaml                # Main configuration coordinator")
    
    print("\n✅ Benefits of this structure:")
    print("   - Agent isolation and modularity")
    print("   - Easy agent development and testing")
    print("   - Environment-specific configuration")
    print("   - Hot-reloading support")
    print("   - Better validation and error handling")
    print("   - Clear separation of concerns")
    
    print("\n" + "=" * 50)

def demo_best_practices():
    """Demonstrate configuration best practices"""
    print("💡 Configuration Best Practices Demo")
    print("=" * 50)
    
    print("🎯 Best Practices:")
    print("")
    print("1. Agent Organization:")
    print("   ✅ One directory per agent in config/agents/")
    print("   ✅ Consistent naming: snake_case for agent names")
    print("   ✅ Clear descriptions in agent.description")
    print("")
    print("2. Configuration Structure:")
    print("   ✅ Keep shared configs in config/shared/")
    print("   ✅ Use environment overrides for deployment differences")
    print("   ✅ Prefer YAML over JSON for readability")
    print("")
    print("3. Model Configuration:")
    print("   ✅ Define global models in shared/models.yaml")
    print("   ✅ Use agent-specific model preferences")
    print("   ✅ Always provide fallback models")
    print("")
    print("4. Prompt Management:")
    print("   ✅ Use template variables for dynamic content")
    print("   ✅ Keep prompts in separate files from settings")
    print("   ✅ Version your prompts for A/B testing")
    print("")
    print("5. Environment Management:")
    print("   ✅ Use environment variables for secrets")
    print("   ✅ Keep environment-specific configs minimal")
    print("   ✅ Test all environments before deployment")
    print("")
    print("6. Validation:")
    print("   ✅ Validate configuration on startup")
    print("   ✅ Use descriptive error messages")
    print("   ✅ Implement configuration health checks")
    
    print("\n" + "=" * 50)

def main():
    """Main tutorial function"""
    print("🎓 Configuration Tutorial: Agent-Centric Configuration System")
    print("=" * 60)
    print("This tutorial demonstrates the agent-centric configuration system")
    print("and best practices for configuration management.")
    print("")
    
    try:
        # Run tutorial sections
        demo_configuration_overview()
        demo_agent_specific_configuration()
        demo_environment_overrides()
        demo_agent_initialization()
        demo_model_configuration()
        demo_configuration_validation()
        demo_creating_custom_agent()
        demo_configuration_structure()
        demo_best_practices()
        
        print("✅ Tutorial completed successfully!")
        print("")
        print("🚀 Next Steps:")
        print("1. Try creating your own custom agent")
        print("2. Experiment with different environment configurations")
        print("3. Set up A/B testing for prompts")
        print("4. Implement configuration hot-reloading")
        print("5. Explore advanced agent settings and behaviors")
        
    except KeyboardInterrupt:
        print("\n\n❌ Tutorial interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Tutorial failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()