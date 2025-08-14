"""
LangSmith integration setup for local LLMs
"""

import os

from dotenv import load_dotenv
from langsmith import Client

from ..core.logging import get_logger

# Load environment variables
load_dotenv()


def setup_langsmith():
    """Setup LangSmith client and configuration for local LLM tracking"""
    logger = get_logger(__name__)
    api_key = os.getenv("LANGSMITH_API_KEY")
    project_name = os.getenv("LANGSMITH_PROJECT", "hybrid-ai-system")

    if not api_key:
        logger.warning(
            "LANGSMITH_API_KEY not found in environment",
            extra={"operation": "setup_langsmith"},
        )
        return None

    try:
        # Initialize LangSmith client
        client = Client(api_key=api_key)

        # Set project name for tracing
        os.environ["LANGCHAIN_PROJECT"] = project_name

        # Enable tracing for local LLMs
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

        logger.info(
            "LangSmith configured successfully",
            extra={"project_name": project_name, "operation": "setup_langsmith"},
        )
        return client

    except Exception as e:
        logger.error(
            "Failed to setup LangSmith",
            extra={
                "error": str(e),
                "project_name": project_name,
                "operation": "setup_langsmith",
            },
        )
        return None


def get_langsmith_client():
    """Get LangSmith client instance"""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        return None

    try:
        return Client(api_key=api_key)
    except Exception as e:
        logger = get_logger(__name__)
        logger.warning(
            "Could not create LangSmith client",
            extra={"error": str(e), "operation": "get_langsmith_client"},
        )
        return None


def is_langsmith_enabled():
    """Check if LangSmith tracking is enabled"""
    return os.getenv("LANGSMITH_API_KEY") is not None
