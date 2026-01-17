import asyncio
from core.server import start_servers

async def main():
    print("Starting honeypot...")
    await start_servers()

if __name__ == "__main__":
    asyncio.run(main())
