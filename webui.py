import logging
from pathlib import Path
import os, time, sys, argparse, subprocess
import requests, winshell
from functools import wraps
from pyshortcuts import make_shortcut
import threading
import signal
import psutil

from squawklib import scan_serial

# move to directory where the script is for relative paths to work
os.chdir(Path(__file__).parent.resolve())

# set up logging
log = logging.getLogger('__squawker__')
log.setLevel(logging.INFO)

# create handlers
file_handler = logging.FileHandler('./install.log')
stream_handler = logging.StreamHandler()

# set the logging level for handlers
file_handler.setLevel(logging.INFO)
stream_handler.setLevel(logging.INFO)

# create a formatter and set it for handlers
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s: %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# add handlers to the logger
log.addHandler(file_handler)
log.addHandler(stream_handler)

stop_event = threading.Event()
server_process = None
PIDS = []

def server_control(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global server_process

        server = 'localhost'
        port = kwargs.get('port', 5000)
        _socket = f'{server}:{port}'

        log.info('bringing up test webui server...')

        # set up node path to ensure yarn is recognized
        setup_node_path()

        # start the test server
        server_process = subprocess.Popen(
            "yarn start-api",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        PIDS.append(server_process.pid)

        # wait up to 30 seconds for the server to start
        for _ in range(60):
            try:
                response = requests.get(f'http://{_socket}')
                if response.status_code == 200:
                    log.info('test webui is accessible')
                    break
            except requests.ConnectionError:
                if stop_event.is_set():
                    break
                time.sleep(0.5)
        else:
            server_process.terminate()
            raise RuntimeError("server did not start within 30 seconds.")

        try:
            # run the test function
            result = func(*args, **kwargs)
        finally:
            pass

        return result
    return wrapper

def finish():
    """
    Shuts down the server and kills all processes in PIDS.
    """
    global PIDS

    log.info('shutting down all processes')
    stop_event.set()

    for pid in PIDS:
        try:
            process = psutil.Process(pid)
            for child in process.children(recursive=True):
                log.info(f'killing child process {child.pid}')
                child.kill()
            log.info(f'killing process {pid}')
            process.kill()
        except psutil.NoSuchProcess:
            log.info(f'process {pid} already terminated')

    log.info('all processes stopped, exiting')
    sys.exit(0)

def signal_handler(sig, frame):
    log.info(f'received signal {sig}, shutting down')
    finish()

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

@server_control
def test_webui(port=5000):
    server = 'localhost'
    _socket = f'{server}:{port}'

    try:
        response = requests.get(f'http://{_socket}/')
    except Exception as e:
        log.error(f"didn't get expected response from server! {e}")
        raise Exception('server test failed!')

    if response.status_code == 200:
       log.debug('received HTTP-200/OK from webui')
    else:
       log.error(f'received {response.status_code} from {_socket} instead of HTTP-200/OK!')
       raise ValueError('received unexpected status code from webui')

    expected_str = r'You need to enable JavaScript to run this app.'
    log.debug('checking for string in response: %s' % expected_str)
    if expected_str in response.text:
       log.debug('found expected string in response')
    else:
       log.error(f'failed to find expected string in webui ({_socket}) response!')
       raise ValueError('received unexpected status code from webui')

    log.info('all webui tests passed')
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Installer to install teejusb fsr webui",
        epilog="Author: a pretty parrot\n\n"
               "Examples:\n"
               "  Install the webui for x64 architecture:\n"
               "    python webui.py --install --arch x64\n\n"
               "  Run the server on the default port (5000):\n"
               "    python webui.py --run\n\n"
               "  Run the server on a specific port (e.g., 8080):\n"
               "    python webui.py --run --port 8080\n",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '-a', '--arch',
        choices=['x64', 'x86'],
        required=False,
        help='your processor architecture (x86/x64)'
    )

    parser.add_argument(
        '-r', '--run',
        action='store_true',
        help='run the server'
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        default=5000,
        help='the port to run the server on (default: 5000)'
    )

    parser.add_argument(
        '-i', '--install',
        action='store_true',
        help='install the webui'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='set log level to DEBUG'
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    log.setLevel(log_level)

    if args.run and args.arch:
        log.error("you cannot use --arch with --run")
        sys.exit(1)

    if args.install and not args.arch:
        args.arch = auto_detect_arch()
        log.info(f"auto-detected architecture: {args.arch}")

    if args.install:
        install(args.arch)

    if args.run:
        os.chdir(Path('fsr/webui').resolve())
        setup_node_path()
        try:
            log.info(f"starting server on http://localhost:{args.port}")
            test_webui(port=args.port)
            log.info(f"server running on http://localhost:{args.port}")
            log.info("use your browser to navigate to the server, and press CTRL+C to stop it")
            signal.signal(signal.SIGINT, lambda sig, frame: finish())
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("received CTRL+C, stopping the server")
            finish()

def install(arch):
    log.info(f'starting webui install for {arch} cpu')

    if not scan_serial():
       log.warning('''failed to automatically detect teejusb device!
this will happen if you have not properly flashed it yet, or it is not connected.
you will have to manually update fsr/server/server.py with your serial device and sensor count.
otherwise you can rerun the installer with the flashed device connected and it will update it.''')

    os.chdir(Path('fsr/webui').resolve())
    log.debug(f'current directory: {os.getcwd()}')

    setup_node_path()

    try: remove_package_lock_and_node_modules()
    except: pass

    log.info('installing nodejs packages...')
    node_packages = [ '-g yarn', ]
    for package in node_packages:
        npm_install(package)

    log.info('installing webui...')
    run_shell_command('yarn install')
    log.info('building (this may take a few minutes)...')
    run_shell_command('yarn build')

    test_webui()

    log.info('squawk squawk - all done')
    create_shortcut()
    finish()
    sys.exit(0)

def update_package_json():
    with open('package.json', 'r') as file:
        data = json.load(file)

    if 'devDependencies' not in data:
        data['devDependencies'] = {}

    data['devDependencies']['@types/node'] = '^18.7.23'

    with open('package.json', 'w') as file:
        json.dump(data, file, indent=2)

    print("Updated package.json with @types/node")

def remove_package_lock_and_node_modules():
    if os.path.exists('package-lock.json'):
        os.remove('package-lock.json')
        print("Removed package-lock.json")

    if os.path.exists('node_modules'):
        subprocess.run(['rm', '-rf', 'node_modules'])
        print("Removed node_modules")

def auto_detect_arch():
    if sys.maxsize > 2**32:
        return 'x64'
    else:
        return 'x86'

def npm_install(package):
    log.info('installing npm package: %s' % package)
    command = f'npm install {package} --verbose'
    rc, _ = run_shell_command(command)
    log.debug(_)

    if rc != 0:
        log.error('failed to install package (%s)!' % package)
        raise SystemError('failed to install npm package: %s\nOutput: %s' % (package, _))
    return True

def run_shell_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    PIDS.append(process.pid)
    stdout, stderr = [], []

    while True:
        output = process.stdout.readline()
        if output:
            stdout.append(output.strip())
        err = process.stderr.readline()
        if err:
            stderr.append(err.strip())

        if output == '' and err == '' and process.poll() is not None:
            break

    rc = process.poll()
    if rc != 0:
        full_stderr = "\n".join(stderr)
        log.error(f'command ({command}) failed with RC={rc}\n{full_stderr}')
        raise SystemError(f'command ({command}) failed with RC={rc}\n{full_stderr}')
    return rc, "\n".join(stdout)

def setup_node_path():
    nodejs_path = Path("../../nodejs/node-v16.20.2-win-x64").resolve()
    os.environ['PATH'] = f"{nodejs_path}{os.pathsep}{nodejs_path / 'node_modules' / 'npm' / 'bin'}{os.pathsep}{os.environ['PATH']}"
    os.environ['PATH'] = f"{Path(os.getcwd()) / 'node_modules' / '.bin'}{os.pathsep}{os.environ['PATH']}"


def create_shortcut():
    def get_user_input():
        while True:
            user_input = input("Do you want to continue? (y/yes/n/no): ").strip().lower()
            if user_input in ['y', 'yes']:
                return True
            elif user_input in ['n', 'no']:
                print("Exiting the program.")
                exit()
            else:
                log.error("invalid input. please enter y/yes or n/no.")
    
    log.info('do you want to create a desktop shortcut to run the webui? (y/n):')
    if get_user_input():
        log.info('creating shortcut...')
    else:
        pass

# define all the paths needed for the .bat file
os.chdir(Path(__file__).parent.resolve())
desktop = Path(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'))
pwd = Path.cwd()
python_fp = pwd / 'python' / 'python.exe'
batch_filepath = str(desktop / "fsr_webui.bat")

# build up the command to run the Python script
command = f'"{python_fp}" "{pwd / "webui.py"}" --run'

# create the .bat file on the desktop
try:
    with open(batch_filepath, 'w') as batch_file:
        batch_file.write(f'@echo off\n')
        batch_file.write(f'cd /d "{pwd}"\n')
        batch_file.write(command + '\n')
        batch_file.write('pause\n')
    print('Batch file created!')
    return True
except Exception as e:
    print(f'Failed to create batch file!\n{e}')
    return False

if __name__ == "__main__":
    main()

