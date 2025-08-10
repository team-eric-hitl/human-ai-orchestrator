"""
Agent Field Mapper
Handles field mapping and transformations between database schema and agent interfaces
"""

import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ..core.logging import get_logger


class AgentFieldMapper:
    """Maps database fields to agent interface fields with configurable transformations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize field mapper with configuration"""
        self.logger = get_logger(__name__)
        
        if config_path is None:
            # Default to human routing agent field mapping
            config_path = Path(__file__).parent.parent.parent / "config" / "agents" / "human_routing_agent" / "field_mapping.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load field mapping configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.debug(f"Loaded field mapping config from {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load field mapping config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default field mapping configuration"""
        return {
            "database_to_agent_mapping": {
                "id": "id",
                "name": "name", 
                "email": "email",
                "status": "status",
                "shift_start": "shift_start",
                "shift_end": "shift_end"
            },
            "transformations": {
                "experience_level_to_skill_level": {
                    1: "junior", 2: "junior", 3: "intermediate", 4: "senior", 5: "senior"
                },
                "json_fields": ["specializations", "languages", "metadata"]
            },
            "computed_fields": {},
            "legacy_fields": {}
        }
    
    def map_database_to_agent(self, db_record: Dict[str, Any], 
                             include_computed: bool = True) -> Dict[str, Any]:
        """Map database record to agent interface format"""
        try:
            mapped_record = {}
            db_to_agent = self.config.get("database_to_agent_mapping", {})
            
            # Direct field mappings
            for db_field, agent_field in db_to_agent.items():
                if db_field in db_record and db_record[db_field] is not None:
                    value = db_record[db_field]
                    
                    # Apply transformations
                    transformed_value = self._transform_value(db_field, value, "db_to_agent")
                    mapped_record[agent_field] = transformed_value
            
            # Add computed fields if requested
            if include_computed:
                computed_fields = self._compute_fields(db_record)
                mapped_record.update(computed_fields)
            
            # Add legacy fields with defaults
            legacy_fields = self._add_legacy_fields(db_record)
            mapped_record.update(legacy_fields)
            
            # Validate mapped record
            if not self._validate_mapped_record(mapped_record):
                self.logger.warning("Mapped record failed validation", extra={"record_id": db_record.get("id")})
            
            return mapped_record
            
        except Exception as e:
            self.logger.error(f"Failed to map database record to agent format: {e}", 
                            extra={"record_id": db_record.get("id")})
            return self._get_fallback_agent_record(db_record)
    
    def map_agent_to_database(self, agent_record: Dict[str, Any]) -> Dict[str, Any]:
        """Map agent interface record to database format"""
        try:
            mapped_record = {}
            agent_to_db = self.config.get("agent_to_database_mapping", {})
            
            # Direct field mappings
            for agent_field, db_field in agent_to_db.items():
                if agent_field in agent_record and agent_record[agent_field] is not None:
                    value = agent_record[agent_field]
                    
                    # Apply reverse transformations
                    transformed_value = self._transform_value(agent_field, value, "agent_to_db")
                    mapped_record[db_field] = transformed_value
            
            # Add timestamps if not present
            now = datetime.now().isoformat()
            if "created_at" not in mapped_record:
                mapped_record["created_at"] = now
            mapped_record["updated_at"] = now
            
            return mapped_record
            
        except Exception as e:
            self.logger.error(f"Failed to map agent record to database format: {e}")
            return {}
    
    def _transform_value(self, field_name: str, value: Any, direction: str) -> Any:
        """Transform value based on field mappings and direction"""
        transformations = self.config.get("transformations", {})
        
        # Handle JSON fields
        json_fields = transformations.get("json_fields", [])
        if field_name in json_fields:
            if direction == "db_to_agent" and isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            elif direction == "agent_to_db" and not isinstance(value, str):
                try:
                    return json.dumps(value)
                except (TypeError, ValueError):
                    return str(value)
        
        # Handle experience level to skill level conversion
        if field_name == "experience_level" and direction == "db_to_agent":
            mapping = transformations.get("experience_level_to_skill_level", {})
            return mapping.get(value, "junior")
        elif field_name == "skill_level" and direction == "agent_to_db":
            mapping = transformations.get("skill_level_to_experience_level", {})
            return mapping.get(value, 2)
        
        return value
    
    def _compute_fields(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Compute derived fields from database record"""
        computed_fields = {}
        field_definitions = self.config.get("computed_fields", {})
        
        for field_name, definition in field_definitions.items():
            try:
                if field_name == "current_workload":
                    # This would normally query the agent_workload table
                    # For now, use a default value
                    computed_fields[field_name] = definition.get("default_value", 0)
                
                elif field_name == "frustration_tolerance":
                    # Derive from experience level
                    experience_level = db_record.get("experience_level", 1)
                    tolerance_mapping = self.config.get("transformations", {}).get("frustration_tolerance_mapping", {})
                    computed_fields[field_name] = tolerance_mapping.get(experience_level, "medium")
                
                elif field_name == "performance_metrics":
                    # This would normally aggregate from agent_metrics table
                    # For now, use default values
                    default_metrics = {
                        "avg_resolution_time": 20,
                        "customer_satisfaction": 4.5,
                        "escalation_rate": 0.15
                    }
                    computed_fields[field_name] = default_metrics
                
                elif field_name == "schedule":
                    # Build schedule from shift times
                    schedule = self._build_schedule_from_shifts(db_record)
                    computed_fields[field_name] = schedule
                    
            except Exception as e:
                self.logger.warning(f"Failed to compute field {field_name}: {e}")
                continue
        
        return computed_fields
    
    def _build_schedule_from_shifts(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Build schedule dictionary from shift start/end times"""
        shift_start = db_record.get("shift_start", "09:00")
        shift_end = db_record.get("shift_end", "17:00")
        
        return {
            "timezone": "UTC",
            "working_hours": {
                "start": shift_start,
                "end": shift_end
            },
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
    
    def _add_legacy_fields(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Add legacy fields with default values"""
        legacy_fields = {}
        field_definitions = self.config.get("legacy_fields", {})
        
        for field_name, definition in field_definitions.items():
            try:
                if field_name == "consecutive_difficult_cases":
                    # This would normally be computed from conversation history
                    legacy_fields[field_name] = definition.get("default_value", 0)
                
                elif field_name == "last_frustration_assignment":
                    # This would normally be computed from assignment history
                    legacy_fields[field_name] = definition.get("default_value", None)
                    
            except Exception as e:
                self.logger.warning(f"Failed to add legacy field {field_name}: {e}")
                continue
        
        return legacy_fields
    
    def _validate_mapped_record(self, record: Dict[str, Any]) -> bool:
        """Validate mapped record against configuration rules"""
        validation_config = self.config.get("validation", {})
        
        # Check required fields
        required_fields = validation_config.get("required_fields", [])
        for field in required_fields:
            if field not in record:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Check field types (basic validation)
        field_types = validation_config.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in record:
                value = record[field]
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):  
                    return False
                elif expected_type == "list" and not isinstance(value, list):
                    return False
                elif expected_type == "dict" and not isinstance(value, dict):
                    return False
        
        return True
    
    def _get_fallback_agent_record(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback agent record when mapping fails"""
        return {
            "id": db_record.get("id", "unknown"),
            "name": db_record.get("name", "Unknown Agent"),
            "email": db_record.get("email", "unknown@company.com"),
            "status": "offline",
            "skills": ["general"],
            "skill_level": "junior",
            "languages": ["english"],
            "current_workload": 0,
            "max_concurrent": 3,
            "frustration_tolerance": "medium",
            "specializations": [],
            "shift_start": "09:00",
            "shift_end": "17:00",
            "performance_metrics": {
                "avg_resolution_time": 30,
                "customer_satisfaction": 4.0,
                "escalation_rate": 0.20
            },
            "schedule": {
                "timezone": "UTC",
                "working_hours": {"start": "09:00", "end": "17:00"},
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            "consecutive_difficult_cases": 0,
            "last_frustration_assignment": None
        }
    
    def get_mapped_fields_info(self) -> Dict[str, Any]:
        """Get information about field mappings"""
        return {
            "database_to_agent_fields": list(self.config.get("database_to_agent_mapping", {}).keys()),
            "agent_to_database_fields": list(self.config.get("agent_to_database_mapping", {}).keys()),
            "computed_fields": list(self.config.get("computed_fields", {}).keys()),
            "legacy_fields": list(self.config.get("legacy_fields", {}).keys()),
            "json_fields": self.config.get("transformations", {}).get("json_fields", []),
            "validation_rules": self.config.get("validation", {})
        }