"""
LangChain RAG Chain Utilities

This module creates and configures the Retrieval Augmented Generation (RAG) chain
that powers the question-answering functionality. It combines document retrieval
from ChromaDB with LLM-based answer generation, supporting multi-turn conversations
through chat history awareness.

The RAG chain uses:
- ChromaDB for semantic document retrieval
- OpenAI LLMs for answer generation
- History-aware retriever for context-aware responses
"""

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
from chroma_utils import vectorstore

load_dotenv()

# Initialize document retriever from ChromaDB with k=2 (top 2 relevant documents)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

output_parser = StrOutputParser()


# System prompts for the RAG chain

# Contextualize the user's question based on chat history
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

# Prompt template for contextualizing questions with chat history
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


# Main QA prompt that combines context from retrieved documents and chat history
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use the following context to answer the user's question."),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


async def get_rag_chain(model="gpt-4o-mini"):
    """
    Create and return a configured RAG (Retrieval Augmented Generation) chain.
    
    Builds a chain that processes queries by:
    1. Contextualizing user questions based on chat history
    2. Retrieving relevant documents from ChromaDB
    3. Generating answers using an LLM with retrieved context
    
    The chain is aware of conversation history and can reference previous
    messages to provide coherent multi-turn responses.
    
    Args:
        model (str): The OpenAI model to use for answer generation.
            Common options: "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"
            Default: "gpt-4o-mini"
            
    Returns:
        Chain: A LangChain chain object that accepts:
            - input (str): The user's question
            - chat_history (List[Dict]): List of previous messages with roles and content
            
            The chain returns a dict with:
            - answer (str): The generated response
            - context (List[Document]): Retrieved document chunks used for response
            
    Note:
        - The retriever fetches the top 2 most relevant documents
        - The LLM model must be supported by OpenAI API
        - Requires OPENAI_API_KEY environment variable to be set
    """
    llm = ChatOpenAI(model=model)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)    
    return rag_chain
