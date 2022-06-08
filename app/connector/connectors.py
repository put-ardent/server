import subprocess
from time import sleep
from app.struct.league_connection import LeagueConnection


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
