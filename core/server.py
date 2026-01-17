import asyncio
from telemetry.stats import record
from telemetry.logger import log_event
from config import HTTP_PORT, SSH_PORT

async def handle_client(reader, writer, service_name):
    addr = writer.get_extra_info("peername")
    ip = addr[0] if addr else "unknown"

    record(service_name, ip)
    log_event("connection", {
        "service": service_name,
        "ip": ip
    })

    if service_name == "http":
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
    elif service_name == "ssh":
        writer.write(b"SSH-2.0-OpenSSH_8.2p1\r\n")

    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def start_tcp_server(port, service_name):
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, service_name),
        "0.0.0.0",
        port
    )
    print(f"[+] {service_name.upper()} listening on {port}")
    async with server:
        await server.serve_forever()

async def start_servers():
    await asyncio.gather(
        start_tcp_server(HTTP_PORT, "http"),
        start_tcp_server(SSH_PORT, "ssh")
    )
