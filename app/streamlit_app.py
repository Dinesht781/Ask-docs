"""
Ask-Docs Streamlit Web Application

This module implements the frontend user interface for the Ask-Docs RAG system.
It provides an interactive chat interface with document management capabilities,
allowing users to:
- Ask questions about uploaded documents
- Upload new documents (PDF, DOCX, HTML)
- Manage document collections
- Select AI models for responses
- Maintain multi-turn conversations

Features:
- Real-time WebSocket-based chat communication
- Document upload and indexing
- Chat history tracking per session
- Model selection (GEMINI-2.5-FLASH, GEMINI-2.0-FLASH)
"""

import streamlit as st
from sidebar import display_sidebar
from chat_interface import display_chat_interface

st.title("Langchain RAG Chatbot")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Display the sidebar
display_sidebar()

# Display the chat interface
display_chat_interface()
