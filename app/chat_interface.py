"""
Chat Interface Module

This module implements the chat interface component for the Streamlit application.
It handles the display of chat messages, user input, and communication with the
backend API through WebSocket and REST endpoints.

Features:
- Real-time message display with role-based styling
- User input handling
- WebSocket-based real-time response streaming
- Session state management
- Error handling and user feedback
"""

import streamlit as st
from api_utils import get_api_response,websocket_communicate
import asyncio

def display_chat_interface():
    """
    Display and manage the chat interface component.
    
    Renders the chat message history, accepts user input, and processes
    queries through the backend RAG system using WebSocket communication.
    Messages are displayed in real-time as they are received from the server.
    
    The function manages:
    - Chat history display with role-based formatting
    - User input capture and validation
    - Real-time message streaming via WebSocket
    - Session state updates for multi-turn conversations
    
    Args:
        None
        
    Returns:
        None
        
    Session State Variables Used:
        - messages (list): Chat history of {"role": "user"/"assistant", "content": str}
        - session_id (str): Unique session identifier for conversation tracking
        - model (str): Selected AI model for response generation
    """
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Query:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Use WebSocket for real-time communication
        with st.spinner("Connecting to WebSocket..."):
            asyncio.run(websocket_communicate(prompt, st.session_state.session_id, st.session_state.model))


# Commented out alternative implementation using REST API
# def display_chat_interface():
#     # Chat interface
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     if prompt := st.chat_input("Query:"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.spinner("Generating response..."):
#             response = get_api_response(prompt, st.session_state.session_id, st.session_state.model)
            
#             if response:
#                 st.session_state.session_id = response.get('session_id')
#                 st.session_state.messages.append({"role": "assistant", "content": response['answer']})
                
#                 with st.chat_message("assistant"):
#                     st.markdown(response['answer'])
                    
#             else:
#                 st.error("Failed to get a response from the API. Please try again.")
