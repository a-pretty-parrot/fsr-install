import urllib.request
import subprocess, os
import sys, serial, psutil, re, logging
import serial.tools.list_ports
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger('__squawker__')


def scan_serial():
    logger.info('scanning all serial ports...')
    ports = list_serial_ports()

    # check which serial ''ports'' are currently in use
    device = None
    for port in ports:
        status = is_port_in_use(port.device)
        if status == True:
           logger.warning('cant scan %s because port is in use' % port.device)
        else:
           device, sensors = is_teejusb(port.device)
           if device != None: break

    if device == None:
       logger.error('failed to find teejusb device!')
       return False
       raise SystemError('no teejusb device detected')

    logger.info('found teejusb serial device on: %s' % device)
    if patch_serial_port('fsr/webui/server/server.py', 'COM5', sensors):
       return True
    else:
       return False



def patch_serial_port(file_path, new_port, sensor_count):
    """
    Patch the SERIAL_PORT value in the specified file.

    Parameters:
    file_path (str): The path to the file to be patched.
    new_port (str): The new serial port value to set.

    Returns:
    None
    """
    logger.info('updating serial port in server.py')
    try:
        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Open the file for writing
        sensor_success = False
        serial_success = False
        with open(file_path, 'w') as file:
            for line in lines:
                # Replace the SERIAL_PORT line
                if re.match(r'^SERIAL_PORT = .*', line):
                    file.write(f'SERIAL_PORT = "{new_port}"\n')
                    serial_success = True
                elif re.match(r'^num_sensors = \d+', line):
                    file.write(f'num_sensors = {sensor_count}\n')
                    sensor_success = True
                else:
                    file.write(line)
    except Exception as e:
        logger.error(f"an error occurred while patching the file: {e}")

    if sensor_success and serial_success:
        logger.info(f"successfully patched serial {new_port} with {sensor_count} sensors")
        return True
    else:
        logger.error('failed to patch!')
        logger.debug('sensor success: %s' % sensor_success)
        logger.debug('device success: %s' % serial_success)
        return False



@contextmanager
def serial_port(port, baudrate=115200, timeout=1):
    """
    Context manager for opening and closing a serial port.

    Parameters:
    port (str): The COM/serial port to open (e.g., 'COM3', '/dev/ttyUSB0').
    baudrate (int): The baud rate for the serial port.
    timeout (int): The timeout for serial operations in seconds.

    Yields:
    Serial: The opened serial port object.
    """
    ser = None
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        logger.debug(f"opened serial port {port}")
        yield ser
    except serial.SerialException as e:
        logger.error(f"error opening serial port {port}: {e}")
        raise e
    finally:
        if ser and ser.is_open:
            ser.close()
            logger.debug(f"closed serial port {port}")



def send_command(ser, command):
    """
    Send a command to the serial port and return the response.

    Parameters:
    ser (Serial): The opened serial port object.
    command (str): The command to send to the serial port.

    Returns:
    str: The response from the serial port.
    """
    try:
        ser.write(command.encode())
        response = ser.readline().decode('utf-8').strip()
        logger.debug(f"Received response: {response}")
        return response
    except serial.SerialException as e:
        logger.error(f"Error sending command: {e}")
        return ""



def is_teejusb(port):
    """
    Automatically detect which serial device is the one we want by sending "v" and checking the response.

    Returns:
    str: The correct COM/serial port if found, None otherwise.
    """
    try:
        with serial_port(port) as ser:
            response = send_command(ser, 'v')
            match = re.match(r'^v\s(\d+(\s\d+)*)$', response)
            if match:
                sensor_count = len(match.group(1).split())
                logger.info(f"found teejusb device on {port} with {sensor_count} sensors")
                return port, sensor_count
    except Exception as e:
        logger.warning(f"error with port {port}: {e}")
        return None, None



def list_serial_ports():
    """
    List all available COM/serial ports on the system.

    This function works on both Windows and Linux.

    Returns:
    list: A list of strings representing the available COM/serial ports.
    """
    ports = serial.tools.list_ports.comports()
    logger.info('found %s serial port(s)' % len(ports))
    return ports

def is_port_in_use(port):
    """
    Check if a specified COM/serial port is in use.

    Parameters:
    port (str): The COM/serial port to check (e.g., 'COM3', '/dev/ttyUSB0').

    Returns:
    bool: True if the port is in use, False otherwise.
    """
    try:
        ser = serial.Serial(port)
        ser.close()
        return False
    except (serial.SerialException, OSError):
        return True
























def debug_print_env():
    print("Current PATH:", os.environ.get("PATH"))
    print("Current PYTHONPATH:", os.environ.get("PYTHONPATH"))
    print("sys.executable:", sys.executable)
    scripts_dir = os.path.join(os.path.dirname(sys.executable), 'Scripts')
    print("Scripts directory:", scripts_dir)
    pip_executable = os.path.join(scripts_dir, 'pip.exe')
    print("pip executable path:", pip_executable)

def install_pip():
    """
    download and install python pip
    """
    print("Downloading get-pip.py...")
    url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_script = "get-pip.py"
    urllib.request.urlretrieve(url, get_pip_script)
    print("Downloaded get-pip.py")

    # run get-pip.py using the current python interpreter
    print("Installing pip...")
    try:
        result = subprocess.run([sys.executable, get_pip_script], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        print("pip installation script completed")
    finally:
        # clean up by removing get-pip.py script
        os.remove(get_pip_script)
        print("Removed get-pip.py")

    # Add the Scripts directory to the PATH
    scripts_dir = os.path.join(os.path.dirname(sys.executable), 'Scripts')
    os.environ["PATH"] += os.pathsep + scripts_dir
    os.environ["PYTHONPATH"] = scripts_dir
    print("Updated PATH and PYTHONPATH")
    debug_print_env()

def verify_pip():
    print("Verifying pip installation...")
    scripts_dir = os.path.join(os.path.dirname(sys.executable), 'Scripts')
    pip_executable = os.path.join(scripts_dir, 'pip.exe')
    try:
        result = subprocess.run([pip_executable, "--version"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        if result.returncode == 0:
            print("pip is installed successfully.")
        else:
            print("pip installation failed.")
            sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print("pip installation failed.")
        sys.exit(e.returncode)

def pip_install(package_name):
    print(f"Installing package: {package_name}")
    # Get the path to the pip executable directly
    pip_executable = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pip.exe')
    print("Using pip executable at:", pip_executable)

    # Install the specified package using pip
    result = subprocess.run([pip_executable, "install", package_name], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        print(f"Failed to install {package_name}. Return code: {result.returncode}")
        sys.exit(result.returncode)
    else:
        print(f"Successfully installed {package_name}")

'''
if __name__ == '__main__':
    print("Starting installation process...")
    debug_print_env()
    install_pip()
    verify_pip()
    pip_install('requests')
    try:
        import requests
        print('Successfully imported requests')
    except ImportError:
        print('Failed to import requests')
'''



if __name__ == '__main__':
   pass
