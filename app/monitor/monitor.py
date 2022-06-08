import chalk
from time import sleep
import sys

from app.struct.league_connection import LeagueConnection


class Monitor:
    SPINNER_SEQUENCE = ('⠏', '⠛', '⠹', '⠼', '⠶', '⠧')

    def __init__(self, league_connection: LeagueConnection):
        self._league_connection = league_connection
        self._shutdown = False
        self._sequence_index = 0

    def run(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        print()

        while not self._shutdown:
            spinner_char = self.SPINNER_SEQUENCE[self._sequence_index]

            status_ok = chalk.green('✔')
            status_pending = chalk.blue(spinner_char)

            league_line = (status_ok + ' ' + chalk.white('League Client is open.')) if self._league_connection.open \
                else (status_pending + ' ' + chalk.white('Waiting for league client.'))
            league_line = league_line.ljust(50)

            mobile_line = (status_pending + ' ' + chalk.white('Waiting for mobile app.'))

            print(f"\033[F{ league_line }", end='\n')
            print(f"{ mobile_line }", end='\r')

            self._iterate_sequence_index()
            sleep(.15)

        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        print()

    def shutdown(self) -> None:
        self._shutdown = True

    def _iterate_sequence_index(self):
        self._sequence_index += 1
        if self._sequence_index == 6:
            self._sequence_index = 0
