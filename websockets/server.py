import asyncio
import websockets

async def hello(websocket, path):
    header = await websocket.recv()
    numpackets = int(header)
    print('receiving %d packets'%numpackets)

    with open('recvd','wb') as f:
        for i in range(numpackets):
            f.write(await websocket.recv())

start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

