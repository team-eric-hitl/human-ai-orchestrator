"""
Entry point demonstrating the modular system with local LLMs

Run with: uv run python main.py
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from src.workflows.hybrid_workflow import HybridSystemWorkflow
from src.integrations.langsmith_setup import setup_langsmith
from src.core.logging import get_logger, setup_development_logging

def setup_environment():
    """Setup logging, LangSmith and configuration-based environment"""
    load_dotenv()
    
    # Setup logging first
    setup_development_logging()
    logger = get_logger("main")
    
    logger.info("Starting hybrid AI system initialization")
    
    # Setup LangSmith
    setup_langsmith()
    
    # Load and validate configuration
    try:
        from src.core.config import ConfigManager
        config_manager = ConfigManager("config")
        
        # Get configuration summary
        summary = config_manager.get_summary()
        
        logger.info("Configuration loaded successfully", extra={
            "provider_strategy": summary['provider_strategy'],
            "primary_model": summary['primary_model'],
            "available_models_count": len(summary['available_models']),
            "total_models_configured": summary['total_models_configured']
        })
        
        print(f"🚀 Configuration Summary:")
        print(f"   Provider Strategy: {summary['provider_strategy']}")
        print(f"   Primary Model: {summary['primary_model']} ({summary.get('primary_model_type', 'unknown')})")
        print(f"   Available Models: {len(summary['available_models'])}/{summary['total_models_configured']}")
        
        if summary['available_models']:
            print(f"   ✅ Available: {', '.join(summary['available_models'])}")
        
        # Show validation results for local models
        validation_results = summary.get('validation_results', {})
        missing_models = [name for name, valid in validation_results.items() if not valid]
        
        if missing_models:
            logger.warning("Missing model files detected", extra={
                "missing_models": missing_models
            })
            print(f"   ⚠️  Missing model files: {', '.join(missing_models)}")
            print("      Download model files or update paths in config/models.yaml")
        
        logger.info("Environment setup completed successfully")
        print("✅ Environment setup complete")
        return True
        
    except Exception as e:
        logger.error("Configuration setup failed", exc_info=True, extra={
            "error": str(e)
        })
        print(f"❌ Configuration error: {e}")
        print("Please check your config files in the config/ directory")
        return False

def main():
    """Main demonstration"""
    if not setup_environment():
        return
    
    logger = get_logger("main")
    
    # Initialize the complete hybrid system
    try:
        logger.info("Initializing hybrid system workflow")
        hybrid_system = HybridSystemWorkflow(
            config_dir="config",
            context_db="hybrid_system.db"
        )
        logger.info("Hybrid system workflow initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize hybrid system", exc_info=True, extra={
            "error": str(e)
        })
        print(f"❌ Failed to initialize hybrid system: {e}")
        print("Please check your configuration and model files")
        return
    
    # Demo conversation
    user_id = "demo_user"
    
    demo_queries = [
        "How do I reset my password?",
        "That didn't work, can you help me with a different approach?",
        "I'm getting frustrated, I need to speak to someone"
    ]
    
    print("=== Modular LangGraph Hybrid System Demo (Config-Based) ===")
    print("Each module is a separate, testable LangGraph node!")
    print("Using configuration-driven model management!")
    print()
    
    for i, query in enumerate(demo_queries, 1):
        print(f"--- Query {i}: {query} ---")
        
        try:
            result = hybrid_system.process_query(
                query=query,
                user_id=user_id,
                session_id="demo_session"
            )
            
            print(f"Result: {'Escalated' if result['escalated'] else 'AI Handled'}")
            if result['escalated']:
                escalation = result['escalation_data']
                print(f"Priority: {escalation.priority}")
                print(f"Assigned to: {escalation.suggested_human_id or 'Queue'}")
            else:
                print(f"Response: {result['final_response']}")
                
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print()
    
    print("✅ All interactions automatically tracked in LangSmith!")
    print("🔍 View traces, costs, and performance in LangSmith dashboard")
    print("⚙️  Model configuration managed through config/models.yaml and config/llm.yaml")

if __name__ == "__main__":
    main() 