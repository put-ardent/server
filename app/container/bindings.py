from app.container.container import Container
from app.http.request_handler import RequestHandler
from http.server import HTTPServer


def apply(container: Container) -> None:
    server = HTTPServer(('0.0.0.0', 2137), RequestHandler)
    RequestHandler.CONNECTION = container.get('app.struct.league_connection.LeagueConnection')

    container.bind('app.container.Container.Container', container)
    container.bind('http-server', server)