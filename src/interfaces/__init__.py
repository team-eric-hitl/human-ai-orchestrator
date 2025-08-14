"""
Interfaces package - Clean contracts for AI and human consumption

This package contains abstract base classes and protocols that define
the contracts for the hybrid system components. These interfaces are
separated from implementations to:

1. Enable AI tools to quickly understand system architecture
2. Reduce context window usage for AI analysis
3. Provide clear contracts for human developers
4. Enable easier testing and mocking

The directory structure mirrors the implementation structure:
- interfaces/core/ - Core system interfaces
- interfaces/nodes/ - Node processing interfaces
- interfaces/workflows/ - Workflow orchestration interfaces
"""
