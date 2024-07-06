# fsr-install
Windows/Linux/MacOS Installer for teejusb webui

### About
This will install the webui for teejusb dance pad firmware, with no need to install python or nodejs beforehand. Simply execute and it will do the rest.
During installation it will automatically detect which serial port (`COM#`) your teejusb is connected to and configure the server for it.
NOTE: if your device is not flashed correctly or you need to reflash, etc. you can simply run `install.bat` again and it will update the configuration.

The actual teejusb firmware can be found here https://github.com/teejusb/fsr/

SQUAWK SQUAWK

### Notes
- As I get feedback I will introduce new features such as interactive install if you want to skip the autoconfigure, etc.
- Known Issues:
  - using --port does not currently work. you only need this if you want to run 2 pads together (coming)
This is the initial version, so there may be some bugs! let me know if there are.


### Installation
1) Download and Extract this repository to where you want to install it
2) Connect a device flashed with teejusb firmware
   NOTE: not required, but it cannot automatically configure the server for your unique serial port and sensor count during installation if it is not connected.
2) Run the appropraite install script from a terminal (so if it fails you can give me output :)
   Windows: install.bat
   Linux: ./install.sh
   MacOS: ./install.sh

### Example
```
.\install.bat
Checking system architecture...
Found architecture: x64                                                                                                 
Setting variables based on architecture...                                                                              
Calculating MD5 checksums...                                                                                            
Checking MD5 checksums...                                                                                               
Creating directories...                                                                                                 
Installing Python...
Installing NodeJS...
Collecting pip
  Using cached pip-24.1.1-py3-none-any.whl.metadata (3.6 kB)
Collecting setuptools
  Using cached setuptools-70.2.0-py3-none-any.whl.metadata (5.8 kB)
<---- TRUNCATED ---->
Installing collected packages: pywin32, urllib3, pyshortcuts, psutil, charset-normalizer, certifi, requests
Successfully installed certifi-2024.7.4 charset-normalizer-3.3.2 psutil-6.0.0 pyshortcuts-1.9.0 pywin32-306 requests-2.32.3 urllib3-2.2.2
        1 file(s) copied.

C:\squawk-fsr-install>echo finished installer initialization, executing installer
finished installer initialization, executing installer

C:\squawk-fsr-install>python\python.exe webui.py --install --arch x64
No conda env active, defaulting to base
2024-07-06 06:24:32,961 INFO install: starting webui install for x64 cpu
2024-07-06 06:24:32,962 INFO scan_serial: scanning all serial ports...
2024-07-06 06:24:32,970 INFO list_serial_ports: found 1 serial port(s)
2024-07-06 06:24:33,977 INFO is_teejusb: found teejusb device on COM5 with 4 sensors
2024-07-06 06:24:33,980 INFO scan_serial: found teejusb serial device on: COM5
2024-07-06 06:24:33,983 INFO patch_serial_port: updating serial port in server.py
2024-07-06 06:24:33,986 INFO patch_serial_port: successfully patched serial COM5 with 4 sensors
2024-07-06 06:24:33,995 INFO install: installing nodejs packages...
2024-07-06 06:24:33,995 INFO npm_install: installing npm package: -g yarn
2024-07-06 06:24:38,421 INFO install: installing webui...
2024-07-06 06:24:40,032 INFO install: building (this may take a few minutes)...
2024-07-06 06:24:51,529 INFO wrapper: bringing up test webui server...
2024-07-06 06:24:53,116 INFO wrapper: test webui is accessible
2024-07-06 06:24:53,120 INFO test_webui: all webui tests passed
2024-07-06 06:24:53,120 INFO install: squawk squawk - all done
```

### To Run
To run the webui after installation, a shortcut will be placed in the installation directory.
Optionally you can run it from the installation directory (windows) with `python\python.exe webui.py --run`
```
PS C:\squawk-fsr-install> .\python\python.exe .\webui.py -r
No conda env active, defaulting to base
2024-07-06 06:27:01,268 INFO main: starting server on http://localhost:5000
2024-07-06 06:27:01,269 INFO wrapper: bringing up test webui server...
2024-07-06 06:27:02,360 INFO wrapper: test webui is accessible
2024-07-06 06:27:02,365 INFO test_webui: all webui tests passed
2024-07-06 06:27:02,365 INFO main: server running on http://localhost:5000
2024-07-06 06:27:02,366 INFO main: use your browser to navigate to the server, and press CTRL+C to stop it
```
