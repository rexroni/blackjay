import asyncio
import websockets
import os
import sys

async def hello():
    async with websockets.connect('ws://localhost:8765') as websocket:
        # .5MB blocks of data
        BS = 500000

        size = os.stat(sys.argv[1]).st_size
        blocks,extra = divmod(size,BS)
        print('b,e %d,%d'%(blocks,extra))
        numblocks = blocks + (extra < 0)
        print('numblocks %d'%numblocks)

        await websocket.send(str(numblocks))

        with open(sys.argv[1],'rb') as f:
            for i in range(numblocks):
                data = f.read(BS)
                await websocket.send(data)


asyncio.get_event_loop().run_until_complete(hello())

