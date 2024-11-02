import streamlit as st
from api_utils import get_api_response

# chat_interface.py
import streamlit as st
import asyncio
from api_utils import websocket_communicate

def display_chat_interface():
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
