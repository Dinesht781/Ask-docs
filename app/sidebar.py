"""
Sidebar Component Module

This module implements the sidebar component for the Streamlit application.
It provides UI controls for document management and model selection, including:
- AI model selection (GEMINI-2.5-FLASH, GEMINI-2.0-FLASH)
- Document upload functionality
- Document list display and management
- Document deletion capabilities
- Document list refresh

The sidebar maintains the document list in session state for efficient
re-rendering and manages all file operations through API calls.
"""

import streamlit as st
from api_utils import upload_document, list_documents, delete_document


def display_sidebar():
    """
    Display and manage the sidebar component.
    
    Renders the sidebar with the following sections:
    1. Model Selection: Choose between GEMINI-2.5-FLASH & GEMINI-2.0-FLASH
    2. Document Upload: Upload new documents (PDF, DOCX, HTML)
    3. Document List: Display all uploaded documents with metadata
    4. Document Deletion: Select and delete documents
    
    Manages API calls for document operations and maintains session state
    for efficient UI updates. Document list is cached in session state and
    refreshed when documents are uploaded or deleted.
    
    Args:
        None
        
    Returns:
        None
        
    Session State Variables Modified:
        - model (str): Selected AI model, defaults to last selection
        - documents (list): List of available documents with metadata
        
    Features:
        - File type validation (pdf, docx, html)
        - User feedback with success/error messages
        - Automatic document list refresh after operations
        - Loading indicators for better UX
    """
    # Sidebar: Model Selection
    model_options = ["gemini-2.5-flash", "gemini-2.0-flash"]
    st.sidebar.selectbox("Select Model", options=model_options, key="model")

    # Sidebar: Upload Document
    st.sidebar.header("Upload Document")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file is not None:
        if st.sidebar.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    st.sidebar.success(f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                    st.session_state.documents = list_documents()  # Refresh the list after upload

    # Sidebar: List Documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        with st.spinner("Refreshing..."):
            st.session_state.documents = list_documents()

    # Initialize document list if not present
    if "documents" not in st.session_state:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents
    if documents:
        for doc in documents:
            st.sidebar.text(f"{doc['filename']} (ID: {doc['id']}, Uploaded: {doc['upload_timestamp']})")
        
        # Delete Document
        selected_file_id = st.sidebar.selectbox("Select a document to delete", options=[doc['id'] for doc in documents], format_func=lambda x: next(doc['filename'] for doc in documents if doc['id'] == x))
        if st.sidebar.button("Delete Selected Document"):
            with st.spinner("Deleting..."):
                delete_response = delete_document(selected_file_id)
                if delete_response:
                    st.sidebar.success(f"Document with ID {selected_file_id} deleted successfully.")
                    st.session_state.documents = list_documents()  # Refresh the list after deletion
                else:
                    st.sidebar.error(f"Failed to delete document with ID {selected_file_id}.")
