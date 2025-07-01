import socket
import struct
import sys
import time

from switch_config import SwitchConfiguration, HostInformation

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_public_ip():
    try:
        # Create a UDP socket and connect to an external address (Google's DNS)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception as e:
        logger.error(f"Error getting public-facing IP: {e}")
        return None

def checksum(data):
    """Compute the checksum of the given data."""
    if len(data) % 2 == 1:
        data += b"\x00"

    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s & 0xFFFF) + (s >> 16)
    s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


def pretty_print_icmp_packet(packet):
    """Decode and pretty print the ICMP packet."""
    ip_header = packet[:20]
    icmp_header = packet[20:28]

    iph = struct.unpack("!BBHHHBBH4s4s", ip_header)
    icmph = struct.unpack("!BBHHBB", icmp_header)

    logger.debug("IP Header:")
    logger.debug(f" - Version: {iph[0] >> 4}")
    logger.debug(f" - IHL: {iph[0] & 0xF}")
    logger.debug(f" - TTL: {iph[5]}")
    logger.debug(f" - Protocol: {iph[6]}")
    logger.debug(f" - Source IP: {socket.inet_ntoa(iph[8])}")
    logger.debug(f" - Destination IP: {socket.inet_ntoa(iph[9])}")

    logger.debug("ICMP Header:")
    logger.debug(f" - Type: {icmph[0]}")
    logger.debug(f" - Code: {icmph[1]}")
    logger.debug(f" - Checksum: {icmph[2]}")
    logger.debug(f" - Destination ID: {icmph[3]}")
    logger.debug(f" - Source Port: {icmph[4]}")
    logger.debug(f" - Destination Port: {icmph[5]}")


class ICMPController:
    def __init__(
        self,
        my_ip: str,
        hosts: list[HostInformation],
        sw_configs: list[SwitchConfiguration],
    ):
        self.my_ip = my_ip
        self.hosts = {host.host_id: host for host in hosts}
        self.sw_configs = sw_configs

        # index: [configuration][connection]
        self.reconfig_start_messages = [
            [
                self.generate_icmp_message_string(
                    self.hosts[conn[0]],
                    self.hosts[conn[1]],
                    0,
                )
                for conn in config.connections
            ]
            for config in self.sw_configs
        ]
        self.reconfig_finish_messages = [
            [
                self.generate_icmp_message_string(
                    self.hosts[conn[0]],
                    self.hosts[conn[1]],
                    1,
                )
                for conn in config.connections
            ]
            for config in self.sw_configs
        ]

        self.socket_fd = self.create_raw_socket()

        # slight faster access
        self.dst_ip_to_send = [
            [self.hosts[conn[0]].ip_addr for conn in config.connections]
            for config in self.sw_configs
        ]

    def create_raw_socket(self):
        """Create a raw socket for sending ICMP packets."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.bind((self.my_ip, 0))
        except socket.error as e:
            logger.error(f"Socket creation failed: {e}")
            sys.exit(1)

        # Set socket option so that we provide the IP header
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except socket.error as e:
            logger.error(f"setsockopt() failed: {e}")
            sys.exit(1)

        return sock

    def generate_icmp_message_string(
        self, src_host: HostInformation, dst_host: HostInformation, code: int
    ):
        srcip_str = src_host.ip_addr
        dstip_str = dst_host.ip_addr
        src_port = src_host.nic_id
        dst_port = dst_host.nic_id

        # The packet is sent from the control server to the source of the
        # new configuration, hence the "try" block.
        try:
            srcip = socket.inet_aton(self.my_ip)
            dstip = socket.inet_aton(srcip_str)
        except socket.error:
            logger.error("Invalid IP address format")
            sys.exit(1)

        # Construct IP header
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,  # Version & IHL
            0,  # Type of Service
            20 + 8,  # Total Length (IP header + ICMP header)
            0,  # Identification
            0,  # Flags & Fragment Offset
            64,  # Time to Live
            socket.IPPROTO_ICMP,  # Protocol
            0,  # Header checksum (initially 0)
            srcip,  # Source IP
            dstip,  # Destination IP
        )

        # Construct ICMP header
        icmp_type = 9  # Custom ICMP type
        icmp_code = code
        icmp_checksum = 0  # Will be calculated later
        icmp_dst_id = struct.pack("!H", dst_host.host_id)
        icmp_src_port = struct.pack("!B", src_port)
        icmp_dst_port = struct.pack("!B", dst_port)

        icmp_header = (
            struct.pack("!BBH", icmp_type, icmp_code, icmp_checksum)
            + icmp_dst_id
            + icmp_src_port
            + icmp_dst_port
        )

        # Compute ICMP checksum
        icmp_checksum = checksum(icmp_header)
        icmp_header = (
            struct.pack("!BBH", icmp_type, icmp_code, icmp_checksum)
            + icmp_dst_id
            + icmp_src_port
            + icmp_dst_port
        )

        # Compute IP checksum
        ip_checksum = checksum(ip_header)
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            20 + 8,
            0,
            0,
            64,
            socket.IPPROTO_ICMP,
            ip_checksum,
            srcip,
            dstip,
        )

        # Construct final packet
        packet = ip_header + icmp_header

        return packet

    def reconfig_start(self, config_id: int):
        logger.info("====================================")
        logger.info("config start")
        logger.info("------------------------------------")
        for i, msg in enumerate(self.reconfig_start_messages[config_id]):
            logger.info(f"sending to {self.dst_ip_to_send[config_id][i]}.")
            pretty_print_icmp_packet(msg)
            logger.debug('Packet: ')
            self.socket_fd.sendto(msg, (self.dst_ip_to_send[config_id][i], 0))

    def reconfig_finish(self, config_id: int):
        print("config finish")
        logger.info("------------------------------------")
        for i, msg in enumerate(self.reconfig_finish_messages[config_id]):
            logger.info(f"sending to {self.dst_ip_to_send[config_id][i]}.")
            pretty_print_icmp_packet(msg)
            logger.debug('Packet:')
            self.socket_fd.sendto(msg, (self.dst_ip_to_send[config_id][i], 0))
        logger.info("====================================")
        return self.sw_configs[config_id].duration
