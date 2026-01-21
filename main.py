import asyncio
import signal

from core.server import start_servers, stop_servers
from telemetry.logger import get_logger

logger = get_logger("ddospot.main")


async def main():
    logger.info("Starting DDoSPot")

    await start_servers()

    stop_event = asyncio.Event()

    def shutdown():
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    await stop_event.wait()

    logger.info("Stopping servers")
    await stop_servers()
    logger.info("DDoSPot stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())
