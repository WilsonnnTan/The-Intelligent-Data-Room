"""
Conversation Memory Module
Maintains conversation history for context retention (last 3-5 messages).
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    execution_plan: Optional[str] = None
    chart_data: Optional[dict] = None


class ConversationMemory:
    """
    Manages conversation history for context retention.
    Keeps track of the last 5 messages to provide context for follow-up questions.
    """
    
    def __init__(self, max_messages: int = 5):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to retain (default: 5)
        """
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.data_schema: Optional[str] = None
        self.current_dataframe_info: Optional[str] = None
    
    def add_message(
        self, 
        role: str, 
        content: str, 
        execution_plan: Optional[str] = None,
        chart_data: Optional[dict] = None
    ) -> None:
        """
        Add a new message to the conversation history.
        
        Args:
            role: Either "user" or "assistant"
            content: The message content
            execution_plan: Optional execution plan from the planner agent
            chart_data: Optional chart configuration data
        """
        message = Message(
            role=role,
            content=content,
            execution_plan=execution_plan,
            chart_data=chart_data
        )
        self.messages.append(message)
        
        # Keep only the last N messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    

    def get_context(self) -> str:
        """
        Get formatted conversation context for agents.
        
        Returns:
            Formatted string of conversation history
        """
        if not self.messages:
            return "No previous conversation."
        
        context_parts = []
        for msg in self.messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role_label}: {msg.content}")
        
        return "\n".join(context_parts)
    

    def get_last_user_query(self) -> Optional[str]:
        """Get the most recent user query."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None
    

    def get_last_assistant_response(self) -> Optional[Message]:
        """Get the most recent assistant response."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None
    

    def set_data_schema(self, schema: str) -> None:
        """Store the current data schema."""
        self.data_schema = schema
    

    def set_dataframe_info(self, info: str) -> None:
        """Store information about the current dataframe."""
        self.current_dataframe_info = info
    

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages = []
        self.data_schema = None
        self.current_dataframe_info = None
    
    
    def get_full_context(self) -> str:
        """
        Get full context including data schema and conversation history.
        Used by the Planner agent for comprehensive understanding.
        """
        parts = []
        
        if self.data_schema:
            parts.append(f"DATA SCHEMA:\n{self.data_schema}")
        
        if self.current_dataframe_info:
            parts.append(f"DATAFRAME INFO:\n{self.current_dataframe_info}")
        
        conversation = self.get_context()
        if conversation != "No previous conversation.":
            parts.append(f"CONVERSATION HISTORY:\n{conversation}")
        
        return "\n\n".join(parts) if parts else "No context available."