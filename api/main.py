"""
Ask-Docs FastAPI Application

This module implements the backend API for the Ask-Docs document Q&A system.
It provides REST endpoints and WebSocket connections for:
- Querying documents using a RAG (Retrieval Augmented Generation) model
- Uploading and indexing documents
- Managing chat history and sessions
- Document lifecycle management (list, delete)

The API integrates LangChain for RAG functionality, ChromaDB for vector storage,
and SQLite for application state management.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from langchain_utils import get_rag_chain
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import os
import uuid
import logging
from dotenv import load_dotenv
from fastapi import UploadFile, File, HTTPException
import shutil

logging.basicConfig(filename='app.log', level=logging.INFO)
app = FastAPI()
load_dotenv()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.
    
    This class handles multiple concurrent WebSocket connections, allowing
    bidirectional communication with multiple clients and supporting broadcast
    messages to all connected clients.
    """

    def __init__(self):
        """
        Initialize the ConnectionManager.
        
        Args:
            None
            
        Returns:
            None
        """
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket (WebSocket): The WebSocket connection to accept and register.
            
        Returns:
            None
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Unregister and close a WebSocket connection.
        
        Args:
            websocket (WebSocket): The WebSocket connection to disconnect.
            
        Returns:
            None
        """
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """
        Send a message to all connected WebSocket clients.
        
        Args:
            message (str): The text message to broadcast to all connections.
            
        Returns:
            None
        """
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket) 

#     # session_id = str(uuid.uuid4())  # Generate session ID on websocket connection
#     try:
#         while True:
#             user_msg = await websocket.receive_text()
#             # Create QueryInput object with received message and session ID
#             query_input = QueryInput(question=user_msg)
#             # Call the chat function with the QueryInput object
#             response = await chat(query_input)
#             # Send the AI's response back to the user through websocket
#             await websocket.send_text(f"AI: {response.answer}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client disconnected")

# main.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat communication.
    
    Establishes a WebSocket connection with a client and processes incoming
    queries through the RAG system, returning real-time responses.
    
    Args:
        websocket (WebSocket): The WebSocket connection object.
        
    Returns:
        None
    """
    await manager.connect(websocket) 

    try:
        while True:
            # Wait for message from client
            user_msg = await websocket.receive_text()
            
            # Process the incoming message with the RAG system
            query_input = QueryInput(question=user_msg, session_id=str(uuid.uuid4()))
            response = await chat(query_input)
            
            # Send AI's response back to the client via WebSocket
            await websocket.send_text(response.answer)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("Client disconnected")

@app.post("/chat", response_model=QueryResponse)
async def chat(query_input: QueryInput):
    """
    Process a user query and return an AI-generated response using RAG.
    
    Retrieves chat history for the session, queries the RAG chain with the user's
    question, logs the interaction, and returns the response with session information.
    
    Args:
        query_input (QueryInput): Pydantic model containing the user's question,
            optional session ID, and selected model name.
            
    Returns:
        QueryResponse: Pydantic model containing:
            - answer (str): The AI-generated response
            - session_id (str): The session ID for tracking conversation history
            - model (ModelName): The model used to generate the response
    """
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    

    chat_history =  get_chat_history(session_id)
    rag_chain = await get_rag_chain(query_input.model.value)
    answer = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })['answer']
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)



@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    """
    Upload and index a document for RAG retrieval.
    
    Accepts a document file (PDF, DOCX, or HTML), validates its format,
    stores it temporarily, indexes it into the ChromaDB vector store,
    and records metadata in the application database.
    
    Args:
        file (UploadFile): The document file to upload (required). Supported formats:
            - .pdf: PDF documents
            - .docx: Microsoft Word documents
            - .html: HTML files
            
    Returns:
        dict: A dictionary containing:
            - message (str): Success message with file name
            - file_id (int): Unique identifier for the indexed document
            
    Raises:
        HTTPException: 400 if file type is not supported
        HTTPException: 500 if document indexing fails
    """
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")
    
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    """
    Retrieve a list of all uploaded documents.
    
    Fetches metadata for all documents that have been uploaded and indexed
    in the system, sorted by upload timestamp in descending order.
    
    Args:
        None
        
    Returns:
        list[DocumentInfo]: A list of DocumentInfo objects containing:
            - id (int): Unique document identifier
            - filename (str): Original filename of the document
            - upload_timestamp (datetime): When the document was uploaded
    """
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    """
    Delete a document from the RAG system.
    
    Removes a document from both the ChromaDB vector store and the application
    database. The document is identified by its file_id.
    
    Args:
        request (DeleteFileRequest): Contains:
            - file_id (int): The ID of the document to delete
            
    Returns:
        dict: A dictionary containing either:
            - message (str): Success message confirming deletion
            - error (str): Error message if deletion fails
            
    Note:
        If deletion from ChromaDB succeeds but database deletion fails,
        the function returns a partial deletion message to alert the user.
    """
    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}
    
    
    
    
# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             # await manager.broadcast(f"Client #{client_id} says: {data}")
            
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"{client_id} left the chat")
#         await process_user_message(data)
#         await manager.broadcast(f"{client_id} says: {data}")


# async def process_user_message(session_id: str, message: str):
#     """Processes a user message received via WebSocket.

#     Args:
#         session_id (str): The unique identifier for the user's session.
#         message (str): The message received from the user.
#     """

#     query_input = QueryInput(question=message, session_id=session_id)
#     response = await chat(query_input)

#     # Handle the response and send it back to the user
#     await manager.broadcast(f"AI: {response.answer}")
