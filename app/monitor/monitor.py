import chalk
from time import sleep
import sys

from app.struct.league_connection import LeagueConnection


class Monitor:
    def __init__(self, league_connection: LeagueConnection):
        self._league_connection = league_connection
        self._shutdown = False

    def run(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        print()

        while not self._shutdown:
            if self._league_connection.open:
                print(f"{chalk.green('v')} League Client is open.         ", end='\r')
            else:
                print(f"{chalk.blue('o')} Waiting for league client.      ", end='\r')
            sleep(.5)

        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def shutdown(self) -> None:
        self._shutdown = True
