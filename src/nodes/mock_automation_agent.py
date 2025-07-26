"""
Mock Automation Agent Node
Responsibility: Simulate automated insurance system responses for routine tasks
Designed to handle common insurance inquiries without requiring LLM processing
"""

import random
import time
import uuid
from typing import Any

import yaml
from langsmith import traceable

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState
from ..interfaces.nodes.automation import AutomationAgentInterface


class MockAutomationAgent(AutomationAgentInterface):
    """LangGraph node for simulating automated insurance system responses"""

    def __init__(
        self, config_manager: ConfigManager, context_provider: ContextProvider
    ):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("mock_automation_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)

        # Load automation repertoire and response templates
        self.automation_repertoire = self._load_automation_repertoire()
        self.response_templates = self._load_response_templates()

        self.logger.info(
            "Mock Automation Agent initialized",
            extra={
                "operation": "initialize",
                "tasks_loaded": len(self.automation_repertoire.get("automation_tasks", {})),
                "mock_data_loaded": len(self.automation_repertoire.get("mock_data", {})),
            },
        )

    def _load_automation_repertoire(self) -> dict[str, Any]:
        """Load the automation repertoire configuration"""
        try:
            config_dir = self.config_manager.config_dir
            repertoire_path = config_dir / "agents" / "mock_automation_agent" / "automation_repertoire.yaml"

            if repertoire_path.exists():
                with open(repertoire_path) as f:
                    return yaml.safe_load(f)
            else:
                self.logger.warning(
                    "Automation repertoire file not found, using empty configuration",
                    extra={"file_path": str(repertoire_path)},
                )
                return {}
        except Exception as e:
            self.logger.error(
                "Failed to load automation repertoire",
                extra={"error": str(e), "operation": "load_automation_repertoire"},
            )
            return {}

    def _load_response_templates(self) -> dict[str, Any]:
        """Load response templates from prompts.yaml"""
        try:
            if self.agent_config:
                return self.agent_config.get_all_prompts()
            return {}
        except Exception as e:
            self.logger.error(
                "Failed to load response templates",
                extra={"error": str(e), "operation": "load_response_templates"},
            )
            return {}

    def detect_automation_intent(self, query: str) -> tuple[str, dict[str, Any]] | None:
        """
        Detect if the query matches any automation task patterns
        Returns (task_name, task_config) if match found, None otherwise
        """
        query_lower = query.lower()
        automation_tasks = self.automation_repertoire.get("automation_tasks", {})

        # Check each automation task for keyword matches
        for task_name, task_config in automation_tasks.items():
            keywords = task_config.get("keywords", [])

            # Check if any keywords are present in the query
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    self.logger.debug(
                        "Automation intent detected",
                        extra={
                            "task": task_name,
                            "keyword_matched": keyword,
                            "query": query[:100],  # Log first 100 chars
                        },
                    )
                    return task_name, task_config

        return None

    def check_escalation_triggers(self, query: str) -> bool:
        """Check if the query contains escalation trigger keywords"""
        query_lower = query.lower()
        escalation_triggers = self.automation_repertoire.get("escalation_triggers", {})

        complexity_keywords = escalation_triggers.get("complexity_keywords", [])
        for keyword in complexity_keywords:
            if keyword.lower() in query_lower:
                self.logger.info(
                    "Escalation trigger detected",
                    extra={"trigger_keyword": keyword, "query": query[:100]},
                )
                return True
        return False

    def _simulate_processing_time(self, task_config: dict[str, Any]) -> float:
        """Simulate realistic processing time for the task"""
        base_time = task_config.get("avg_response_time", 0.5)
        # Add some variance (±30%) to make it more realistic
        variance = base_time * 0.3
        processing_time = base_time + random.uniform(-variance, variance)
        return max(0.1, processing_time)  # Minimum 0.1 seconds

    def _simulate_success_rate(self, task_config: dict[str, Any]) -> bool:
        """Determine if the automation task succeeds based on success rate"""
        success_rate = task_config.get("success_rate", 0.95)
        return random.random() < success_rate

    def _extract_policy_info(self, query: str, state: HybridSystemState) -> dict[str, Any] | None:
        """
        Extract policy information from query or state
        In a real system, this would query actual databases
        """
        # Try to extract policy number from query
        words = query.split()
        policy_number = None

        # Look for policy number patterns
        for word in words:
            if word.startswith("POL-") or (word.startswith("pol") and len(word) > 3):
                policy_number = word.upper()
                break

        # If no policy number found, try to get from context
        if not policy_number:
            customer_context = state.get("customer_context", {})
            policy_number = customer_context.get("policy_number")

        if not policy_number:
            # For demo purposes, use a default policy
            policy_number = "POL-2024-001234"

        # Get mock policy data
        mock_policies = self.automation_repertoire.get("mock_data", {}).get("policies", {})
        return mock_policies.get(policy_number)

    def _extract_claim_info(self, query: str, state: HybridSystemState) -> dict[str, Any] | None:
        """Extract claim information from query or state"""
        # Try to extract claim number from query
        words = query.split()
        claim_number = None

        for word in words:
            if word.startswith("CLM-") or (word.startswith("clm") and len(word) > 3):
                claim_number = word.upper()
                break

        if not claim_number:
            # For demo purposes, use a default claim
            claim_number = "CLM-2024-9001"

        # Get mock claim data
        mock_claims = self.automation_repertoire.get("mock_data", {}).get("claims", {})
        return mock_claims.get(claim_number)

    def _format_response(
        self,
        template_path: str,
        data: dict[str, Any],
        reference_id: str,
        processing_time: float
    ) -> str:
        """Format the response using the specified template"""
        try:
            # Navigate to the template in the nested structure
            template_parts = template_path.split(".")
            template_data = self.response_templates

            for part in template_parts:
                template_data = template_data.get(part, {})

            if isinstance(template_data, str):
                # Add standard metadata to data
                data.update({
                    "reference_id": reference_id,
                    "processing_time": f"{processing_time:.1f}"
                })

                # Format the template with the data
                return template_data.format(**data)
            else:
                self.logger.warning(
                    "Template not found or not a string",
                    extra={"template_path": template_path},
                )
                return f"Automated response completed. Reference ID: {reference_id}"

        except Exception as e:
            self.logger.error(
                "Failed to format response template",
                extra={"error": str(e), "template_path": template_path},
            )
            return f"Automated response completed. Reference ID: {reference_id}"

    def _generate_automation_response(
        self,
        task_name: str,
        task_config: dict[str, Any],
        query: str,
        state: HybridSystemState
    ) -> tuple[str, dict[str, Any]]:
        """Generate the automated response for the identified task"""
        reference_id = f"AUTO-{uuid.uuid4().hex[:8].upper()}"
        processing_time = self._simulate_processing_time(task_config)

        # Simulate processing delay
        time.sleep(processing_time)

        # Check if task succeeds
        if not self._simulate_success_rate(task_config):
            # Task failed - return failure response
            error_msg = random.choice([
                "System temporarily unavailable",
                "Unable to verify account information",
                "Request requires additional verification"
            ])

            response = self._format_response(
                "system_templates.failure_response",
                {"error_message": error_msg},
                reference_id,
                processing_time
            )

            metadata = {
                "automation_result": "failed",
                "task_name": task_name,
                "error_reason": error_msg,
                "reference_id": reference_id,
                "processing_time": processing_time,
                "escalation_required": True
            }

            return response, metadata

        # Task succeeded - generate appropriate response
        category = task_config.get("category", "unknown")
        response_template = task_config.get("response_template")

        if category == "policy_information":
            policy_info = self._extract_policy_info(query, state)
            if policy_info:
                response = self._format_response(
                    response_template,
                    policy_info,
                    reference_id,
                    processing_time
                )
            else:
                response = f"Policy information retrieved. Reference ID: {reference_id}"

        elif category == "claims_status":
            claim_info = self._extract_claim_info(query, state)
            if claim_info:
                response = self._format_response(
                    response_template,
                    claim_info,
                    reference_id,
                    processing_time
                )
            else:
                response = f"Claim status updated. Reference ID: {reference_id}"

        else:
            # Generic success response
            response = self._format_response(
                "system_templates.success_response",
                {},
                reference_id,
                processing_time
            )

        metadata = {
            "automation_result": "success",
            "task_name": task_name,
            "task_category": category,
            "reference_id": reference_id,
            "processing_time": processing_time,
            "escalation_required": False
        }

        return response, metadata

    @traceable(run_type="tool", name="Mock Automation Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main automation function - attempt to handle routine queries automatically
        """
        start_time = time.time()
        query = state.get("query", "")

        self.logger.info(
            "Processing automation request",
            extra={"operation": "automation_processing", "query": query[:100]},
        )

        # Check for escalation triggers first
        if self.check_escalation_triggers(query):
            escalation_metadata = {
                "automation_result": "escalated",
                "escalation_reason": "trigger_keyword_detected",
                "escalation_required": True,
                "processing_time": time.time() - start_time
            }

            state["automation_response"] = None
            state["automation_metadata"] = escalation_metadata
            state["requires_escalation"] = True

            self.logger.info(
                "Query escalated due to trigger keywords",
                extra=escalation_metadata,
            )

            return state

        # Detect automation intent
        automation_match = self.detect_automation_intent(query)

        if automation_match:
            task_name, task_config = automation_match

            # Generate automated response
            try:
                response, metadata = self._generate_automation_response(
                    task_name, task_config, query, state
                )

                state["automation_response"] = response
                state["automation_metadata"] = metadata
                state["requires_escalation"] = metadata.get("escalation_required", False)

                # Save interaction to context
                self._save_automation_context(state, response, metadata)

                self.logger.info(
                    "Automation task completed",
                    extra={
                        "task_name": task_name,
                        "result": metadata.get("automation_result"),
                        "processing_time": metadata.get("processing_time"),
                    },
                )

            except Exception as e:
                self.logger.error(
                    "Automation task failed with exception",
                    extra={"error": str(e), "task_name": task_name},
                )

                # Escalate on error
                error_metadata = {
                    "automation_result": "error",
                    "error_message": str(e),
                    "escalation_required": True,
                    "processing_time": time.time() - start_time
                }

                state["automation_response"] = None
                state["automation_metadata"] = error_metadata
                state["requires_escalation"] = True

        else:
            # No automation match found
            no_match_metadata = {
                "automation_result": "no_match",
                "escalation_reason": "no_automation_task_matched",
                "escalation_required": True,
                "processing_time": time.time() - start_time
            }

            state["automation_response"] = None
            state["automation_metadata"] = no_match_metadata
            state["requires_escalation"] = True

            self.logger.debug(
                "No automation match found for query",
                extra={"query": query[:100]},
            )

        return state

    def _save_automation_context(
        self, state: HybridSystemState, response: str, metadata: dict[str, Any]
    ):
        """Save automation interaction to context"""
        try:
            session_id = state.get("session_id", "unknown")

            context_data = {
                "type": "automation_response",
                "query": state.get("query", ""),
                "response": response,
                "metadata": metadata,
                "timestamp": time.time()
            }

            self.context_provider.store_context(session_id, context_data)

        except Exception as e:
            self.logger.error(
                "Failed to save automation context",
                extra={"error": str(e), "operation": "save_automation_context"},
            )

    def get_supported_tasks(self) -> list[str]:
        """Return list of supported automation tasks"""
        return list(self.automation_repertoire.get("automation_tasks", {}).keys())

    def get_task_categories(self) -> list[str]:
        """Return list of task categories"""
        categories = set()
        automation_tasks = self.automation_repertoire.get("automation_tasks", {})

        for task_config in automation_tasks.values():
            category = task_config.get("category")
            if category:
                categories.add(category)

        return list(categories)

    @property
    def agent_name(self) -> str:
        """Get the name of this automation agent"""
        return "MockAutomationAgent"

    @property
    def response_time_range(self) -> tuple[float, float]:
        """Get the expected response time range for this agent"""
        return (0.1, 1.0)  # 0.1 to 1.0 seconds

    @property
    def success_rate(self) -> float:
        """Get the overall success rate for this agent"""
        if self.agent_config:
            return self.agent_config.get_setting("success_rate", 0.95)
        return 0.95
