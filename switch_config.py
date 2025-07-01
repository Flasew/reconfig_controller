from dataclasses import dataclass

@dataclass
class HostInformation:
    host_id: int  # host id in integer
    host_name: str  # host name
    ip_addr: str  # host WAN IP address used for reconfiguration message
    nic_id: int  # NIC id in integer for the reconfigurable interface

@dataclass
class SwitchConfiguration:
    """
    This is a generic class that we want to use to describe a particular
    configuration of a switch.
    connections: a list of tuples, where each tuple is a truplet of integers
    representing the connection between two hosts and the wavelength ID.
    Wavelength ID is ignored for now, but it is used to identify the connection.
    duration: an integer representing the duration of the configuration im ms
    ring_configs: a dictionary mapping ring IDs to their voltage
    """
    connections: list[tuple[int, int, int]]  # list of connections (host1, host2, wavelength_id)
    duration: int
    ring_configs: tuple[int, float]
    

SWITCH_CONFIG_1 = SwitchConfiguration(
    connections=[
        (1, 2, 1), 
        (2, 1, 1),
        (3, 4, 1), 
        (4, 3, 1),
    ], 
    duration=10000,
    ring_configs={
        (88, 1.61),
        (87, 1.62),
        (83, 1.64),
        (82, 1.63),
        (64, 1.46),

        (80, 1.48),
        (81, 1.48),
        (92, 1.54),
        (91, 1.54),
        (53, 1.62),

        (8, 1.88),
        (7, 1.83),
        (23, 1.84),
        (24, 1.85),
        
        (20, 1.74),
        (16, 1.69),
        (15, 1.70),
        (14, 1.75),
        (43, 1.9),
    }
)

SWITCH_CONFIG_2 = SwitchConfiguration(
    connections=[
        (1, 4, 1), 
        (4, 1, 1),
        (2, 3, 1), 
        (3, 2, 1),
    ], 
    duration=10000,
    ring_configs={
        (69, 1.44),
        (70, 1.49),
        (23, 1.49),
        (24, 1.49),

        (11, 1.75),
        (10, 1.79),
        (83, 1.75),
        (82, 1.74),
        (64, 1.46),

        (79, 1.66),
        (78, 1.60),
        (15, 1.59),
        (14, 1.62),
        (41, 1.89),

        (4, 1.92),
        (3, 1.86),
        (90, 1.86),
        (89, 1.83),
        (53, 1.62),
    }
)

SW_CONFIGS = [SWITCH_CONFIG_1, SWITCH_CONFIG_2]

HOSTS = [
    HostInformation(1, "host1", "Host1", 17),
    HostInformation(2, "host2", "Host2", 19),
    HostInformation(3, "host3", "Host3", 19),
    HostInformation(4, "host4", "Host4", 17),
]