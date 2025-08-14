"""SQLite implementation of human agent repository."""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from ..core.human_agents_db import HumanAgentsDatabase
from ..core.logging import get_logger
from ..interfaces.human_agents import HumanAgent, HumanAgentRepository, HumanAgentStatus, Specialization, WorkloadMetrics


class SQLiteHumanAgentRepository(HumanAgentRepository):
    """SQLite implementation of human agent repository."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize repository with database."""
        self.db_manager = HumanAgentsDatabase(db_path)
        self.logger = get_logger(__name__)
        
        # Initialize database schema
        self.db_manager.initialize_database()

    async def create(self, agent: HumanAgent) -> HumanAgent:
        """Create a new human agent."""
        try:
            with self.db_manager.get_connection() as conn:
                # Insert agent record
                conn.execute("""
                    INSERT INTO human_agents (
                        id, name, email, status, specializations, max_concurrent_conversations,
                        experience_level, languages, shift_start, shift_end, metadata,
                        created_at, updated_at, last_activity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent.id, agent.name, agent.email, agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                    json.dumps([s.value if hasattr(s, 'value') else str(s) for s in agent.specializations]),
                    agent.max_concurrent_conversations, agent.experience_level,
                    json.dumps(agent.languages), agent.shift_start, agent.shift_end,
                    json.dumps(agent.metadata), agent.created_at.isoformat(),
                    agent.updated_at.isoformat(),
                    agent.last_activity.isoformat() if agent.last_activity else None
                ))

                # Insert workload metrics
                conn.execute("""
                    INSERT INTO agent_workload (
                        agent_id, active_conversations, queue_length, avg_response_time_minutes,
                        satisfaction_score, stress_level, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent.id, agent.workload.active_conversations, agent.workload.queue_length,
                    agent.workload.avg_response_time_minutes, agent.workload.satisfaction_score,
                    agent.workload.stress_level, datetime.utcnow().isoformat()
                ))

                conn.commit()

            self.logger.info(f"Created human agent: {agent.id}")
            return agent

        except Exception as e:
            self.logger.error(f"Failed to create agent {agent.id}: {e}")
            raise

    async def get_by_id(self, agent_id: str) -> Optional[HumanAgent]:
        """Get human agent by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT a.*, w.active_conversations, w.queue_length, w.avg_response_time_minutes,
                           w.satisfaction_score, w.stress_level
                    FROM human_agents a
                    LEFT JOIN agent_workload w ON a.id = w.agent_id
                    WHERE a.id = ?
                """, (agent_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_agent(row)

        except Exception as e:
            self.logger.error(f"Failed to get agent {agent_id}: {e}")
            raise

    async def get_by_email(self, email: str) -> Optional[HumanAgent]:
        """Get human agent by email."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT a.*, w.active_conversations, w.queue_length, w.avg_response_time_minutes,
                           w.satisfaction_score, w.stress_level
                    FROM human_agents a
                    LEFT JOIN agent_workload w ON a.id = w.agent_id
                    WHERE a.email = ?
                """, (email,))
                
                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_agent(row)

        except Exception as e:
            self.logger.error(f"Failed to get agent by email {email}: {e}")
            raise

    async def get_all(self) -> List[HumanAgent]:
        """Get all human agents."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT a.*, w.active_conversations, w.queue_length, w.avg_response_time_minutes,
                           w.satisfaction_score, w.stress_level
                    FROM human_agents a
                    LEFT JOIN agent_workload w ON a.id = w.agent_id
                    ORDER BY a.name
                """)
                
                return [self._row_to_agent(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get all agents: {e}")
            raise

    async def get_available_agents(self) -> List[HumanAgent]:
        """Get all available human agents."""
        return await self.get_by_status(HumanAgentStatus.AVAILABLE)

    async def get_by_specialization(self, specialization: Specialization) -> List[HumanAgent]:
        """Get agents by specialization."""
        try:
            with self.db_manager.get_connection() as conn:
                spec_value = specialization.value if hasattr(specialization, 'value') else str(specialization)
                pattern = f'%"{spec_value}"%'
                
                cursor = conn.execute("""
                    SELECT a.*, w.active_conversations, w.queue_length, w.avg_response_time_minutes,
                           w.satisfaction_score, w.stress_level
                    FROM human_agents a
                    LEFT JOIN agent_workload w ON a.id = w.agent_id
                    WHERE a.specializations LIKE ?
                    ORDER BY a.name
                """, (pattern,))
                
                return [self._row_to_agent(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get agents by specialization {specialization}: {e}")
            raise

    async def get_by_status(self, status: HumanAgentStatus) -> List[HumanAgent]:
        """Get agents by status."""
        try:
            with self.db_manager.get_connection() as conn:
                status_value = status.value if hasattr(status, 'value') else str(status)
                cursor = conn.execute("""
                    SELECT a.*, w.active_conversations, w.queue_length, w.avg_response_time_minutes,
                           w.satisfaction_score, w.stress_level
                    FROM human_agents a
                    LEFT JOIN agent_workload w ON a.id = w.agent_id
                    WHERE a.status = ?
                    ORDER BY a.name
                """, (status_value,))
                
                return [self._row_to_agent(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get agents by status {status}: {e}")
            raise

    async def update(self, agent: HumanAgent) -> HumanAgent:
        """Update human agent."""
        try:
            agent.updated_at = datetime.utcnow()
            
            with self.db_manager.get_connection() as conn:
                # Update agent record
                conn.execute("""
                    UPDATE human_agents SET
                        name = ?, email = ?, status = ?, specializations = ?,
                        max_concurrent_conversations = ?, experience_level = ?, languages = ?,
                        shift_start = ?, shift_end = ?, metadata = ?, updated_at = ?,
                        last_activity = ?
                    WHERE id = ?
                """, (
                    agent.name, agent.email, agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                    json.dumps([s.value if hasattr(s, 'value') else str(s) for s in agent.specializations]),
                    agent.max_concurrent_conversations, agent.experience_level,
                    json.dumps(agent.languages), agent.shift_start, agent.shift_end,
                    json.dumps(agent.metadata), agent.updated_at.isoformat(),
                    agent.last_activity.isoformat() if agent.last_activity else None,
                    agent.id
                ))

                # Update workload metrics
                conn.execute("""
                    UPDATE agent_workload SET
                        active_conversations = ?, queue_length = ?, avg_response_time_minutes = ?,
                        satisfaction_score = ?, stress_level = ?, updated_at = ?
                    WHERE agent_id = ?
                """, (
                    agent.workload.active_conversations, agent.workload.queue_length,
                    agent.workload.avg_response_time_minutes, agent.workload.satisfaction_score,
                    agent.workload.stress_level, datetime.utcnow().isoformat(), agent.id
                ))

                conn.commit()

            self.logger.info(f"Updated human agent: {agent.id}")
            return agent

        except Exception as e:
            self.logger.error(f"Failed to update agent {agent.id}: {e}")
            raise

    async def update_status(self, agent_id: str, status: HumanAgentStatus) -> bool:
        """Update agent status."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE human_agents SET status = ?, updated_at = ?, last_activity = ?
                    WHERE id = ?
                """, (status.value if hasattr(status, 'value') else str(status), datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), agent_id))
                
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update status for agent {agent_id}: {e}")
            raise

    async def update_workload(self, agent_id: str, workload_data: dict) -> bool:
        """Update agent workload metrics."""
        try:
            with self.db_manager.get_connection() as conn:
                # Build dynamic update query based on provided data
                set_clauses = []
                params = []
                
                for field in ['active_conversations', 'queue_length', 'avg_response_time_minutes', 
                             'satisfaction_score', 'stress_level']:
                    if field in workload_data:
                        set_clauses.append(f"{field} = ?")
                        params.append(workload_data[field])
                
                if not set_clauses:
                    return False
                
                set_clauses.append("updated_at = ?")
                params.append(datetime.utcnow().isoformat())
                params.append(agent_id)
                
                query = f"UPDATE agent_workload SET {', '.join(set_clauses)} WHERE agent_id = ?"
                cursor = conn.execute(query, params)
                conn.commit()
                
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update workload for agent {agent_id}: {e}")
            raise

    async def delete(self, agent_id: str) -> bool:
        """Delete human agent."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("DELETE FROM human_agents WHERE id = ?", (agent_id,))
                conn.commit()
                
                self.logger.info(f"Deleted human agent: {agent_id}")
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise

    async def get_best_available_agent(
        self, 
        specialization: Optional[Specialization] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> Optional[HumanAgent]:
        """Get the best available agent based on workload and specialization."""
        try:
            with self.db_manager.get_connection() as conn:
                # Build query with optional filters
                where_clauses = ["a.status = 'available'"]
                params = []
                
                if specialization:
                    where_clauses.append("a.specializations LIKE ?")
                    spec_value = specialization.value if hasattr(specialization, 'value') else str(specialization)
                    params.append(f'%"{spec_value}"%')
                
                if exclude_agents:
                    placeholders = ','.join(['?' for _ in exclude_agents])
                    where_clauses.append(f"a.id NOT IN ({placeholders})")
                    params.extend(exclude_agents)
                
                # Add workload constraint (not at max capacity)
                where_clauses.append("w.active_conversations < a.max_concurrent_conversations")
                
                query = f"""
                    SELECT a.*, w.active_conversations, w.queue_length, w.avg_response_time_minutes,
                           w.satisfaction_score, w.stress_level
                    FROM human_agents a
                    LEFT JOIN agent_workload w ON a.id = w.agent_id
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY 
                        w.stress_level ASC,
                        w.active_conversations ASC,
                        a.experience_level DESC,
                        w.satisfaction_score DESC
                    LIMIT 1
                """
                
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                
                return self._row_to_agent(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get best available agent: {e}")
            raise

    def _row_to_agent(self, row: sqlite3.Row) -> HumanAgent:
        """Convert database row to HumanAgent object."""
        workload = WorkloadMetrics(
            active_conversations=row['active_conversations'] or 0,
            queue_length=row['queue_length'] or 0,
            avg_response_time_minutes=row['avg_response_time_minutes'] or 0.0,
            satisfaction_score=row['satisfaction_score'] or 5.0,
            stress_level=row['stress_level'] or 1.0
        )
        
        return HumanAgent(
            id=row['id'],
            name=row['name'],
            email=row['email'],
            status=HumanAgentStatus(row['status']),
            specializations=[Specialization(s) for s in json.loads(row['specializations'] or '[]')],
            max_concurrent_conversations=row['max_concurrent_conversations'],
            experience_level=row['experience_level'],
            languages=json.loads(row['languages'] or '["en"]'),
            workload=workload,
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            shift_start=row['shift_start'],
            shift_end=row['shift_end'],
            metadata=json.loads(row['metadata'] or '{}'),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )