#!/usr/bin/env python3
"""
Experimentation Demo Script

This script demonstrates how to use the experimentation module to:
1. Test different prompts
2. Optimize thresholds
3. Compare models
4. Run continuous optimization

Usage:
    python scripts/experimentation_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime
from typing import List

from src.core.config import ConfigManager
from src.core.session_tracker import SessionTracker
from src.integrations.experimentation import ExperimentationFactory
from src.integrations.llm_providers import LLMProviderFactory
from src.interfaces.experimentation import (
    OptimizationTarget,
    PromptVariant,
    ThresholdExperiment,
)


def create_sample_prompt_variants() -> List[PromptVariant]:
    """Create sample prompt variants for testing"""
    return [
        PromptVariant(
            name="friendly_assistant",
            system_prompt="You are a friendly and helpful AI assistant. Always be polite and encouraging.",
            user_prompt_template="User question: {query}\n\nPlease provide a helpful response:",
            parameters={"style": "friendly", "tone": "encouraging"},
            metadata={"category": "customer_service", "version": "1.0"}
        ),
        PromptVariant(
            name="technical_expert",
            system_prompt="You are a technical expert. Provide detailed, accurate, and precise responses.",
            user_prompt_template="Technical query: {query}\n\nProvide a detailed technical response:",
            parameters={"style": "technical", "tone": "precise"},
            metadata={"category": "technical_support", "version": "1.0"}
        ),
        PromptVariant(
            name="concise_responder",
            system_prompt="You are a concise AI assistant. Keep responses brief and to the point.",
            user_prompt_template="Question: {query}\n\nBrief answer:",
            parameters={"style": "concise", "tone": "direct"},
            metadata={"category": "quick_help", "version": "1.0"}
        )
    ]


def create_sample_test_cases() -> List[str]:
    """Create sample test cases for experimentation"""
    return [
        "How do I reset my password?",
        "What are the system requirements for the software?",
        "I'm having trouble with the installation process.",
        "Can you explain how the API authentication works?",
        "What's the best way to optimize database performance?",
        "How do I troubleshoot network connectivity issues?",
        "Can you help me understand the pricing structure?",
        "What are the security best practices for this platform?"
    ]


def create_sample_threshold_experiments() -> List[ThresholdExperiment]:
    """Create sample threshold experiments"""
    test_cases = [
        "This is a complex technical question about system architecture.",
        "I need help with a simple password reset.",
        "Can you explain quantum computing in detail?",
        "What time does the store close?",
        "I'm having a critical system outage issue."
    ]
    
    return [
        ThresholdExperiment(
            parameter_name="confidence_threshold",
            min_value=0.5,
            max_value=0.9,
            step_size=0.1,
            test_cases=test_cases,
            metadata={"description": "Optimize confidence threshold for escalation"}
        ),
        ThresholdExperiment(
            parameter_name="escalation_score",
            min_value=4.0,
            max_value=8.0,
            step_size=0.5,
            test_cases=test_cases,
            metadata={"description": "Optimize escalation score threshold"}
        )
    ]


def demo_prompt_experiments():
    """Demonstrate prompt experimentation"""
    print("🧪 Running Prompt Experiments Demo")
    print("=" * 50)
    
    # Setup
    config_manager = ConfigManager("config")
    session_tracker = SessionTracker()
    llm_factory = LLMProviderFactory("config")
    
    # Create experimenter
    factory = ExperimentationFactory(config_manager, session_tracker, llm_factory)
    experimenter = factory.create_auto_experimenter()
    
    # Prepare experiment data
    variants = create_sample_prompt_variants()
    test_cases = create_sample_test_cases()[:3]  # Use first 3 for demo
    
    print(f"Testing {len(variants)} prompt variants on {len(test_cases)} test cases")
    print("Variants:", [v.name for v in variants])
    print("Test cases:", [tc[:50] + "..." if len(tc) > 50 else tc for tc in test_cases])
    print()
    
    # Run experiments
    try:
        results = experimenter.run_prompt_experiments(
            variants=variants,
            test_cases=test_cases,
            agent_type="answer_agent",
            iterations=2
        )
        
        # Display results
        print("Results:")
        print(f"  Total experiments: {results.total_experiments}")
        print(f"  Successful experiments: {results.successful_experiments}")
        print(f"  Success rate: {results.success_rate:.1f}%")
        print(f"  Duration: {results.duration_seconds:.2f} seconds")
        print(f"  Best variant: {results.best_variant}")
        print(f"  Best score: {results.best_score:.2f}")
        
        # Show variant scores
        print("\nVariant Scores:")
        variant_scores = results.get_variant_scores()
        for variant, score in variant_scores.items():
            print(f"  {variant}: {score:.2f}")
        
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
    
    print("\n" + "=" * 50)


def demo_threshold_experiments():
    """Demonstrate threshold experimentation"""
    print("🎯 Running Threshold Experiments Demo")
    print("=" * 50)
    
    # Setup
    config_manager = ConfigManager("config")
    session_tracker = SessionTracker()
    llm_factory = LLMProviderFactory("config")
    
    # Create experimenter
    factory = ExperimentationFactory(config_manager, session_tracker, llm_factory)
    experimenter = factory.create_auto_experimenter()
    
    # Prepare experiment data
    experiments = create_sample_threshold_experiments()[:1]  # Use first experiment for demo
    
    print(f"Testing {len(experiments)} threshold parameters")
    for exp in experiments:
        print(f"  {exp.parameter_name}: {exp.min_value} to {exp.max_value} (step: {exp.step_size})")
    print()
    
    # Run experiments
    try:
        results = experimenter.run_threshold_experiments(
            experiments=experiments,
            agent_type="evaluator_agent"
        )
        
        # Display results
        print("Results:")
        print(f"  Total experiments: {results.total_experiments}")
        print(f"  Successful experiments: {results.successful_experiments}")
        print(f"  Success rate: {results.success_rate:.1f}%")
        print(f"  Duration: {results.duration_seconds:.2f} seconds")
        print(f"  Best configuration: {results.best_variant}")
        print(f"  Best score: {results.best_score:.2f}")
        
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
    
    print("\n" + "=" * 50)


def demo_continuous_optimization():
    """Demonstrate continuous optimization"""
    print("🔄 Running Continuous Optimization Demo")
    print("=" * 50)
    
    # Setup
    config_manager = ConfigManager("config")
    session_tracker = SessionTracker()
    llm_factory = LLMProviderFactory("config")
    
    # Create experimenter
    factory = ExperimentationFactory(config_manager, session_tracker, llm_factory)
    experimenter = factory.create_auto_experimenter()
    
    # Prepare experiment data
    test_cases = create_sample_test_cases()[:2]  # Use first 2 for demo
    target = OptimizationTarget.OVERALL_SCORE
    
    print(f"Optimizing for: {target.value}")
    print(f"Test cases: {len(test_cases)}")
    print(f"Iterations: 3")
    print()
    
    # Run optimization
    try:
        results = experimenter.run_continuous_optimization(
            target=target,
            test_cases=test_cases,
            iterations=3,
            agent_type="answer_agent"
        )
        
        # Display results
        print("Results:")
        print(f"  Total experiments: {results.total_experiments}")
        print(f"  Successful experiments: {results.successful_experiments}")
        print(f"  Success rate: {results.success_rate:.1f}%")
        print(f"  Duration: {results.duration_seconds:.2f} seconds")
        print(f"  Best configuration: {results.best_variant}")
        print(f"  Best score: {results.best_score:.2f}")
        
        # Show optimization progress
        if results.metadata.get("final_config"):
            print(f"  Final config: {results.metadata['final_config']}")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
    
    print("\n" + "=" * 50)


def demo_model_comparison():
    """Demonstrate model comparison"""
    print("⚖️ Running Model Comparison Demo")
    print("=" * 50)
    
    # Setup
    config_manager = ConfigManager("config")
    session_tracker = SessionTracker()
    llm_factory = LLMProviderFactory("config")
    
    # Create experimenter
    factory = ExperimentationFactory(config_manager, session_tracker, llm_factory)
    experimenter = factory.create_auto_experimenter()
    
    # Get available models
    available_models = config_manager.get_available_models()
    model_names = [model.name for model in available_models[:2]]  # Use first 2 models
    
    if not model_names:
        print("❌ No models available for comparison")
        return
    
    # Prepare experiment data
    test_cases = create_sample_test_cases()[:2]  # Use first 2 for demo
    
    print(f"Comparing {len(model_names)} models:")
    for model in model_names:
        print(f"  - {model}")
    print(f"Test cases: {len(test_cases)}")
    print()
    
    # Run comparison
    try:
        results = experimenter.run_model_comparison(
            model_names=model_names,
            test_cases=test_cases,
            agent_type="answer_agent"
        )
        
        # Display results
        print("Results:")
        print(f"  Total experiments: {results.total_experiments}")
        print(f"  Successful experiments: {results.successful_experiments}")
        print(f"  Success rate: {results.success_rate:.1f}%")
        print(f"  Duration: {results.duration_seconds:.2f} seconds")
        print(f"  Best model: {results.best_variant}")
        print(f"  Best score: {results.best_score:.2f}")
        
        # Show model scores
        print("\nModel Scores:")
        variant_scores = results.get_variant_scores()
        for model, score in variant_scores.items():
            print(f"  {model}: {score:.2f}")
        
    except Exception as e:
        print(f"❌ Model comparison failed: {e}")
    
    print("\n" + "=" * 50)


def demo_experiment_history():
    """Demonstrate experiment history tracking"""
    print("📊 Experiment History Demo")
    print("=" * 50)
    
    # Setup
    config_manager = ConfigManager("config")
    session_tracker = SessionTracker()
    llm_factory = LLMProviderFactory("config")
    
    # Create experimenter
    factory = ExperimentationFactory(config_manager, session_tracker, llm_factory)
    experimenter = factory.create_auto_experimenter()
    
    # Get experiment history
    history = experimenter.get_experiment_history()
    
    print(f"Total experiments in history: {len(history)}")
    
    if history:
        print("\nRecent experiments:")
        for i, exp in enumerate(history[:3]):  # Show first 3
            print(f"  {i+1}. {exp.experiment_type}")
            print(f"     Time: {exp.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Results: {exp.successful_experiments}/{exp.total_experiments}")
            print(f"     Best: {exp.best_variant} ({exp.best_score:.2f})")
            print()
    else:
        print("No experiments in history yet.")
    
    print("=" * 50)


def main():
    """Main demo function"""
    print("🚀 Experimentation Module Demo")
    print("=" * 60)
    print()
    
    try:
        # Run demos
        demo_prompt_experiments()
        demo_threshold_experiments()
        demo_continuous_optimization()
        demo_model_comparison()
        demo_experiment_history()
        
        print("✅ All demos completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()