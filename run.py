from switch_config import HostInformation, SW_CONFIGS, HOSTS
from switch_ctrl import SwitchController
from icmp_ctrl import ICMPController, get_public_ip
import time

PRE_GUARD = 50  # milliseconds
POST_GUARD = 7000  # milliseconds

def main():
    # Initialize the switch controller with the serial port name
    switch_controller = SwitchController('/dev/ttyUSB1', SW_CONFIGS)
    
    # Initialize the ICMP controller with the switch configurations
    icmp_controller = ICMPController(
        my_ip=get_public_ip(),
        hosts=HOSTS,
        sw_configs=SW_CONFIGS,
    )

    # zero the switch controller
    switch_controller.zero(verify=False)
    
    # loop across two configurations
    curr_config = 0
    while True:
        # reconfigure the switch
        print(f"Switching to configuration {curr_config}")
        icmp_controller.reconfig_start(curr_config)
        time.sleep(PRE_GUARD / 1000)  # wait for the pre guard time to make sure hosts are down
        switch_controller.zero(verify=False)
        switch_controller.set_configuration(curr_config)
        time.sleep(POST_GUARD / 1000)  # wait for the guard time
        duration = icmp_controller.reconfig_finish(curr_config)
        # switch to the next configuration
        print(f"Switched to configuration {curr_config} and waiting for {duration} ms") 
        curr_config = (curr_config + 1) % len(SW_CONFIGS)
        time.sleep(duration / 1000)  # wait for the duration of the configuration

if __name__ == "__main__":
    main()
    
     
            
