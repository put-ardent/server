from http.server import HTTPServer
from app.container.container import Container
from app.connector.connectors import LeagueConnector, MobileConnector
from app.container import bindings
from threading import Thread
from app.monitor.monitor import Monitor
from time import sleep


if __name__ == '__main__':
    container = Container()
    bindings.apply(container)

    league_connector: LeagueConnector = container.get('app.connector.connectors.LeagueConnector')
    mobile_connector: MobileConnector = container.get('app.connector.connectors.MobileConnector')
    http_server: HTTPServer = container.get('http-server')
    monitor: Monitor = container.get('app.monitor.monitor.Monitor')

    threads = {
        'league_connector': Thread(target=league_connector.run),
        'mobile_connector': Thread(target=mobile_connector.run),
        'http': Thread(target=http_server.serve_forever),
        'monitor': Thread(target=monitor.run),
    }

    try:
        for thread in threads.values():
            thread.start()

        while True:
            sleep(100)
    except BaseException:
        league_connector.shutdown()
        mobile_connector.shutdown()
        http_server.shutdown()
        monitor.shutdown()
