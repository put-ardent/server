from http.server import HTTPServer
from app.container.container import Container
from app.connector.connectors import LeagueConnector
from app.container import bindings
from threading import Thread
from app.monitor.monitor import Monitor
from time import sleep


if __name__ == '__main__':
    print('Initializing app')

    container = Container()
    bindings.apply(container)

    league_connector: LeagueConnector = container.get('app.connector.connectors.LeagueConnector')
    http_server: HTTPServer = container.get('http-server')
    monitor: Monitor = container.get('app.monitor.monitor.Monitor')

    threads = {
        'league_connector': Thread(target=league_connector.run),
        'http': Thread(target=http_server.serve_forever),
        'monitor': Thread(target=monitor.run),
    }

    try:
        for thread in threads.values():
            thread.start()

        while True:
            sleep(100)
    except BaseException:
        http_server.shutdown()
        league_connector.shutdown()
        monitor.shutdown()
