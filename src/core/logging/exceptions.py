"""
Custom exception classes for the hybrid AI system

Provides structured exception hierarchy with proper categorization
and context information for better error handling and debugging.
"""

from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HybridSystemError(Exception):
    """
    Base exception class for all hybrid system errors

    Provides structured error information with context and severity.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recoverable: bool = True,
        user_message: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self._generate_error_code()
        self.context = context or {}
        self.severity = severity
        self.recoverable = recoverable
        self.user_message = user_message or self._generate_user_message()

    def _generate_error_code(self) -> str:
        """Generate error code based on exception class"""
        return f"{self.__class__.__name__.upper()}_001"

    def _generate_user_message(self) -> str:
        """Generate user-friendly error message"""
        return "An error occurred while processing your request. Please try again."

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "context": self.context,
        }


class ModelError(HybridSystemError):
    """Errors related to model loading, inference, or configuration"""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        model_type: str | None = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if model_name:
            context["model_name"] = model_name
        if model_type:
            context["model_type"] = model_type
        kwargs["context"] = context

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "MODEL_ERROR_001"

    def _generate_user_message(self) -> str:
        return "I'm having trouble with the AI model. Please try again in a moment."


class ModelLoadError(ModelError):
    """Specific error for model loading failures"""

    def _generate_error_code(self) -> str:
        return "MODEL_LOAD_ERROR_001"

    def _generate_user_message(self) -> str:
        return "The AI model is currently unavailable. Please try again later."


class ModelInferenceError(ModelError):
    """Specific error for model inference failures"""

    def _generate_error_code(self) -> str:
        return "MODEL_INFERENCE_ERROR_001"

    def _generate_user_message(self) -> str:
        return "I encountered an error while processing your request. Please try rephrasing your question."


class ConfigurationError(HybridSystemError):
    """Errors related to configuration loading or validation"""

    def __init__(self, message: str, config_file: str | None = None, **kwargs):
        context = kwargs.get("context", {})
        if config_file:
            context["config_file"] = config_file
        kwargs["context"] = context
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        kwargs.setdefault("recoverable", False)

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "CONFIG_ERROR_001"

    def _generate_user_message(self) -> str:
        return "There's a configuration issue. Please contact support."


class ValidationError(HybridSystemError):
    """Errors related to input or data validation"""

    def __init__(
        self, message: str, field: str | None = None, value: Any = None, **kwargs
    ):
        context = kwargs.get("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["invalid_value"] = str(value)
        kwargs["context"] = context
        kwargs.setdefault("severity", ErrorSeverity.LOW)

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "VALIDATION_ERROR_001"

    def _generate_user_message(self) -> str:
        return "Please check your input and try again."


class EvaluationError(HybridSystemError):
    """Errors related to response evaluation"""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        response: str | None = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if query:
            context["query"] = query[:100] + "..." if len(query) > 100 else query
        if response:
            context["response"] = (
                response[:100] + "..." if len(response) > 100 else response
            )
        kwargs["context"] = context

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "EVALUATION_ERROR_001"

    def _generate_user_message(self) -> str:
        return "I'm having trouble evaluating the response quality. The system will proceed with caution."


class EscalationError(HybridSystemError):
    """Errors related to escalation to human agents"""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        escalation_reason: str | None = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if user_id:
            context["user_id"] = user_id
        if escalation_reason:
            context["escalation_reason"] = escalation_reason
        kwargs["context"] = context
        kwargs.setdefault("severity", ErrorSeverity.HIGH)

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "ESCALATION_ERROR_001"

    def _generate_user_message(self) -> str:
        return "I'm having trouble connecting you with a human agent. Please try again."


class ContextError(HybridSystemError):
    """Errors related to context management"""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        session_id: str | None = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if user_id:
            context["user_id"] = user_id
        if session_id:
            context["session_id"] = session_id
        kwargs["context"] = context

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "CONTEXT_ERROR_001"

    def _generate_user_message(self) -> str:
        return "I'm having trouble accessing your conversation history. Your current request will still be processed."


class LangSmithError(HybridSystemError):
    """Errors related to LangSmith integration"""

    def __init__(self, message: str, operation: str | None = None, **kwargs):
        context = kwargs.get("context", {})
        if operation:
            context["langsmith_operation"] = operation
        kwargs["context"] = context
        kwargs.setdefault("severity", ErrorSeverity.LOW)
        kwargs.setdefault("recoverable", True)

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "LANGSMITH_ERROR_001"

    def _generate_user_message(self) -> str:
        return None  # LangSmith errors shouldn't be shown to users


class WorkflowError(HybridSystemError):
    """Errors related to workflow execution"""

    def __init__(
        self,
        message: str,
        workflow_step: str | None = None,
        workflow_state: dict[str, Any] | None = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if workflow_step:
            context["workflow_step"] = workflow_step
        if workflow_state:
            # Only include non-sensitive state information
            safe_state = {
                k: v
                for k, v in workflow_state.items()
                if k not in ["messages", "api_keys", "secrets"]
            }
            context["workflow_state"] = safe_state
        kwargs["context"] = context

        super().__init__(message, **kwargs)

    def _generate_error_code(self) -> str:
        return "WORKFLOW_ERROR_001"

    def _generate_user_message(self) -> str:
        return "I encountered an issue while processing your request. Please try again."
