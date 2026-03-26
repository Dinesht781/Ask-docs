"""
Database Utilities

This module provides functions for managing SQLite database operations,
including storing application logs, chat history, and document metadata.

The database consists of two main tables:
- application_logs: Tracks user queries, AI responses, and model usage
- document_store: Maintains metadata for uploaded documents

Tables are automatically initialized on module import.
"""

import sqlite3
from datetime import datetime

DB_NAME = "rag_app.db"


def get_db_connection():
    """
    Establish and return a connection to the SQLite database.
    
    Creates a new connection with row factory set to sqlite3.Row for
    convenient access to query results by column name.
    
    Args:
        None
        
    Returns:
        sqlite3.Connection: A database connection object configured to return
            rows as sqlite3.Row objects with dictionary-like access.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_application_logs():
    """
    Create the application_logs table if it does not already exist.
    
    The table stores all user queries and associated AI responses for
    auditing and history purposes. Each record includes session tracking
    for multi-turn conversations.
    
    Args:
        None
        
    Returns:
        None
        
    Database Schema:
        - id (INTEGER PRIMARY KEY): Auto-incrementing record identifier
        - session_id (TEXT): Session identifier for grouping related conversations
        - user_query (TEXT): The user's original question
        - gpt_response (TEXT): The AI-generated response
        - model (TEXT): The AI model used to generate the response
        - created_at (TIMESTAMP): Record creation timestamp, defaults to current time
    """
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     session_id TEXT,
                     user_query TEXT,
                     gpt_response TEXT,
                     model TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()


def insert_application_logs(session_id, user_query, gpt_response, model):
    """
    Insert a new application log entry recording a user query and AI response.
    
    Creates a permanent record of the interaction for audit trails, debugging,
    and model performance analysis.
    
    Args:
        session_id (str): Unique session identifier for tracking multi-turn conversations
        user_query (str): The original user question
        gpt_response (str): The AI-generated response
        model (str): Name of the AI model used (e.g., "gemini-2.5-flash", "gemini-2.0-flash")
        
    Returns:
        None
    """
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                 (session_id, user_query, gpt_response, model))
    conn.commit()
    conn.close()


def get_chat_history(session_id):
    """
    Retrieve all messages from a specific session in chronological order.
    
    Retrieves all user queries and AI responses for a given session and
    formats them as a list of message dictionaries compatible with LangChain's
    chat history format.
    
    Args:
        session_id (str): The session identifier to retrieve history for
        
    Returns:
        list[dict]: A list of message dictionaries with structure:
            [
                {"role": "human", "content": "user query 1"},
                {"role": "ai", "content": "ai response 1"},
                {"role": "human", "content": "user query 2"},
                {"role": "ai", "content": "ai response 2"},
                ...
            ]
            
            Returns an empty list if no messages exist for the session_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at', (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['gpt_response']}
        ])
    conn.close()
    return messages


def create_document_store():
    """
    Create the document_store table if it does not already exist.
    
    The table maintains metadata for all uploaded documents, tracking
    their filenames and upload timestamps.
    
    Args:
        None
        
    Returns:
        None
        
    Database Schema:
        - id (INTEGER PRIMARY KEY): Auto-incrementing unique document identifier
        - filename (TEXT): Original filename of the uploaded document
        - upload_timestamp (TIMESTAMP): When the document was uploaded, defaults to current time
    """
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     filename TEXT,
                     upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()


def insert_document_record(filename):
    """
    Insert a new document record into the database and return its ID.
    
    Creates a metadata record for an uploaded document before it is indexed
    into the vector database. The returned ID should be used to associate
    vector chunks with this document.
    
    Args:
        filename (str): The original filename of the uploaded document
        
    Returns:
        int: The auto-generated primary key ID of the inserted document record.
            Use this ID when indexing the document to ChromaDB.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO document_store (filename) VALUES (?)', (filename,))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id


def delete_document_record(file_id):
    """
    Delete a document record from the database by its ID.
    
    Removes the metadata entry for a document. Should be called after
    the document has been successfully deleted from the vector store.
    
    Args:
        file_id (int): The document ID to delete
        
    Returns:
        bool: Always returns True if execution completes (assumes successful deletion)
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return True


def get_all_documents():
    """
    Retrieve metadata for all documents in the system.
    
    Fetches all document records sorted by upload timestamp in descending order
    (newest first), useful for displaying document lists in the UI.
    
    Args:
        None
        
    Returns:
        list[dict]: A list of document dictionaries with keys:
            - id (int): Unique document identifier
            - filename (str): Original document filename
            - upload_timestamp (str/datetime): When the document was uploaded
            
            Returns an empty list if no documents exist in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
    documents = cursor.fetchall()
    conn.close()
    return [dict(doc) for doc in documents]


# Initialize the database tables
create_application_logs()
create_document_store()
