# Human Routing Agent - Enhanced System Design

## Overview

This document outlines the design for an enhanced Human Routing Agent system that intelligently routes customer escalations to the most suitable human agents based on configurable scoring criteria, real-time availability, performance metrics, and employee wellbeing considerations.

## Current State Analysis

The existing routing agent (`src/nodes/routing_agent.py`) provides:
- Enhanced agent data structure with realistic agent profiles
- Multiple sophisticated scoring algorithms (skill-based, workload-balanced, wellbeing-based)
- Comprehensive employee wellbeing protection measures
- Flexible configuration-based routing strategies
- Integration with the MockAutomationAgent and quality assessment workflow
- Support for the automation-first HITL architecture

### Current Implementation Strengths
- **Comprehensive agent profiles** - detailed skill and performance modeling
- **Advanced scoring algorithms** - multiple strategies with configurable weights
- **Employee wellbeing protection** - sophisticated burnout prevention
- **Flexible configuration** - YAML-based configuration with hot-reloading
- **Queue simulation** - realistic queue management for demonstration
- **Integration ready** - works seamlessly with HITL workflow

### Areas for Enhancement (Future Development)
- **Persistent storage** - database-backed agent data for production scale
- **Real-time metrics** - live performance tracking and updates
- **Advanced queue management** - production-grade queue systems
- **Extended analytics** - comprehensive historical performance analysis

## Enhanced System Architecture

### 1. Database Schema Design

#### Core Tables

##### `human_agents` - Static Agent Information
```sql
CREATE TABLE human_agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    employee_id VARCHAR(50) UNIQUE,
    department VARCHAR(50),
    hire_date DATE,
    skill_level ENUM('junior', 'intermediate', 'senior', 'expert') NOT NULL,
    base_hourly_rate DECIMAL(10,2),
    max_concurrent_cases INTEGER DEFAULT 5,
    frustration_tolerance ENUM('low', 'medium', 'high') DEFAULT 'medium',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

##### `agent_skills` - Skills and Expertise Mapping
```sql
CREATE TABLE agent_skills (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    skill_domain VARCHAR(50) NOT NULL,
    proficiency_level ENUM('basic', 'intermediate', 'advanced', 'expert') NOT NULL,
    years_experience DECIMAL(3,1),
    certification_level VARCHAR(50),
    last_updated DATE,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id),
    UNIQUE KEY unique_agent_skill (agent_id, skill_domain)
);
```

##### `agent_specializations` - Specific Areas of Expertise
```sql
CREATE TABLE agent_specializations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.50,
    case_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0.0000,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);
```

##### `agent_languages` - Language Capabilities
```sql
CREATE TABLE agent_languages (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    proficiency_level ENUM('basic', 'conversational', 'fluent', 'native') NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);
```

#### Performance Tracking Tables

##### `agent_performance_metrics` - Real-time Performance Data
```sql
CREATE TABLE agent_performance_metrics (
    agent_id VARCHAR(50) PRIMARY KEY,
    current_workload INTEGER DEFAULT 0,
    cases_today INTEGER DEFAULT 0,
    cases_this_week INTEGER DEFAULT 0,
    cases_this_month INTEGER DEFAULT 0,
    avg_resolution_time_minutes INTEGER,
    customer_satisfaction_score DECIMAL(3,2),
    escalation_rate DECIMAL(5,4),
    first_contact_resolution_rate DECIMAL(5,4),
    consecutive_difficult_cases INTEGER DEFAULT 0,
    last_difficult_case_timestamp TIMESTAMP NULL,
    last_break_timestamp TIMESTAMP NULL,
    stress_score DECIMAL(3,2) DEFAULT 0.00,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);
```

##### `case_assignments` - Historical Case Assignment Data
```sql
CREATE TABLE case_assignments (
    assignment_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50),
    assigned_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_timestamp TIMESTAMP NULL,
    completed_timestamp TIMESTAMP NULL,
    status ENUM('assigned', 'in_progress', 'completed', 'escalated', 'transferred') DEFAULT 'assigned',
    priority_level ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    complexity_level ENUM('low', 'medium', 'high') NOT NULL,
    required_skills JSON,
    customer_frustration_level ENUM('low', 'moderate', 'high', 'critical') DEFAULT 'low',
    resolution_time_minutes INTEGER NULL,
    customer_satisfaction_rating INTEGER NULL,
    escalated BOOLEAN DEFAULT FALSE,
    routing_strategy VARCHAR(50),
    routing_confidence DECIMAL(3,2),
    match_score DECIMAL(5,2),
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id),
    INDEX idx_agent_completed (agent_id, completed_timestamp),
    INDEX idx_case_status (case_id, status)
);
```

#### Availability and Scheduling Tables

##### `agent_schedules` - Work Schedules
```sql
CREATE TABLE agent_schedules (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    day_of_week ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    effective_from DATE NOT NULL,
    effective_until DATE NULL,
    schedule_type ENUM('regular', 'temporary', 'exception') DEFAULT 'regular',
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);
```

##### `agent_availability` - Real-time Availability Status
```sql
CREATE TABLE agent_availability (
    agent_id VARCHAR(50) PRIMARY KEY,
    current_status ENUM('available', 'busy', 'break', 'meeting', 'training', 'offline') NOT NULL,
    status_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_available_at TIMESTAMP NULL,
    manual_status_override BOOLEAN DEFAULT FALSE,
    override_reason VARCHAR(200) NULL,
    last_status_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);
```

#### Queue Management Tables

##### `escalation_queue` - Active Queue Management
```sql
CREATE TABLE escalation_queue (
    queue_entry_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50),
    priority_level ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    complexity_level ENUM('low', 'medium', 'high') NOT NULL,
    required_skills JSON NOT NULL,
    special_requirements JSON,
    customer_frustration_level ENUM('low', 'moderate', 'high', 'critical') DEFAULT 'low',
    estimated_resolution_time INTEGER,
    queue_position INTEGER NOT NULL,
    queued_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_assignment_time TIMESTAMP,
    max_wait_time INTEGER DEFAULT 30,
    assigned_agent_id VARCHAR(50) NULL,
    assignment_timestamp TIMESTAMP NULL,
    status ENUM('queued', 'assigned', 'completed', 'cancelled') DEFAULT 'queued',
    FOREIGN KEY (assigned_agent_id) REFERENCES human_agents(agent_id),
    INDEX idx_queue_position (queue_position),
    INDEX idx_priority_queued (priority_level, queued_timestamp)
);
```

### 2. Configurable Scoring Algorithm

#### Scoring Configuration Structure
```yaml
# config/agents/routing_agent/scoring_weights.yaml
scoring_algorithm:
  version: "2.0"
  
  # Main scoring categories and their weights (must sum to 1.0)
  category_weights:
    skill_match: 0.35           # How well agent skills match requirements
    availability: 0.25          # Current availability and workload
    performance_history: 0.20   # Historical performance metrics
    wellbeing_factors: 0.15     # Employee wellbeing considerations
    customer_factors: 0.05      # Customer-specific considerations
    
  # Detailed scoring within each category
  skill_match_scoring:
    exact_domain_match: 15      # Points for exact skill domain match
    partial_domain_match: 8     # Points for related skill domain
    proficiency_bonus:
      expert: 10
      advanced: 7
      intermediate: 4
      basic: 1
    experience_years_multiplier: 0.5  # Points per year of experience
    specialization_match: 12    # Bonus for matching specializations
    certification_bonus: 5      # Bonus for relevant certifications
    
  availability_scoring:
    status_scores:
      available: 20
      busy_low_load: 10         # Busy but under 50% capacity
      busy_medium_load: 5       # Busy but under 80% capacity
      busy_high_load: -5        # Busy over 80% capacity
      break: -10
      offline: -50
    workload_penalties:
      per_active_case: -2       # Penalty per active case
      over_capacity_penalty: -15 # Penalty for being over max capacity
    time_since_last_case_bonus: 0.1  # Bonus points per minute since last assignment
    
  performance_history_scoring:
    customer_satisfaction:
      weight: 0.4
      scale_multiplier: 4       # Multiply satisfaction (1-5) by this
    resolution_time:
      weight: 0.3
      baseline_minutes: 25      # Average resolution time
      penalty_per_minute_over: -0.2
      bonus_per_minute_under: 0.1
    escalation_rate:
      weight: 0.2
      penalty_multiplier: -50   # Multiply escalation rate by this
    first_contact_resolution:
      weight: 0.1
      bonus_multiplier: 20      # Multiply FCR rate by this
      
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
    stress_score_penalty: -10   # Multiply stress score (0-1) by this
    break_recency_bonus:
      under_30_min: 5
      30_60_min: 3
      1_2_hours: 1
      over_2_hours: 0
      
  customer_factors_scoring:
    vip_customer_bonus: 5
    repeat_customer_bonus: 2
    language_match_bonus: 8
    timezone_compatibility_bonus: 3

# Priority-based scoring adjustments
priority_adjustments:
  critical:
    skill_match_weight: 0.45    # Increase skill matching importance
    performance_history_weight: 0.25
    availability_weight: 0.20
    wellbeing_factors_weight: 0.05  # Reduce wellbeing consideration
    customer_factors_weight: 0.05
    
  high:
    skill_match_weight: 0.40
    performance_history_weight: 0.22
    availability_weight: 0.23
    wellbeing_factors_weight: 0.10
    customer_factors_weight: 0.05
    
  medium:
    # Use default weights
    
  low:
    skill_match_weight: 0.25    # Decrease skill matching importance
    availability_weight: 0.35   # Increase availability importance
    performance_history_weight: 0.15
    wellbeing_factors_weight: 0.20  # Increase wellbeing consideration
    customer_factors_weight: 0.05
```

### 3. Real-time Availability and Queue Management System

#### Availability Tracking Components

##### Real-time Status Updates
- **WebSocket connections** for real-time agent status updates
- **Heartbeat monitoring** to detect agent disconnections
- **Automatic status transitions** based on case assignments
- **Manual status override** capabilities for agents

##### Workload Calculation Engine
```python
class WorkloadCalculator:
    def calculate_current_workload(self, agent_id: str) -> dict:
        """Calculate real-time workload metrics for an agent"""
        return {
            'active_cases': self._count_active_cases(agent_id),
            'utilization_percentage': self._calculate_utilization(agent_id),
            'estimated_capacity_minutes': self._estimate_remaining_capacity(agent_id),
            'stress_indicators': self._assess_stress_indicators(agent_id),
            'recommended_max_new_cases': self._recommend_case_limit(agent_id)
        }
```

#### Queue Management System

##### Dynamic Queue Positioning
- **Priority-based ordering** with automatic position updates
- **Wait time estimation** based on current agent availability
- **Queue overflow handling** with escalation to supervisors
- **Customer communication** for queue updates

##### Queue Analytics and Optimization
```python
class QueueOptimizer:
    def optimize_queue_assignments(self) -> List[QueueAssignment]:
        """Optimize queue assignments for maximum efficiency"""
        # Implement optimization algorithms:
        # - Hungarian algorithm for optimal matching
        # - Load balancing across agents
        # - Minimize total wait time
        # - Consider urgency and complexity
```

### 4. Performance Metrics Tracking System

#### Real-time Metrics Collection

##### Automated Metric Updates
- **Case completion triggers** update resolution times and satisfaction scores
- **Escalation events** update escalation rates
- **Customer feedback** automatically updates satisfaction scores
- **Stress monitoring** tracks consecutive difficult cases

##### Metric Calculation Engine
```python
class PerformanceMetricsEngine:
    def update_agent_metrics(self, agent_id: str, case_data: dict):
        """Update all relevant metrics for an agent after case completion"""
        # Update resolution time rolling average
        # Update customer satisfaction rolling average  
        # Update escalation rate
        # Update first contact resolution rate
        # Update stress indicators
        # Trigger wellbeing alerts if needed
        
    def calculate_rolling_averages(self, agent_id: str, time_window: str):
        """Calculate performance metrics over different time windows"""
        # Daily, weekly, monthly rolling averages
        # Trend analysis
        # Performance compared to team averages
```

#### Historical Analytics

##### Performance Trend Analysis
- **Time-series analysis** of agent performance metrics
- **Seasonal pattern detection** in workload and performance
- **Comparative analysis** between agents and teams
- **Predictive modeling** for performance forecasting

##### Reporting and Dashboards
- **Real-time performance dashboards** for supervisors
- **Agent self-service analytics** for personal improvement
- **System-wide efficiency reports** for management
- **Wellbeing monitoring alerts** for HR intervention

### 5. Enhanced Employee Wellbeing Protection

#### Stress Monitoring System

##### Stress Score Calculation
```python
def calculate_stress_score(agent_id: str) -> float:
    """Calculate real-time stress score for an agent (0.0 - 1.0)"""
    factors = {
        'consecutive_difficult_cases': 0.25,
        'workload_intensity': 0.20,
        'customer_frustration_exposure': 0.20,
        'work_duration_today': 0.15,
        'recent_break_history': 0.10,
        'complexity_of_recent_cases': 0.10
    }
    # Weighted calculation of stress factors
```

##### Intervention Triggers
- **Automated break suggestions** when stress scores exceed thresholds
- **Case routing adjustments** to protect high-stress agents
- **Supervisor notifications** for wellbeing concerns
- **Mandatory cooldown periods** after multiple difficult cases

#### Workload Balancing

##### Fair Distribution Algorithms
- **Round-robin with skill weighting** for equitable case distribution
- **Complexity balancing** to avoid overwhelming individual agents
- **Skill development routing** to provide growth opportunities
- **Experience level considerations** for appropriate case assignment

### 6. Configuration Management

#### Multi-level Configuration Structure
```
config/agents/routing_agent/
├── scoring_weights.yaml          # Configurable scoring algorithm
├── wellbeing_thresholds.yaml     # Employee protection parameters
├── queue_management.yaml         # Queue behavior configuration
├── performance_targets.yaml      # Performance benchmarks and goals
├── availability_rules.yaml       # Availability calculation rules
└── escalation_policies.yaml      # When and how to escalate issues
```

#### Environment-specific Overrides
- **Development environment** with relaxed thresholds for testing
- **Production environment** with optimized parameters
- **A/B testing capabilities** for experimenting with different algorithms

### 7. Integration Points

#### External System Integrations

##### HR System Integration
- **Employee data synchronization** for skills and availability
- **Performance review integration** for comprehensive evaluation
- **Scheduling system integration** for accurate availability tracking

##### Customer Data Integration  
- **CRM integration** for customer tier and history information
- **Previous interaction history** for personalized routing
- **Customer preference tracking** for language and agent preferences

##### Communication Systems
- **Slack/Teams integration** for agent status updates
- **Email notifications** for queue and assignment updates
- **SMS alerts** for high-priority escalations

### 8. Monitoring and Alerting

#### System Health Monitoring
- **Queue length alerts** when wait times exceed thresholds
- **Agent overload alerts** when utilization exceeds safe limits
- **Performance degradation alerts** when metrics drop below targets
- **System availability monitoring** for database and service health

#### Business Intelligence
- **Routing effectiveness analysis** measuring customer satisfaction impact
- **Cost optimization analysis** measuring efficiency improvements
- **Employee satisfaction correlation** with routing decisions
- **Capacity planning recommendations** based on historical data

## Implementation Roadmap

### Phase 1: Database and Core Infrastructure (2-3 weeks)
1. Implement database schema and migrations
2. Create data access layers and repositories
3. Implement basic CRUD operations for agent management
4. Set up configuration management system

### Phase 2: Enhanced Scoring Algorithm (2 weeks)
1. Implement configurable scoring engine
2. Create scoring weight management interface
3. Add performance metrics calculation
4. Implement A/B testing framework for scoring algorithms

### Phase 3: Real-time Systems (3 weeks)
1. Implement real-time availability tracking
2. Create queue management system
3. Add workload calculation engine
4. Implement WebSocket-based status updates

### Phase 4: Analytics and Wellbeing (2 weeks)
1. Implement performance metrics tracking
2. Create stress monitoring system
3. Add wellbeing protection measures
4. Implement reporting and analytics dashboards

### Phase 5: Integration and Optimization (2 weeks)
1. Integrate with existing system components
2. Add external system integrations
3. Implement monitoring and alerting
4. Performance optimization and testing

### Phase 6: Testing and Deployment (1-2 weeks)
1. Comprehensive testing of all components
2. Load testing and performance validation
3. User acceptance testing
4. Production deployment and monitoring

## Success Metrics

### Customer Experience Metrics
- **Reduced average wait time** for escalations
- **Improved customer satisfaction** scores for escalated cases
- **Higher first-contact resolution rate** for human-handled cases
- **Reduced re-escalation rate**

### Employee Experience Metrics
- **Improved agent satisfaction** with case assignments
- **Reduced agent burnout** indicators
- **Better work-life balance** through fair workload distribution
- **Enhanced skill development** through appropriate case routing

### Operational Efficiency Metrics
- **Optimized agent utilization** without overloading
- **Reduced case resolution times** through better matching
- **Improved routing accuracy** and confidence scores
- **Lower operational costs** through efficiency gains

This enhanced Human Routing Agent system will provide a sophisticated, data-driven approach to escalation routing that balances customer needs with employee wellbeing while optimizing operational efficiency.