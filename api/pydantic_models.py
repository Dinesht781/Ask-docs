"""
Pydantic Data Models

This module defines the data validation and serialization models used throughout
the Ask-Docs API. It includes models for API requests, responses, and data
entities such as documents and model selection.

All models use Pydantic's BaseModel for automatic validation and JSON serialization.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ModelName(str, Enum):
    """
    Enumeration of available AI models for query processing.
    
    Attributes:
        GPT4_O (str): OpenAI's GPT-4 Omni model, most capable and recommended
        GPT4_O_MINI (str): OpenAI's GPT-4 Omni Mini model, faster and more cost-effective
    """
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"


class QueryInput(BaseModel):
    """
    Request model for submitting a question to the RAG system.
    
    Attributes:
        question (str): The user's question to be answered by the RAG system (required)
        session_id (str): Optional session identifier for tracking conversation history.
            If not provided, a new session will be created. Default: None
        model (ModelName): The AI model to use for generating responses.
            Default: ModelName.GPT4_O_MINI
    """
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.GPT4_O_MINI)


class QueryResponse(BaseModel):
    """
    Response model for query results from the RAG system.
    
    Attributes:
        answer (str): The AI-generated answer to the user's question
        session_id (str): The session identifier used for this query,
            used for tracking multi-turn conversations
        model (ModelName): The AI model that generated this response
    """
    answer: str
    session_id: str
    model: ModelName


class DocumentInfo(BaseModel):
    """
    Model representing metadata for an uploaded document.
    
    Attributes:
        id (int): Unique database identifier for the document
        filename (str): Original filename of the uploaded document
        upload_timestamp (datetime): Timestamp when the document was uploaded to the system
    """
    id: int
    filename: str
    upload_timestamp: datetime


class DeleteFileRequest(BaseModel):
    """
    Request model for deleting a document from the system.
    
    Attributes:
        file_id (int): The unique identifier of the document to delete
    """
    file_id: int