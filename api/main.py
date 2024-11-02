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
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
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
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
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
