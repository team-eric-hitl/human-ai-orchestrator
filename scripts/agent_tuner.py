#!/usr/bin/env python3
"""
Agent Settings Tuner
Interactive tool for adjusting agent settings based on simulation results
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.core.logging import get_logger


class AgentTuner:
    """Interactive agent settings tuner"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_manager = ConfigManager(str(config_dir))
        self.logger = get_logger(__name__)
        
        # Common tuning parameters
        self.tuning_params = {
            "quality_agent": {
                "adequate_threshold": {"min": 5.0, "max": 9.0, "step": 0.5, "description": "Score threshold for adequate responses"},
                "intervention_threshold": {"min": 3.0, "max": 7.0, "step": 0.5, "description": "Score threshold for quality intervention"},
                "confidence_weight": {"min": 0.1, "max": 1.0, "step": 0.1, "description": "Weight for confidence in decisions"},
            },
            "frustration_agent": {
                "intervention_threshold": {"min": 4.0, "max": 8.0, "step": 0.5, "description": "Frustration score threshold for intervention"},
                "critical_threshold": {"min": 7.0, "max": 10.0, "step": 0.5, "description": "Critical frustration threshold"},
                "confidence_threshold": {"min": 0.5, "max": 0.9, "step": 0.1, "description": "Minimum confidence for decisions"},
            },
            "routing_agent": {
                "workload_balance_weight": {"min": 0.1, "max": 1.0, "step": 0.1, "description": "Weight for workload balancing"},
                "skill_match_weight": {"min": 0.1, "max": 1.0, "step": 0.1, "description": "Weight for skill matching"},
                "min_match_score": {"min": 0.5, "max": 0.9, "step": 0.1, "description": "Minimum match score for routing"},
            },
            "chatbot_agent": {
                "response_confidence_threshold": {"min": 0.5, "max": 0.9, "step": 0.1, "description": "Confidence threshold for responses"},
                "max_response_length": {"min": 100, "max": 500, "step": 50, "description": "Maximum response length"},
            }
        }
    
    def show_current_settings(self, agent_name: str) -> Dict[str, Any]:
        """Show current settings for an agent"""
        try:
            agent_config = self.config_manager.get_agent_config(agent_name)
            return agent_config.settings
        except Exception as e:
            self.logger.error(f"Could not load settings for {agent_name}: {e}")
            return {}
    
    def update_agent_setting(self, agent_name: str, setting_name: str, new_value: Any) -> bool:
        """Update a specific agent setting"""
        try:
            config_file = self.config_dir / "agents" / agent_name / "config.yaml"
            
            if not config_file.exists():
                self.logger.error(f"Config file not found: {config_file}")
                return False
            
            # Load current config
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update setting
            if "settings" not in config:
                config["settings"] = {}
            
            config["settings"][setting_name] = new_value
            
            # Save updated config
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Updated {agent_name}.{setting_name} = {new_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update {agent_name}.{setting_name}: {e}")
            return False
    
    def suggest_adjustments(self, metrics_summary: Dict[str, Any]) -> Dict[str, List[str]]:
        """Suggest setting adjustments based on metrics"""
        suggestions = {
            "quality_agent": [],
            "frustration_agent": [],
            "routing_agent": [],
            "chatbot_agent": []
        }
        
        # Quality agent suggestions
        if "quality_agent_accuracy" in metrics_summary:
            accuracy = metrics_summary["quality_agent_accuracy"]
            if accuracy < 0.7:
                suggestions["quality_agent"].append(
                    "🔴 Low accuracy - consider adjusting adequate_threshold (currently too strict or too lenient)"
                )
                suggestions["quality_agent"].append(
                    "💡 Try decreasing adequate_threshold by 0.5-1.0 if too many adequate responses are flagged"
                )
                suggestions["quality_agent"].append(
                    "💡 Try increasing adequate_threshold by 0.5-1.0 if poor responses are marked adequate"
                )
        
        # Frustration agent suggestions
        if "frustration_detection_precision" in metrics_summary:
            precision = metrics_summary["frustration_detection_precision"]
            if precision < 0.7:
                suggestions["frustration_agent"].append(
                    "🔴 Low precision - too many false positives in frustration detection"
                )
                suggestions["frustration_agent"].append(
                    "💡 Try increasing intervention_threshold by 0.5-1.0 to reduce false positives"
                )
        
        # Escalation rate suggestions
        if "escalation_rate" in metrics_summary:
            escalation_rate = metrics_summary["escalation_rate"]
            if escalation_rate > 0.6:
                suggestions["quality_agent"].append(
                    "🟡 High escalation rate - chatbot responses may need improvement"
                )
                suggestions["quality_agent"].append(
                    "💡 Consider decreasing intervention_threshold to be more tolerant of responses"
                )
                suggestions["frustration_agent"].append(
                    "💡 Consider increasing intervention_threshold to reduce frustration interventions"
                )
            elif escalation_rate < 0.2:
                suggestions["quality_agent"].append(
                    "🟡 Low escalation rate - may be missing issues that need human attention"
                )
                suggestions["quality_agent"].append(
                    "💡 Consider decreasing adequate_threshold to catch more quality issues"
                )
        
        # Customer satisfaction suggestions
        if "avg_customer_satisfaction" in metrics_summary:
            satisfaction = metrics_summary["avg_customer_satisfaction"]
            if satisfaction < 7.0:
                suggestions["chatbot_agent"].append(
                    "🔴 Low customer satisfaction - chatbot responses need improvement"
                )
                suggestions["quality_agent"].append(
                    "💡 Consider decreasing adequate_threshold to catch more quality issues"
                )
                suggestions["routing_agent"].append(
                    "💡 Consider increasing skill_match_weight for better agent selection"
                )
        
        # Routing success suggestions
        if "routing_success_rate" in metrics_summary:
            routing_success = metrics_summary["routing_success_rate"]
            if routing_success < 0.8:
                suggestions["routing_agent"].append(
                    "🔴 Low routing success - agent matching needs improvement"
                )
                suggestions["routing_agent"].append(
                    "💡 Try decreasing min_match_score to allow more routing options"
                )
                suggestions["routing_agent"].append(
                    "💡 Try increasing skill_match_weight for better specialization matching"
                )
        
        # Remove empty suggestion lists
        return {k: v for k, v in suggestions.items() if v}
    
    def interactive_tuning_session(self):
        """Run an interactive tuning session"""
        print("🎛️  Agent Settings Tuner")
        print("=" * 50)
        
        while True:
            print("\n📋 Available Agents:")
            agents = ["quality_agent", "frustration_agent", "routing_agent", "chatbot_agent"]
            for i, agent in enumerate(agents, 1):
                print(f"  {i}. {agent}")
            
            print("\n⚙️  Options:")
            print("  v) View current settings")
            print("  u) Update setting")
            print("  s) Show tuning suggestions (requires metrics)")
            print("  r) Reset to defaults")
            print("  x) Exit")
            
            choice = input("\nSelect option: ").strip().lower()
            
            if choice == 'x':
                print("👋 Goodbye!")
                break
            elif choice == 'v':
                self._view_settings_menu()
            elif choice == 'u':
                self._update_setting_menu()
            elif choice == 's':
                self._show_suggestions_menu()
            elif choice == 'r':
                self._reset_defaults_menu()
            else:
                print("❌ Invalid choice. Please try again.")
    
    def _view_settings_menu(self):
        """View current settings menu"""
        print("\n👁️  View Settings")
        agent_name = self._select_agent()
        if not agent_name:
            return
        
        settings = self.show_current_settings(agent_name)
        if settings:
            print(f"\n📄 Current settings for {agent_name}:")
            for key, value in settings.items():
                print(f"  • {key}: {value}")
        else:
            print(f"❌ No settings found for {agent_name}")
    
    def _update_setting_menu(self):
        """Update setting menu"""
        print("\n✏️  Update Setting")
        agent_name = self._select_agent()
        if not agent_name:
            return
        
        # Show available tuning parameters for this agent
        if agent_name in self.tuning_params:
            print(f"\n🎛️  Tunable parameters for {agent_name}:")
            params = self.tuning_params[agent_name]
            for i, (param_name, param_info) in enumerate(params.items(), 1):
                print(f"  {i}. {param_name}: {param_info['description']}")
                print(f"     Range: {param_info['min']}-{param_info['max']}, Step: {param_info['step']}")
            
            # Select parameter
            try:
                choice = input("\nSelect parameter number: ").strip()
                param_names = list(params.keys())
                param_name = param_names[int(choice) - 1]
                param_info = params[param_name]
                
                # Get current value
                current_settings = self.show_current_settings(agent_name)
                current_value = current_settings.get(param_name, "not set")
                print(f"\nCurrent value: {current_value}")
                print(f"Valid range: {param_info['min']}-{param_info['max']} (step: {param_info['step']})")
                
                # Get new value
                new_value = input("Enter new value: ").strip()
                
                # Validate and convert
                try:
                    if isinstance(param_info['min'], float):
                        new_value = float(new_value)
                    else:
                        new_value = int(new_value)
                    
                    if param_info['min'] <= new_value <= param_info['max']:
                        if self.update_agent_setting(agent_name, param_name, new_value):
                            print(f"✅ Updated {agent_name}.{param_name} = {new_value}")
                        else:
                            print(f"❌ Failed to update setting")
                    else:
                        print(f"❌ Value out of range: {param_info['min']}-{param_info['max']}")
                        
                except ValueError:
                    print("❌ Invalid value format")
                    
            except (ValueError, IndexError):
                print("❌ Invalid parameter selection")
        else:
            print(f"❌ No tunable parameters defined for {agent_name}")
    
    def _show_suggestions_menu(self):
        """Show tuning suggestions menu"""
        print("\n💡 Tuning Suggestions")
        print("This requires metrics from a recent simulation run.")
        
        # For now, show example suggestions
        print("\nExample metrics-based suggestions:")
        example_metrics = {
            "avg_customer_satisfaction": 6.5,
            "escalation_rate": 0.7,
            "quality_agent_accuracy": 0.6,
            "frustration_detection_precision": 0.65,
            "routing_success_rate": 0.75
        }
        
        suggestions = self.suggest_adjustments(example_metrics)
        
        for agent_name, agent_suggestions in suggestions.items():
            if agent_suggestions:
                print(f"\n🤖 {agent_name}:")
                for suggestion in agent_suggestions:
                    print(f"  {suggestion}")
        
        print("\n💭 To get real suggestions, run a simulation test first and provide the metrics.")
    
    def _reset_defaults_menu(self):
        """Reset to defaults menu"""
        print("\n🔄 Reset to Defaults")
        agent_name = self._select_agent()
        if not agent_name:
            return
        
        confirm = input(f"⚠️  Are you sure you want to reset {agent_name} to defaults? (y/N): ").strip().lower()
        if confirm == 'y':
            # This would reset to default values - implementation depends on having default configs
            print(f"🔄 Reset {agent_name} to defaults (feature not fully implemented yet)")
        else:
            print("❌ Reset cancelled")
    
    def _select_agent(self) -> str:
        """Select an agent from the available options"""
        agents = ["quality_agent", "frustration_agent", "routing_agent", "chatbot_agent"]
        
        print("\nSelect agent:")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent}")
        
        try:
            choice = input("Enter agent number: ").strip()
            return agents[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid agent selection")
            return None


def main():
    """Main function"""
    tuner = AgentTuner()
    tuner.interactive_tuning_session()


if __name__ == "__main__":
    main()