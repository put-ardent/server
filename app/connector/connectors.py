import subprocess
from time import sleep
from app.struct.connection import LeagueConnection, MobileConnection
import socket
from contextlib import closing
from json import dumps


class Connector:
    def __init__(self):
        self._connected: bool = False

    def get_state(self) -> bool:
        return self._connected


class LeagueConnector(Connector):
    def __init__(self, connection: LeagueConnection):
        super().__init__()
        self._connection = connection
        self._shutdown = False

    def run(self) -> None:
        while not self._shutdown:
            if self._connected:
                self._confirm_connection()
            else:
                self._connect()

            sleep(2)

    def shutdown(self) -> None:
        self._shutdown = True

    def _connect(self) -> None:
        with subprocess.Popen('ps -x | grep LeagueClientUx', shell=True, stdout=subprocess.PIPE).stdout as processes:
            client_process = processes.readline().decode('utf-8')

        if not client_process or client_process.split()[-2] == 'grep':
            return

        raw_flags = client_process.split(' --')[1::]
        flags = {}
        for raw_flag in raw_flags:
            flag = raw_flag.split('=')

            if len(flag) == 2:
                flags[flag[0]] = flag[1]
            else:
                flags[flag[0]] = None

        self._connection.open = True
        self._connection.port = int(flags['app-port'])
        self._connection.password = flags['remoting-auth-token']

        self._connected = True

    def _confirm_connection(self) -> None:
        with subprocess.Popen('ps -x | grep LeagueClientUx', shell=True, stdout=subprocess.PIPE).stdout as processes:
            client_process = processes.readline().decode('utf-8')

        if not client_process or client_process.split()[-2] == 'grep':
            self._connection.open = False
            self._connection.port = None
            self._connection.password = None

            self._connected = False


class MobileConnector(Connector):
    def __init__(self, connection: MobileConnection):
        super().__init__()
        self._connection = connection
        self._shutdown = False

    def run(self) -> None:
        while not self._shutdown:
            if self._connection.open:
                self._send(self._connection.host, self._connection.port)
            else:
                self._broadcast_self()

            sleep(1)

    def shutdown(self) -> None:
        self._shutdown = True

    def _broadcast_self(self) -> None:
        me = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if ip != '127.0.0.1'][0]
        network = '.'.join(me.split('.')[:-1])
        addresses = [me]
        with subprocess.Popen(f'arp -a | grep {network}', shell=True, stdout=subprocess.PIPE).stdout as arp:
            for line in arp.readlines():
                line = line.decode('utf-8')
                address = line.split('(')[1].split(')')[0]
                if address.split('.')[-1] == '255':
                    continue

                addresses.append(address)

        for address in set(addresses):
            self._start_socket(address, 6969)

    def _start_socket(self, host, port) -> None:
        me = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if ip != '127.0.0.1'][0]
        data = {'type': 'connection', 'address': me}
        self._send(host, port, dumps(data).encode())

    def _send(self, host, port, message=b'{"type":"keep-alive"}') -> None:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
            sock.sendto(message, (host, port))
