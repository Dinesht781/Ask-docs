"""
ChromaDB Utilities

This module provides utility functions for managing document indexing and retrieval
using ChromaDB as the vector database. It handles document loading, text splitting,
embedding generation, and vector storage operations for the RAG system.

Supported document formats:
- PDF (.pdf)
- Microsoft Word (.docx)
- HTML (.html)
"""

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize text splitter with 1000-character chunks and 200-character overlap
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

# Initialize OpenAI embedding function
embedding_function = OpenAIEmbeddings()

# Initialize ChromaDB vector store with persistent storage
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)


def load_and_split_document(file_path: str) -> List[Document]:
    """
    Load a document file and split it into smaller chunks for embedding.
    
    Supports multiple document formats and automatically selects the appropriate
    loader based on file extension. Text is split using a recursive character
    splitter to maintain semantic coherence within chunks.
    
    Args:
        file_path (str): The absolute or relative path to the document file.
            Supported formats: .pdf, .docx, .html
            
    Returns:
        List[Document]: A list of Document objects, each representing a chunk of
            the original document with content and metadata.
            
    Raises:
        ValueError: If the file extension is not supported (.pdf, .docx, or .html)
    """
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    documents = loader.load()
    return text_splitter.split_documents(documents)


def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    """
    Load a document and index it into the ChromaDB vector store.
    
    Processes the document by loading, splitting, and embedding its contents,
    then stores the vectors in ChromaDB with file_id metadata for later retrieval
    and deletion. This function is idempotent but overwrites existing entries
    with the same file_id.
    
    Args:
        file_path (str): The path to the document file to index.
        file_id (int): A unique identifier for the document, stored as metadata
            in each vector chunk for tracking and deletion.
            
    Returns:
        bool: True if the document was successfully indexed, False if an error occurred.
        
    Note:
        - Automatically generates embeddings using OpenAI's embedding API
        - Each document chunk includes the file_id in its metadata
        - Errors are logged to stdout for debugging purposes
    """
    try:
        splits = load_and_split_document(file_path)
        
        # Add metadata to each split
        for split in splits:
            split.metadata['file_id'] = file_id
        
        vectorstore.add_documents(splits)
        # vectorstore.persist()
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False


def delete_doc_from_chroma(file_id: int) -> bool:
    """
    Delete all chunks of a document from the ChromaDB vector store.
    
    Removes all vector embeddings associated with a specific document by
    querying and deleting all chunks with the matching file_id metadata.
    This operation is permanent and cannot be undone.
    
    Args:
        file_id (int): The unique identifier of the document to delete.
            This should match the file_id that was assigned during indexing.
            
    Returns:
        bool: True if the document was successfully deleted or no chunks were found,
            False if an error occurred during the deletion process.
            
    Note:
        - Logs the number of chunks found and deleted for debugging
        - Silently handles cases where no chunks exist for the file_id
        - Errors are logged to stdout
    """
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")
        
        vectorstore._collection.delete(where={"file_id": file_id})
        print(f"Deleted all documents with file_id {file_id}")
        
        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False