import sys
sys.path.insert(1, 'Drivers')
import Qontrol
import pyvisa
import numpy as np
from switch_config import SwitchConfiguration

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwitchController:
    def __init__(self, serial_port_name: str, switch_configs: list[SwitchConfiguration]):
        self.QC = Qontrol.QXOutput(serial_port_name = serial_port_name, response_timeout = 0.5)
        self.switch_configs = switch_configs
        logger.info("Qontroller '{:}' initialised with firmware {:} and {:} channels".format(self.QC.device_id, self.QC.firmware, self.QC.n_chs))

    def zero(self, verify: bool = True):
        if verify:
            print("\n\nWARNING!!! \n\nThis will set the voltage and current on ALL channels to ZERO\n\n")
            print("Would you like to proceed? (y/n)\n")
            value_in = input()
        if not verify or value_in.upper() == "Y":
            self.QC.v[:] = 0
            logger.info("\nZeroing Complete")
        else:
            logger.info("No changes were made")
            
    def set_configuration(self, config_id: int):
        """ 
        Set the switch configuration based on the provided SwitchConfiguration object.
        This method sets the voltages for the rings.
        """
        configuration = self.switch_configs[config_id]
        logger.info(f"Setting configuration {config_id}")
        for ring_id, voltage in configuration.ring_configs:
            self.QC.v[ring_id] = voltage
            logger.info(f"Setting ring {ring_id} to {voltage} V")
