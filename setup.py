from setuptools import setup, find_packages

setup(
    name='virtual_steering_wheel',
    version='0.0.1',
    author='bell',
    author_email='bell@bell',
    description='Implementation of virtual Steering Wheel',
    packages=[
        "virtual_steering_wheel",
        "virtual_steering_wheel.joystick"
        ],    
    install_requires=[
        'libevdev>=0.11',
        'pyserial>=3.5',
        'vgamepad>=0.1.0',
        'PyAutoGUI>=0.9.54', 
    ],
)
