"""
WebSocket Test Module

This module contains test code for verifying WebSocket communication with the
Ask-Docs backend API. It's used for debugging and validating real-time chat
functionality through direct WebSocket connections.

This is a development/testing module and should not be used in production.
"""

import asyncio
import websockets


# Alternative test function (commented out)
# async def send_message(message):
#     """
#     Send a single message through WebSocket and receive a response.
#     
#     Args:
#         message (str): The message to send
#         
#     Returns:
#         None
#     """
#     async with websockets.connect("ws://localhost:8000/ws") as websocket:
#         await websocket.send(message)
#         response = await websocket.recv()
#         print(response)

# asyncio.run(send_message("Hello, World!"))


async def connect_websocket():
    """
    Establish a WebSocket connection and test message sending/receiving.
    
    Connects to the backend WebSocket server, sends a test query, receives a response,
    and handles connection errors gracefully. Used for debugging WebSocket functionality
    and testing the backend's real-time communication capabilities.
    
    Args:
        None
        
    Returns:
        None
        
    Side Effects:
        - Prints received response to stdout
        - Prints connection errors if they occur
        
    Note:
        - Requires the FastAPI backend to be running at ws://localhost:8000/ws
        - This is a test/debugging function and should not be used in production
        - Connection is gracefully closed in the finally block
    """
    async with websockets.connect("ws://localhost:8000/ws") as websocket:
        try:
            await websocket.send("where is Puttur located?!")
            response = await websocket.recv()
            print(f"Received: {response}")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed unexpectedly: {e}")
        finally:
            await websocket.close()


# Run the WebSocket connection test
asyncio.run(connect_websocket())