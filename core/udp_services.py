import asyncio

class BaseUDP(asyncio.DatagramProtocol):
    def __init__(self, state, logger, service_name):
        self.state = state
        self.logger = logger
        self.service = service_name

    def datagram_received(self, data, addr):
        ip, port = addr

        if self.state.is_blacklisted(ip):
            return

        asyncio.create_task(
            self.logger.log_event(
                event_type="packet",
                protocol="udp",
                service=self.service,
                source_ip=ip,
                source_port=port,
                details={
                    "size": len(data),
                },
            )
        )
