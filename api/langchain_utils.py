"""
LangChain RAG Chain Utilities

This module creates and configures the Retrieval Augmented Generation (RAG) chain
that powers the question-answering functionality. It combines document retrieval
from ChromaDB with LLM-based answer generation, supporting multi-turn conversations
through chat history awareness.

The RAG chain uses:
- ChromaDB for semantic document retrieval
- Google-Gemini LLMs for answer generation
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict, Any
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
from .chroma_utils import vectorstore

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


def _format_docs(docs: List[Document]) -> str:
    """
    Format retrieved documents into a single context string.
    
    Args:
        docs (List[Document]): List of retrieved document chunks.
        
    Returns:
        str: Formatted context string with document content separated by newlines.
    """
    return "\n\n".join(doc.page_content for doc in docs)


async def get_rag_chain(model="gemini-2.5-flash"):
    """
    Create and return a configured RAG (Retrieval Augmented Generation) chain.
    
    Builds a composable chain using RunnablePassthrough and RunnableParallel that processes queries by:
    1. Contextualizing user questions based on chat history
    2. Retrieving relevant documents from ChromaDB
    3. Formatting retrieved documents into context
    4. Generating answers using an LLM with retrieved context and history
    
    The chain is aware of conversation history and can reference previous
    messages to provide coherent multi-turn responses.
    
    Args:
        model (str): The GEMINI model to use for answer generation.
            Common options: "gemini-2.5-flash", "gemini-2.0-flash"
            Default: "gemini-2.5-flash"
            
    Returns:
        Runnable: A LangChain Runnable chain that accepts:
            - input (str): The user's question
            - chat_history (List[Dict]): List of previous messages with roles and content
            
            The chain returns a string with the AI-generated answer.
            
    Note:
        - The retriever fetches the top 2 most relevant documents
    """
    llm = ChatGoogleGenerativeAI(model=model, temperature=0)
    
    # Step 1: Contextualize question with chat history
    contextualize_chain = contextualize_q_prompt | llm | StrOutputParser()

    rag_chain = (
        RunnablePassthrough.assign(
            standalone_question=lambda x: contextualize_chain.invoke(x)
        )
        .assign(
            context=lambda x: _format_docs(
                retriever.invoke(x["standalone_question"])
            )
        )
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
