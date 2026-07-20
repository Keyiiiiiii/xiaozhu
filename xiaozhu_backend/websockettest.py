import asyncio
import websockets
import json

async def main():
    job_id = input("请输入 job_id: ").strip()
    async with websockets.connect(f'ws://localhost:8000/ws/asr/{job_id}/') as ws:
        print(f'已连接到 ws://localhost:8000/ws/asr/{job_id}/')
        print('等待转写结果...')
        message = await ws.recv()
        data = json.loads(message)
        print('\n转写结果:')
        print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())