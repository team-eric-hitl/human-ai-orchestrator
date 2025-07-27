# Human Routing Agent - Configuration Examples

## Overview

This document provides practical examples of how to configure the enhanced Human Routing Agent system for different scenarios and requirements. These examples demonstrate the flexibility and power of the configurable scoring algorithm.

## Configuration File Structure

The enhanced system uses multiple configuration files organized by purpose:

```
config/agents/routing_agent/
├── config.yaml                    # Main agent configuration  
├── scoring_weights.yaml           # Scoring algorithm configuration
├── wellbeing_thresholds.yaml      # Employee protection settings
├── queue_management.yaml          # Queue behavior settings
├── performance_targets.yaml       # Performance benchmarks
├── availability_rules.yaml        # Availability calculation rules
└── escalation_policies.yaml       # Escalation handling policies
```

## Example 1: Customer-First Configuration

This configuration prioritizes customer experience above all else, suitable for high-value customer segments.

### scoring_weights.yaml - Customer-First
```yaml
scoring_algorithm:
  version: "2.0"
  description: "Customer-first routing prioritizing satisfaction and quick resolution"
  
  # Heavily weight skill matching and performance for customer satisfaction
  category_weights:
    skill_match: 0.45           # Maximum skill alignment
    performance_history: 0.30   # Strong performance preference
    availability: 0.15          # Reduced availability consideration
    wellbeing_factors: 0.05     # Minimal wellbeing consideration
    customer_factors: 0.05      # Standard customer considerations
    
  skill_match_scoring:
    exact_domain_match: 20      # High bonus for exact matches
    partial_domain_match: 10    # Good bonus for partial matches
    proficiency_bonus:
      expert: 15                # Premium for expert knowledge
      advanced: 10
      intermediate: 5
      basic: 0
    experience_years_multiplier: 1.0  # Strong experience preference
    specialization_match: 15    # High bonus for specializations
    certification_bonus: 8      # Value certifications
    
  performance_history_scoring:
    customer_satisfaction:
      weight: 0.5               # 50% of performance score from satisfaction
      scale_multiplier: 6       # Higher impact of satisfaction scores
    resolution_time:
      weight: 0.3
      baseline_minutes: 20      # Aggressive resolution time target
      penalty_per_minute_over: -0.5
      bonus_per_minute_under: 0.3
    escalation_rate:
      weight: 0.15
      penalty_multiplier: -75   # Heavy penalty for escalations
    first_contact_resolution:
      weight: 0.05
      bonus_multiplier: 25
      
  availability_scoring:
    status_scores:
      available: 15             # Reduced from default
      busy_low_load: 8
      busy_medium_load: 3
      busy_high_load: -3
      break: -15
      offline: -50
    workload_penalties:
      per_active_case: -1       # Reduced penalty
      over_capacity_penalty: -8  # Reduced penalty
      
  wellbeing_factors_scoring:
    consecutive_difficult_cases:
      1_case: -1                # Reduced penalties
      2_cases: -2
      3_cases: -4
      4_plus_cases: -8
    stress_score_penalty: -5    # Reduced stress consideration

priority_adjustments:
  critical:
    skill_match_weight: 0.55    # Even higher skill focus for critical issues
    performance_history_weight: 0.35
    availability_weight: 0.08
    wellbeing_factors_weight: 0.02
```

### wellbeing_thresholds.yaml - Customer-First
```yaml
employee_wellbeing:
  # Relaxed wellbeing protections for customer-first approach
  max_consecutive_difficult_cases: 5        # Higher tolerance
  frustration_cooldown_hours: 1             # Shorter cooldown
  stress_score_alert_threshold: 0.8         # Higher stress tolerance
  mandatory_break_stress_threshold: 0.9     # Only break at very high stress
  
  workload_protection:
    max_utilization_percentage: 95          # Allow higher utilization
    overload_alert_threshold: 100           # Alert only at full capacity
    
  escalation_protection:
    max_escalations_per_day: 15             # Higher escalation tolerance
    escalation_cooldown_minutes: 30         # Shorter cooldown between escalations
```

## Example 2: Employee Wellbeing-Focused Configuration

This configuration prioritizes employee satisfaction and sustainable workloads, suitable for teams with high turnover or burnout concerns.

### scoring_weights.yaml - Wellbeing-Focused
```yaml
scoring_algorithm:
  version: "2.0"
  description: "Employee wellbeing focused routing ensuring sustainable workloads"
  
  # Balance customer needs with strong employee protection
  category_weights:
    skill_match: 0.25           # Reduced skill importance
    availability: 0.30          # High availability consideration
    performance_history: 0.15   # Reduced performance pressure
    wellbeing_factors: 0.25     # High wellbeing protection
    customer_factors: 0.05      # Standard customer considerations
    
  skill_match_scoring:
    exact_domain_match: 12      # Moderate bonus for exact matches
    partial_domain_match: 8     # Accept partial matches more readily
    proficiency_bonus:
      expert: 8                 # Reduced pressure on expert agents
      advanced: 6
      intermediate: 4
      basic: 2                  # Give juniors more opportunities
    experience_years_multiplier: 0.3  # Reduced experience pressure
    specialization_match: 8     # Moderate specialization bonus
    certification_bonus: 3      # Reduced certification pressure
    
  availability_scoring:
    status_scores:
      available: 25             # Strong bonus for available agents
      busy_low_load: 15         # Good bonus for low-load agents
      busy_medium_load: 5       # Small bonus for medium-load
      busy_high_load: -10       # Penalty for high-load agents
      break: -25                # Respect break time
      offline: -50
    workload_penalties:
      per_active_case: -3       # Strong penalty per case
      over_capacity_penalty: -20 # Heavy penalty for overloading
    time_since_last_case_bonus: 0.2  # Bonus for rest time
    
  wellbeing_factors_scoring:
    consecutive_difficult_cases:
      1_case: -3                # Higher penalties
      2_cases: -8
      3_cases: -15
      4_plus_cases: -30
    time_since_difficult_case:
      under_1_hour: -10         # Strong protection period
      1_2_hours: -5
      2_4_hours: 0
      over_4_hours: 5
    stress_score_penalty: -20   # High stress consideration
    break_recency_bonus:
      under_30_min: 8           # Reward recent breaks
      30_60_min: 5
      1_2_hours: 2
      over_2_hours: 0
      
priority_adjustments:
  critical:
    # Even for critical issues, maintain wellbeing focus
    skill_match_weight: 0.35
    performance_history_weight: 0.20
    availability_weight: 0.25
    wellbeing_factors_weight: 0.15
    customer_factors_weight: 0.05
    
  low:
    # For low priority, maximize wellbeing consideration
    skill_match_weight: 0.15
    availability_weight: 0.40
    performance_history_weight: 0.10
    wellbeing_factors_weight: 0.30
    customer_factors_weight: 0.05
```

### wellbeing_thresholds.yaml - Wellbeing-Focused
```yaml
employee_wellbeing:
  # Strong wellbeing protections
  max_consecutive_difficult_cases: 2        # Low tolerance for difficult cases
  frustration_cooldown_hours: 4             # Long cooldown period
  stress_score_alert_threshold: 0.6         # Early stress intervention
  mandatory_break_stress_threshold: 0.7     # Mandatory breaks at moderate stress
  
  workload_protection:
    max_utilization_percentage: 80          # Conservative utilization target
    overload_alert_threshold: 85            # Early overload alerts
    ideal_utilization_percentage: 70        # Target utilization
    
  escalation_protection:
    max_escalations_per_day: 8              # Low escalation tolerance
    escalation_cooldown_minutes: 90         # Long cooldown between escalations
    
  skill_development:
    junior_case_complexity_limit: "medium"  # Protect junior agents from complex cases
    learning_opportunity_bonus: 5           # Bonus for skill development opportunities
    cross_training_cases_per_week: 3        # Encourage cross-training
```

## Example 3: Balanced Production Configuration

This configuration provides a balanced approach suitable for most production environments.

### scoring_weights.yaml - Balanced Production
```yaml
scoring_algorithm:
  version: "2.0"
  description: "Balanced production routing optimizing multiple factors"
  
  # Well-balanced weights for production use
  category_weights:
    skill_match: 0.35           # Primary consideration
    availability: 0.25          # Important for efficiency
    performance_history: 0.20   # Moderate performance consideration
    wellbeing_factors: 0.15     # Reasonable wellbeing protection
    customer_factors: 0.05      # Standard customer considerations
    
  skill_match_scoring:
    exact_domain_match: 15
    partial_domain_match: 8
    proficiency_bonus:
      expert: 10
      advanced: 7
      intermediate: 4
      basic: 1
    experience_years_multiplier: 0.5
    specialization_match: 12
    certification_bonus: 5
    
  availability_scoring:
    status_scores:
      available: 20
      busy_low_load: 10
      busy_medium_load: 5
      busy_high_load: -5
      break: -10
      offline: -50
    workload_penalties:
      per_active_case: -2
      over_capacity_penalty: -15
    time_since_last_case_bonus: 0.1
    
  performance_history_scoring:
    customer_satisfaction:
      weight: 0.4
      scale_multiplier: 4
    resolution_time:
      weight: 0.3
      baseline_minutes: 25
      penalty_per_minute_over: -0.2
      bonus_per_minute_under: 0.1
    escalation_rate:
      weight: 0.2
      penalty_multiplier: -50
    first_contact_resolution:
      weight: 0.1
      bonus_multiplier: 20
      
  wellbeing_factors_scoring:
    consecutive_difficult_cases:
      1_case: -2
      2_cases: -5
      3_cases: -10
      4_plus_cases: -20
    time_since_difficult_case:
      under_1_hour: -5
      1_2_hours: -2
      2_4_hours: 0
      over_4_hours: 3
    stress_score_penalty: -10
    break_recency_bonus:
      under_30_min: 5
      30_60_min: 3
      1_2_hours: 1
      over_2_hours: 0

# Dynamic priority adjustments
priority_adjustments:
  critical:
    skill_match_weight: 0.45
    performance_history_weight: 0.25
    availability_weight: 0.20
    wellbeing_factors_weight: 0.05
    customer_factors_weight: 0.05
    
  high:
    skill_match_weight: 0.40
    performance_history_weight: 0.22
    availability_weight: 0.23
    wellbeing_factors_weight: 0.10
    customer_factors_weight: 0.05
    
  low:
    skill_match_weight: 0.25
    availability_weight: 0.35
    performance_history_weight: 0.15
    wellbeing_factors_weight: 0.20
    customer_factors_weight: 0.05
```

## Example 4: Development/Testing Configuration

This configuration is optimized for development and testing environments.

### scoring_weights.yaml - Development
```yaml
scoring_algorithm:
  version: "2.0"
  description: "Development configuration with simplified scoring for testing"
  
  # Simplified weights for easier testing and debugging
  category_weights:
    skill_match: 0.40           # Clear primary factor
    availability: 0.30          # Clear secondary factor
    performance_history: 0.15   # Reduced for testing
    wellbeing_factors: 0.10     # Minimal for testing
    customer_factors: 0.05      # Standard
    
  # Simplified scoring for predictable testing
  skill_match_scoring:
    exact_domain_match: 10      # Round numbers for easy calculation
    partial_domain_match: 5
    proficiency_bonus:
      expert: 10
      advanced: 5
      intermediate: 0
      basic: -5
    experience_years_multiplier: 1.0  # Easy to calculate
    specialization_match: 10
    certification_bonus: 5
    
  availability_scoring:
    status_scores:
      available: 20             # Clear differentiation
      busy_low_load: 10
      busy_medium_load: 0
      busy_high_load: -10
      break: -20
      offline: -50
    workload_penalties:
      per_active_case: -5       # Clear penalties
      over_capacity_penalty: -20
      
  # Minimal performance scoring for testing
  performance_history_scoring:
    customer_satisfaction:
      weight: 1.0
      scale_multiplier: 2       # Simple multiplier
    resolution_time:
      weight: 0
      baseline_minutes: 30
      penalty_per_minute_over: 0
      bonus_per_minute_under: 0
    escalation_rate:
      weight: 0
      penalty_multiplier: 0
    first_contact_resolution:
      weight: 0
      bonus_multiplier: 0
      
  # Minimal wellbeing scoring for testing
  wellbeing_factors_scoring:
    consecutive_difficult_cases:
      1_case: -1
      2_cases: -2
      3_cases: -5
      4_plus_cases: -10
    stress_score_penalty: -5
```

## Example 5: A/B Testing Configuration

Configuration for testing different routing strategies.

### scoring_weights.yaml - A/B Testing
```yaml
scoring_algorithm:
  version: "2.0"
  description: "A/B testing configuration with experiment flags"
  
  # Enable A/B testing
  ab_testing:
    enabled: true
    experiment_name: "skill_vs_availability_2024"
    traffic_split: 0.5          # 50/50 split
    
  # Variant A: Skill-focused
  variant_a:
    name: "skill_focused"
    category_weights:
      skill_match: 0.50
      availability: 0.20
      performance_history: 0.20
      wellbeing_factors: 0.05
      customer_factors: 0.05
      
  # Variant B: Availability-focused  
  variant_b:
    name: "availability_focused"
    category_weights:
      skill_match: 0.25
      availability: 0.40
      performance_history: 0.20
      wellbeing_factors: 0.10
      customer_factors: 0.05
      
  # Metrics to track for comparison
  ab_metrics:
    - "customer_satisfaction_score"
    - "average_resolution_time"
    - "agent_utilization_rate"
    - "escalation_rate"
    - "agent_stress_score"
    - "queue_wait_time"
```

## Configuration for Different Use Cases

### High-Volume Support Center
```yaml
# Optimized for handling large volumes efficiently
category_weights:
  skill_match: 0.30
  availability: 0.40          # Prioritize getting cases assigned quickly
  performance_history: 0.20
  wellbeing_factors: 0.05     # Lower wellbeing consideration for volume
  customer_factors: 0.05

queue_management:
  max_queue_size: 500         # Large queue capacity
  queue_timeout_minutes: 15   # Faster timeout
  auto_escalation_enabled: true
  overflow_routing: true      # Route to less optimal agents when needed
```

### Enterprise Customer Support
```yaml
# Optimized for high-value enterprise customers
category_weights:
  skill_match: 0.45           # Highest skill matching
  performance_history: 0.30   # Strong performance requirement
  availability: 0.15
  wellbeing_factors: 0.05
  customer_factors: 0.05

customer_factors_scoring:
  enterprise_customer_bonus: 15    # High bonus for enterprise customers
  account_value_multiplier: 0.001  # Bonus based on account value
  previous_escalation_penalty: -5  # Avoid agents who escalated this customer
```

### Technical Support Team
```yaml
# Optimized for complex technical issues
skill_match_scoring:
  exact_domain_match: 25      # Very high technical skill matching
  technical_certification_bonus: 15
  api_integration_experience_bonus: 10
  
complexity_handling:
  high_complexity_skill_requirement: "advanced"  # Require advanced skills for complex cases
  technical_escalation_threshold: 2   # Escalate complex technical issues quickly
```

## Dynamic Configuration Examples

### Time-Based Configuration
```yaml
# Different configurations for different times of day
time_based_configs:
  business_hours:
    time_range: "09:00-17:00"
    timezone: "PST"
    category_weights:
      skill_match: 0.35
      availability: 0.25
      performance_history: 0.20
      wellbeing_factors: 0.15
      customer_factors: 0.05
      
  after_hours:
    time_range: "17:00-09:00"
    timezone: "PST"
    category_weights:
      skill_match: 0.25         # Less skill focus when fewer agents available
      availability: 0.45        # High availability focus
      performance_history: 0.15
      wellbeing_factors: 0.10
      customer_factors: 0.05
      
  weekend:
    days: ["saturday", "sunday"]
    category_weights:
      skill_match: 0.20
      availability: 0.50        # Maximum availability focus
      performance_history: 0.15
      wellbeing_factors: 0.10
      customer_factors: 0.05
```

### Load-Based Configuration
```yaml
# Adjust configuration based on system load
load_based_configs:
  low_load:
    queue_length_threshold: 10
    category_weights:
      skill_match: 0.45         # Optimize for quality when load is low
      availability: 0.20
      performance_history: 0.20
      wellbeing_factors: 0.10
      customer_factors: 0.05
      
  high_load:
    queue_length_threshold: 50
    category_weights:
      skill_match: 0.25         # Optimize for speed when load is high
      availability: 0.45
      performance_history: 0.15
      wellbeing_factors: 0.05   # Reduced wellbeing consideration under pressure
      customer_factors: 0.10    # Increase customer priority
      
  critical_load:
    queue_length_threshold: 100
    emergency_routing: true
    category_weights:
      availability: 0.60        # Maximum speed focus
      skill_match: 0.20
      performance_history: 0.15
      wellbeing_factors: 0.00   # Suspend wellbeing consideration in emergency
      customer_factors: 0.05
```

## Configuration Validation

### Validation Rules
```yaml
validation_rules:
  category_weights:
    sum_must_equal: 1.0
    individual_min: 0.0
    individual_max: 1.0
    
  scoring_values:
    min_value: -100
    max_value: 100
    
  thresholds:
    stress_score:
      min: 0.0
      max: 1.0
    utilization_percentage:
      min: 0
      max: 100
```

### Configuration Testing
```python
# Example configuration validation script
def validate_configuration(config):
    """Validate routing configuration for consistency and correctness"""
    
    # Check weight sums
    weights = config['category_weights']
    if abs(sum(weights.values()) - 1.0) > 0.001:
        raise ValueError("Category weights must sum to 1.0")
    
    # Check for negative bonuses in positive scoring categories
    if config['skill_match_scoring']['exact_domain_match'] < 0:
        raise ValueError("Exact domain match should have positive bonus")
    
    # Check threshold consistency
    if config['wellbeing_thresholds']['stress_score_alert_threshold'] > \
       config['wellbeing_thresholds']['mandatory_break_stress_threshold']:
        raise ValueError("Alert threshold should be lower than mandatory break threshold")
```

This comprehensive set of configuration examples demonstrates the flexibility and power of the enhanced Human Routing Agent system, allowing organizations to fine-tune the routing behavior to match their specific needs and priorities.