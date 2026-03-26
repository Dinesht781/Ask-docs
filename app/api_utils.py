"""
API Utilities Module

This module provides utility functions for communicating with the backend FastAPI
server. It handles both WebSocket connections for real-time chat and HTTP requests
for document and query operations.

Functions:
- WebSocket communication for real-time chat responses
- REST API calls for document operations (upload, list, delete)
- REST API calls for query processing
- Error handling and user feedback

All functions integrate with Streamlit for UI updates and error display.
"""

import requests
import streamlit as st
import asyncio
import websockets


async def websocket_communicate(question, session_id, model="gpt-4o-mini"):
    """
    Communicate with the backend via WebSocket for real-time chat responses.
    
    Establishes a WebSocket connection to the backend server, sends a user question,
    and streams responses in real-time. Each response is appended to the chat
    message history and displayed in the Streamlit UI immediately.
    
    Args:
        question (str): The user's question to send to the backend.
        session_id (str): Session identifier for conversation tracking. May be None
            for new sessions (backend will generate one).
        model (str): The AI model to use for response generation.
            Default: "gpt-4o-mini"
            
    Returns:
        None
        
    Side Effects:
        - Adds received responses to st.session_state.messages as assistant messages
        - Displays messages in chat interface
        - Shows error messages to user via st.error() if connection fails
        
    Raises (caught internally):
        - websockets.exceptions.ConnectionClosedError: WebSocket connection closed unexpectedly
        - Exception: General WebSocket communication errors
        
    Note:
        WebSocket endpoint must be running at ws://localhost:8000/ws
    """
    uri = "ws://localhost:8000/ws"  # WebSocket endpoint
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(question)  # Send the question to WebSocket server
            
            while True:
                response = await websocket.recv()  # Receive AI response from server
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                with st.chat_message("assistant"):
                    st.markdown(response)
    except websockets.exceptions.ConnectionClosedError:
        st.error("Connection to the WebSocket server was closed.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


def get_api_response(question, session_id, model):
    """
    Send a query to the backend RESTful API and retrieve the response.
    
    Makes a POST request to the /chat endpoint with the user's question
    and session context. Returns the AI-generated response along with
    session and model information.
    
    Args:
        question (str): The user's question to submit.
        session_id (str): Session identifier for conversation tracking, may be None.
        model (str): The AI model to use for response generation.
            
    Returns:
        dict: Response dictionary containing:
            - answer (str): The AI-generated response
            - session_id (str): The session ID for tracking
            - model (str): The model used
            
            Returns None if the request fails.
            
    Raises (caught internally):
        - requests.exceptions.RequestException: Network or HTTP errors
        - ValueError: JSON parsing errors in response
        
    Note:
        - API server must be running at http://localhost:8000/chat
        - Error messages are displayed to user via st.error()
        - Only includes session_id in request if it's provided
    """
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model
    }
    if session_id:
        data["session_id"] = session_id

    try:
        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None


def upload_document(file):
    """
    Upload a document file to the backend for indexing and storage.
    
    Sends a multipart form-data request to the /upload-doc endpoint with
    the document file. The backend validates the file type, indexes it into
    the vector database, and stores metadata.
    
    Args:
        file: A Streamlit UploadedFile object with attributes:
            - name (str): Original filename
            - type (str): MIME type (e.g., 'application/pdf')
            - content: File data bytes
            
    Returns:
        dict: Response dictionary containing:
            - message (str): Success message with filename
            - file_id (int): Unique identifier for the uploaded document
            
            Returns None if upload fails.
            
    Raises (caught internally):
        - requests.exceptions.RequestException: Network or HTTP errors
        - HTTPError: File format validation errors
        
    Side Effects:
        - Displays success or error messages via st.error()
        
    Note:
        - Supported file types: pdf, docx, html
        - Backend must be running at http://localhost:8000/upload-doc
        - File is validated server-side for format and content
    """
    print("Uploading file...")
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post("http://localhost:8000/upload-doc", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None


def list_documents():
    """
    Retrieve a list of all uploaded documents from the backend.
    
    Makes a GET request to the /list-docs endpoint to fetch metadata
    for all documents in the system, including filenames, IDs, and
    upload timestamps.
    
    Args:
        None
        
    Returns:
        list[dict]: List of document dictionaries, each containing:
            - id (int): Unique document identifier
            - filename (str): Original document filename
            - upload_timestamp (str/datetime): Document upload time
            
            Returns an empty list if fetch fails or no documents exist.
            
    Raises (caught internally):
        - requests.exceptions.RequestException: Network or HTTP errors
        - ValueError: JSON parsing errors
        
    Side Effects:
        - Displays error messages via st.error() if request fails
        
    Note:
        - Backend must be running at http://localhost:8000/list-docs
        - Results are sorted by upload timestamp (newest first)
    """
    try:
        response = requests.get("http://localhost:8000/list-docs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []


def delete_document(file_id):
    """
    Delete a document from the system using its file ID.
    
    Makes a POST request to the /delete-doc endpoint to remove a document
    from both the vector store and the application database.
    
    Args:
        file_id (int): The unique identifier of the document to delete.
            This ID is returned when a document is uploaded.
            
    Returns:
        dict: Response dictionary containing either:
            - message (str): Success message confirming deletion
            - error (str): Error message if deletion failed
            
            Returns None if the request fails entirely.
            
    Raises (caught internally):
        - requests.exceptions.RequestException: Network or HTTP errors
        - ValueError: JSON parsing errors
        
    Side Effects:
        - Displays error messages via st.error() if request fails
        
    Note:
        - Backend must be running at http://localhost:8000/delete-doc
        - Deletion affects both vector store and database
        - Operation may take time for large documents with many chunks
    """
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {"file_id": file_id}

    try:
        response = requests.post("http://localhost:8000/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None