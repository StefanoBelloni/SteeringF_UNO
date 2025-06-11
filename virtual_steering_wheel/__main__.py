import sys
import virtual_steering_wheel.joystick.runner as joystick_runner

def print_banner():
    print("""
# =================================================================================== #

  #####                                         #                                    
 #     # ###### #####  #   ##   #               #  ####  #   #  ####  ##### #  ####  
 #       #      #    # #  #  #  #               # #    #  # #  #        #   # #    # 
  #####  #####  #    # # #    # #               # #    #   #    ####    #   # #      
       # #      #####  # ###### #         #     # #    #   #        #   #   # #      
 #     # #      #   #  # #    # #         #     # #    #   #   #    #   #   # #    # 
  #####  ###### #    # # #    # ######     #####   ####    #    ####    #   #  #### 

(https://manytools.org/hacker-tools/ascii-banner/)
# =================================================================================== #
"""
    )

def get_default_port_and_platform():
    isLinux = False
    if sys.platform.startswith('linux'): 
        port = '/dev/ttyACM0'
        isLinux = False
    elif sys.platform.startswith('win'): 
        port = 'COM3'
    else: 
        port = None
    if len(sys.argv) > 1: 
        port = sys.argv[1]
    return port, isLinux

def print_usage_and_exit():
    print(f"usage: {sys.argv[0]} [serial port]")
    sys.exit(0)

def print_invalid_port_and_exit():
    print("[ERROR] running platform ", sys.platform, ": no default value for the serial port. Provide a port")
    sys.exit(1)

def main():
    port, isLinux = get_default_port_and_platform()
    if port == '-h' or port == '--help':
        print_usage_and_exit()
    elif port is None:
        print_invalid_port_and_exit()
    # =========================================== #
    print("[INFO] Reading serial port: ", port)
    # =========================================== #
    try:
        print_banner()
        joystick_runner.execute(port)
    except Exception as e:
        print("[ERROR] Exception:", e)
    finally:
        if isLinux:
            print("[INFO] -----------------------------------------------------")
            print("[INFO] USEFUL COMMANDS")
            print("[INFO]   # run 'sudo chmod +0666 /dev/uinput' to activate")
            print("[INFO]   # run 'jstest-gtk' to confugure")
            print("[INFO] -----------------------------------------------------")


if __name__ == '__main__':
    main()
