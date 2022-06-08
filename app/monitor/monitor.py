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
        print('\n')

        while not self._shutdown:
            spinner_char = self.SPINNER_SEQUENCE[self._sequence_index]

            if self._league_connection.open:
                print(f"\033[F{chalk.green('v')} League Client is open.         ", end='\n')
                print(f"{chalk.green('v')} League Client is open.         ", end='\r')
            else:
                print(f"\033[F{chalk.blue(spinner_char)} Waiting for league client.      ", end='\n')
                print(f"{chalk.blue(spinner_char)} Waiting for league client.         ", end='\r')

            self._iterate_sequence_index()
            sleep(.15)

        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def shutdown(self) -> None:
        self._shutdown = True

    def _iterate_sequence_index(self):
        self._sequence_index += 1
        if self._sequence_index == 6:
            self._sequence_index = 0
