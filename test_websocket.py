import asyncio
import websockets

async def test():
    uri = "ws://localhost:2550/ws/wolftv"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            while True:
                msg = await websocket.recv()
                print(f"Received: {msg}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
