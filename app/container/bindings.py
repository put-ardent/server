from app.container.container import Container
from app.http.request_handler import AbstractRequestHandler, RequestHandler, InternalRequestHandler
from http.server import HTTPServer


def apply(container: Container) -> None:
    AbstractRequestHandler.LEAGUE_CONNECTION = container.get('app.struct.connection.LeagueConnection')
    AbstractRequestHandler.MOBILE_CONNECTION = container.get('app.struct.connection.MobileConnection')

    server = HTTPServer(('0.0.0.0', 2137), RequestHandler)
    internal_server = HTTPServer(('0.0.0.0', 2138), InternalRequestHandler)

    container.bind('app.container.Container.Container', container)
    container.bind('http-server', server)
    container.bind('internal-http-server', internal_server)
