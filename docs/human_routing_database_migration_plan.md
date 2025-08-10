# Human Routing Agent - Database Migration Plan

## Overview

This document outlines the step-by-step migration plan for implementing the enhanced Human Routing Agent database schema, including data migration from the current hardcoded system to the new persistent database structure.

## Current State

The existing routing agent uses hardcoded agent data in `src/nodes/routing_agent.py`:
- 3 sample agents with basic attributes
- Performance metrics embedded in agent objects
- No persistent storage
- Simple availability simulation

## Migration Strategy

### Phase 1: Database Setup and Schema Creation

#### 1.1 Database Environment Setup
```bash
# Create database directories
mkdir -p data/routing_system/
mkdir -p data/routing_system/backups/
mkdir -p data/routing_system/migrations/

# Set up SQLite database for development
# Production could use PostgreSQL or MySQL
```

#### 1.2 Migration Framework Setup
```python
# Create migration tracking table
CREATE TABLE schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

#### 1.3 Core Schema Migrations

**Migration 001: Core Agent Tables**
```sql
-- File: data/routing_system/migrations/001_create_core_agent_tables.sql
-- Description: Create basic agent and skills tables

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

CREATE TABLE agent_specializations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.50,
    case_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0.0000,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);

CREATE TABLE agent_languages (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    proficiency_level ENUM('basic', 'conversational', 'fluent', 'native') NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES human_agents(agent_id)
);

INSERT INTO schema_migrations (version, description) 
VALUES ('001', 'Create core agent tables');
```

**Migration 002: Performance and Metrics Tables**
```sql
-- File: data/routing_system/migrations/002_create_performance_tables.sql

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

INSERT INTO schema_migrations (version, description) 
VALUES ('002', 'Create performance and case assignment tables');
```

**Migration 003: Availability and Scheduling Tables**
```sql
-- File: data/routing_system/migrations/003_create_availability_tables.sql

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

INSERT INTO schema_migrations (version, description) 
VALUES ('003', 'Create availability and scheduling tables');
```

**Migration 004: Queue Management Tables**
```sql
-- File: data/routing_system/migrations/004_create_queue_tables.sql

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

INSERT INTO schema_migrations (version, description) 
VALUES ('004', 'Create queue management tables');
```

### Phase 2: Data Migration from Hardcoded System

#### 2.1 Agent Data Migration Script
```python
# File: scripts/migrate_agent_data.py

import sqlite3
from datetime import datetime, date
from typing import Dict, Any

class AgentDataMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def migrate_hardcoded_agents(self):
        """Migrate the 3 hardcoded agents to the database"""
        
        # Original hardcoded agent data
        hardcoded_agents = [
            {
                "id": "agent_001",
                "name": "Sarah Johnson",
                "email": "sarah.johnson@company.com",
                "skills": ["technical", "billing", "account_management"],
                "skill_level": "senior",
                "languages": ["english", "spanish"],
                "max_concurrent": 5,
                "frustration_tolerance": "high",
                "specializations": ["complex_technical_issues", "enterprise_accounts"],
                "performance_metrics": {
                    "avg_resolution_time": 18,
                    "customer_satisfaction": 4.7,
                    "escalation_rate": 0.12,
                },
            },
            {
                "id": "agent_002", 
                "name": "Mike Chen",
                "email": "mike.chen@company.com",
                "skills": ["general", "billing", "refunds"],
                "skill_level": "junior",
                "languages": ["english", "mandarin"],
                "max_concurrent": 3,
                "frustration_tolerance": "medium",
                "specializations": ["billing_issues", "refund_processing"],
                "performance_metrics": {
                    "avg_resolution_time": 25,
                    "customer_satisfaction": 4.4,
                    "escalation_rate": 0.18,
                },
            },
            {
                "id": "agent_003",
                "name": "Emily Rodriguez", 
                "email": "emily.rodriguez@company.com",
                "skills": ["technical", "product_support", "integrations"],
                "skill_level": "senior",
                "languages": ["english", "spanish", "portuguese"],
                "max_concurrent": 4,
                "frustration_tolerance": "high",
                "specializations": ["api_integrations", "enterprise_support"],
                "performance_metrics": {
                    "avg_resolution_time": 22,
                    "customer_satisfaction": 4.8,
                    "escalation_rate": 0.08,
                },
            },
        ]
        
        for agent_data in hardcoded_agents:
            self._insert_agent(agent_data)
            self._insert_agent_skills(agent_data)
            self._insert_agent_languages(agent_data) 
            self._insert_agent_specializations(agent_data)
            self._insert_performance_metrics(agent_data)
            self._insert_initial_availability(agent_data)
            self._insert_default_schedule(agent_data)
            
        self.conn.commit()
        print(f"Successfully migrated {len(hardcoded_agents)} agents to database")
        
    def _insert_agent(self, agent_data: Dict[str, Any]):
        """Insert basic agent information"""
        self.conn.execute("""
            INSERT INTO human_agents (
                agent_id, name, email, employee_id, department, hire_date,
                skill_level, max_concurrent_cases, frustration_tolerance, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_data["id"],
            agent_data["name"], 
            agent_data["email"],
            agent_data["id"],  # Use agent_id as employee_id for now
            "Customer Support",  # Default department
            date(2023, 1, 1),   # Default hire date
            agent_data["skill_level"],
            agent_data["max_concurrent"],
            agent_data["frustration_tolerance"],
            True
        ))
        
    def _insert_agent_skills(self, agent_data: Dict[str, Any]):
        """Insert agent skills"""
        for skill in agent_data["skills"]:
            # Map skill level to proficiency
            proficiency_map = {
                "junior": "intermediate",
                "senior": "advanced"
            }
            proficiency = proficiency_map.get(agent_data["skill_level"], "intermediate")
            
            self.conn.execute("""
                INSERT INTO agent_skills (
                    agent_id, skill_domain, proficiency_level, years_experience, last_updated
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                agent_data["id"],
                skill,
                proficiency,
                3.0 if agent_data["skill_level"] == "senior" else 1.5,  # Estimated experience
                date.today()
            ))
            
    def _insert_agent_languages(self, agent_data: Dict[str, Any]):
        """Insert agent language capabilities"""
        for language in agent_data["languages"]:
            # Assume native proficiency for english, conversational for others
            proficiency = "native" if language == "english" else "conversational"
            
            self.conn.execute("""
                INSERT INTO agent_languages (
                    agent_id, language_code, proficiency_level
                ) VALUES (?, ?, ?)
            """, (agent_data["id"], language, proficiency))
            
    def _insert_agent_specializations(self, agent_data: Dict[str, Any]):
        """Insert agent specializations"""
        for specialization in agent_data["specializations"]:
            self.conn.execute("""
                INSERT INTO agent_specializations (
                    agent_id, specialization, confidence_score, case_count, success_rate
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                agent_data["id"],
                specialization,
                0.85,  # High confidence for existing specializations
                50,    # Simulated case count
                0.92   # High success rate
            ))
            
    def _insert_performance_metrics(self, agent_data: Dict[str, Any]):
        """Insert initial performance metrics"""
        metrics = agent_data["performance_metrics"]
        
        self.conn.execute("""
            INSERT INTO agent_performance_metrics (
                agent_id, current_workload, cases_today, cases_this_week, cases_this_month,
                avg_resolution_time_minutes, customer_satisfaction_score, escalation_rate,
                first_contact_resolution_rate, consecutive_difficult_cases, stress_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_data["id"],
            2,  # Current workload from original data
            8,  # Simulated daily cases
            35, # Simulated weekly cases  
            140, # Simulated monthly cases
            metrics["avg_resolution_time"],
            metrics["customer_satisfaction"],
            metrics["escalation_rate"],
            0.85,  # Estimated FCR rate
            0,     # No consecutive difficult cases initially
            0.2    # Low stress score initially
        ))
        
    def _insert_initial_availability(self, agent_data: Dict[str, Any]):
        """Insert initial availability status"""
        # Set initial status based on current workload
        workload = 2  # From original data
        max_concurrent = agent_data["max_concurrent"]
        
        if workload >= max_concurrent:
            status = "busy"
        else:
            status = "available"
            
        self.conn.execute("""
            INSERT INTO agent_availability (
                agent_id, current_status, status_since, manual_status_override
            ) VALUES (?, ?, ?, ?)
        """, (agent_data["id"], status, datetime.now(), False))
        
    def _insert_default_schedule(self, agent_data: Dict[str, Any]):
        """Insert default work schedule"""
        # Create standard business hours schedule
        business_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        
        for day in business_days:
            self.conn.execute("""
                INSERT INTO agent_schedules (
                    agent_id, day_of_week, start_time, end_time, timezone,
                    effective_from, schedule_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_data["id"],
                day,
                "09:00:00",
                "17:00:00", 
                "PST",
                date.today(),
                "regular"
            ))

if __name__ == "__main__":
    migrator = AgentDataMigrator("data/routing_system/routing_agents.db")
    migrator.migrate_hardcoded_agents()
```

#### 2.2 Historical Data Generation Script
```python
# File: scripts/generate_historical_data.py

import sqlite3
import random
from datetime import datetime, timedelta
from uuid import uuid4

class HistoricalDataGenerator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def generate_sample_case_history(self, days_back: int = 30, cases_per_day: int = 20):
        """Generate sample case assignment history for testing"""
        
        # Get agent IDs
        agents = self.conn.execute("SELECT agent_id FROM human_agents").fetchall()
        agent_ids = [agent[0] for agent in agents]
        
        priority_levels = ["low", "medium", "high", "critical"]
        complexity_levels = ["low", "medium", "high"] 
        skills_options = [
            '["technical"]',
            '["billing"]', 
            '["account_management"]',
            '["technical", "billing"]',
            '["general"]'
        ]
        frustration_levels = ["low", "moderate", "high", "critical"]
        
        cases_generated = 0
        
        for day in range(days_back):
            case_date = datetime.now() - timedelta(days=day)
            
            for case_num in range(cases_per_day):
                case_id = f"case_{case_date.strftime('%Y%m%d')}_{case_num:03d}"
                assignment_id = str(uuid4())
                agent_id = random.choice(agent_ids)
                
                # Generate realistic case data
                priority = random.choices(priority_levels, weights=[50, 30, 15, 5])[0]
                complexity = random.choices(complexity_levels, weights=[40, 40, 20])[0]
                frustration = random.choices(frustration_levels, weights=[60, 25, 10, 5])[0]
                
                # Generate timestamps
                assigned_time = case_date.replace(
                    hour=random.randint(9, 16),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                started_time = assigned_time + timedelta(minutes=random.randint(1, 15))
                
                # Resolution time based on complexity
                resolution_minutes = {
                    "low": random.randint(10, 25),
                    "medium": random.randint(20, 45), 
                    "high": random.randint(35, 90)
                }[complexity]
                
                completed_time = started_time + timedelta(minutes=resolution_minutes)
                
                # Customer satisfaction correlated with resolution time and agent skill
                base_satisfaction = random.uniform(3.5, 5.0)
                if resolution_minutes > 60:
                    base_satisfaction -= 0.5
                if frustration in ["high", "critical"]:
                    base_satisfaction -= 0.3
                    
                satisfaction = max(1, min(5, base_satisfaction))
                
                # Escalation probability
                escalated = random.random() < 0.15  # 15% escalation rate
                
                self.conn.execute("""
                    INSERT INTO case_assignments (
                        assignment_id, case_id, agent_id, customer_id,
                        assigned_timestamp, started_timestamp, completed_timestamp,
                        status, priority_level, complexity_level, required_skills,
                        customer_frustration_level, resolution_time_minutes,
                        customer_satisfaction_rating, escalated, routing_strategy,
                        routing_confidence, match_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    assignment_id, case_id, agent_id, f"customer_{random.randint(1000, 9999)}",
                    assigned_time, started_time, completed_time,
                    "completed", priority, complexity, random.choice(skills_options),
                    frustration, resolution_minutes, int(satisfaction),
                    escalated, "skill_based", random.uniform(0.7, 0.95),
                    random.uniform(70, 95)
                ))
                
                cases_generated += 1
                
        self.conn.commit()
        print(f"Generated {cases_generated} historical case assignments")

if __name__ == "__main__":
    generator = HistoricalDataGenerator("data/routing_system/routing_agents.db")
    generator.generate_sample_case_history(days_back=30, cases_per_day=25)
```

### Phase 3: Migration Execution Plan

#### 3.1 Pre-Migration Checklist
- [ ] Backup existing system configuration
- [ ] Create test environment database
- [ ] Validate migration scripts on test data
- [ ] Create rollback procedures
- [ ] Prepare monitoring for migration process

#### 3.2 Migration Execution Steps

1. **Database Setup** (30 minutes)
   ```bash
   # Create database directory structure
   mkdir -p data/routing_system/{migrations,backups}
   
   # Run schema migrations
   python scripts/run_migrations.py
   ```

2. **Data Migration** (15 minutes)
   ```bash
   # Migrate hardcoded agent data
   python scripts/migrate_agent_data.py
   
   # Generate historical data for testing
   python scripts/generate_historical_data.py
   ```

3. **Validation** (15 minutes)
   ```bash
   # Run validation scripts
   python scripts/validate_migration.py
   
   # Check data integrity
   python scripts/check_data_integrity.py
   ```

4. **System Integration** (30 minutes)
   ```bash
   # Update routing agent to use database
   # Test basic functionality
   # Verify configuration loading
   ```

#### 3.3 Post-Migration Verification

**Data Integrity Checks:**
- Verify all agents migrated correctly
- Check foreign key relationships
- Validate performance metrics calculations
- Test availability status tracking

**Functional Testing:**
- Test agent selection algorithms
- Verify queue management
- Check real-time updates
- Validate configuration loading

#### 3.4 Rollback Plan

If migration fails:
1. Stop the routing service
2. Restore previous system from backup
3. Investigate migration issues
4. Fix migration scripts
5. Retry migration on test environment

### Phase 4: Ongoing Maintenance

#### 4.1 Database Maintenance Scripts
```python
# File: scripts/database_maintenance.py

class DatabaseMaintenance:
    def daily_maintenance(self):
        """Daily maintenance tasks"""
        # Update performance metrics
        # Clean old queue entries
        # Archive completed cases older than 90 days
        # Update agent stress scores
        
    def weekly_maintenance(self):
        """Weekly maintenance tasks"""  
        # Rebuild indexes
        # Update rolling averages
        # Generate performance reports
        # Check for data inconsistencies
        
    def monthly_maintenance(self):
        """Monthly maintenance tasks"""
        # Archive old performance data
        # Update agent skill assessments
        # Review and optimize queries
        # Database size monitoring
```

#### 4.2 Monitoring and Alerts

**Database Health Monitoring:**
- Query performance monitoring
- Database size tracking
- Index effectiveness analysis
- Connection pool monitoring

**Data Quality Monitoring:**
- Orphaned record detection
- Data consistency validation
- Performance metric accuracy
- Queue state validation

## Success Criteria

### Migration Success Metrics
- [ ] All existing agents migrated without data loss
- [ ] Database queries performing within acceptable limits (<100ms for basic queries)
- [ ] Real-time updates working correctly
- [ ] Configuration system loading from new structure
- [ ] Queue management functioning properly

### Performance Benchmarks
- **Agent lookup queries**: <50ms
- **Queue position updates**: <100ms  
- **Performance metric calculations**: <200ms
- **Availability status updates**: <25ms
- **Complex scoring calculations**: <300ms

### Data Quality Validation
- [ ] No orphaned records in foreign key relationships
- [ ] Performance metrics within expected ranges
- [ ] Queue positions correctly maintained
- [ ] Availability status accurately reflects actual state
- [ ] Historical data patterns appear realistic

This migration plan provides a comprehensive approach to transitioning from the hardcoded system to a robust, scalable database-backed routing system while maintaining system functionality throughout the process.