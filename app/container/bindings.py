from app.container.container import Container
from app.http.request_handler import RequestHandler, InternalRequestHandler
from http.server import HTTPServer


def apply(container: Container) -> None:
    server = HTTPServer(('0.0.0.0', 2137), RequestHandler)
    RequestHandler.CONNECTION = container.get('app.struct.connection.LeagueConnection')

    internal_server = HTTPServer(('0.0.0.0', 2138), InternalRequestHandler)
    InternalRequestHandler.LEAGUE_CONNECTION = container.get('app.struct.connection.LeagueConnection')
    InternalRequestHandler.MOBILE_CONNECTION = container.get('app.struct.connection.MobileConnection')

    container.bind('app.container.Container.Container', container)
    container.bind('http-server', server)
    container.bind('internal-http-server', internal_server)
