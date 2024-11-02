# import asyncio
# import websockets

# async def send_message(message):
#     async with websockets.connect("ws://localhost:8000/ws") as websocket:
#         await websocket.send(message)
#         response = await websocket.recv()
#         print(response)

# asyncio.run(send_message("Hello, World!"))
import asyncio
import websockets
async def connect_websocket():
    
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            try:
                await websocket.send("where is Puttur located?!")
                response = await websocket.recv()
                print(f"Received: {response}")
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed unexpectedly: {e}")
            finally:
                await websocket.close()
asyncio.run(connect_websocket())