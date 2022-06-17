from http.server import HTTPServer
from app.container.container import Container
from app.connector.connectors import LeagueConnector, MobileConnector
from app.container import bindings
from threading import Thread
from app.monitor.monitor import Monitor
from time import sleep
from app.wss.websockets_handler import WebsocketHandler


if __name__ == '__main__':
    container = Container()
    bindings.apply(container)

    league_connector: LeagueConnector = container.get('app.connector.connectors.LeagueConnector')
    mobile_connector: MobileConnector = container.get('app.connector.connectors.MobileConnector')
    http_server: HTTPServer = container.get('http-server')
    internal_http_server: HTTPServer = container.get('internal-http-server')
    monitor: Monitor = container.get('app.monitor.monitor.Monitor')
    websockets: WebsocketHandler = container.get('app.wss.websockets_handler.WebsocketHandler')

    threads = {
        'league_connector': Thread(target=league_connector.run),
        'mobile_connector': Thread(target=mobile_connector.run),
        'http': Thread(target=http_server.serve_forever),
        'internal-http': Thread(target=internal_http_server.serve_forever),
        'monitor': Thread(target=monitor.run),
        'wss': Thread(target=websockets.run)
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
        internal_http_server.shutdown()
        monitor.shutdown()
