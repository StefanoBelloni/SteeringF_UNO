# from joystick.joy6 import run
from joystick.runner import execute

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

if __name__ == '__main__':
    try:
        print_banner()
        execute('/dev/ttyACM0')
    except Exception as e:
        print("[ERROR] Exception:", e)
    finally:
        print("[INFO] -----------------------------------------------------")
        print("[INFO] USEFUL COMMANDS")
        print("[INFO]   # run 'sudo chmod +0666 /dev/uinput' to activate")
        print("[INFO]   # run 'jstest-gtk' to confugure")
        print("[INFO] -----------------------------------------------------")
