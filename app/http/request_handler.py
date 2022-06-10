from http.server import BaseHTTPRequestHandler
from json import dumps, loads
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth
from app.struct.connection import LeagueConnection, MobileConnection


class InternalResponse:
    def __init__(self, body: Optional[dict], status_code: int = 200):
        self.body = body
        self.status_code = status_code


class AbstractRequestHandler(BaseHTTPRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def _get_body(self) -> Optional[dict]:
        if 'Content-Length' not in self.headers:
            return None

        content_length = int(self.headers['Content-Length'])

        return loads(self.rfile.read(content_length).decode())

    def _respond(self, response: InternalResponse) -> None:
        self.send_response(response.status_code)
        self.end_headers()
        self.wfile.write(dumps(response.body).encode())

    def log_message(self, format, *args) -> None:
        return

    def _league_request(self, method: str, path: str, data: Optional[dict] = None) -> requests.Response:
        return requests.request(
            method,
            f'https://127.0.0.1:{RequestHandler.CONNECTION.port}{path}',
            json=data,
            auth=HTTPBasicAuth('riot', RequestHandler.CONNECTION.password),
            verify='./riotgames.pem'
        )


class RequestHandler(AbstractRequestHandler):
    CONNECTION: Optional[LeagueConnection] = None

    def __init__(self, *args, **kwargs):
        for method in self.SUPPORTED_METHODS:
            setattr(self, 'do_' + method, self.do)

        super().__init__(*args, **kwargs)

    def do(self) -> None:
        if not self.CONNECTION.open:
            self._respond(InternalResponse({'error': 'LCU connection is not yet open.'}, 502))
            return

        self._respond(self._pass_request())

    def _pass_request(self) -> InternalResponse:
        data = self._get_body()
        response = self._league_request(self.command, self.path, data)

        if response.status_code > 299:
            print(response.json())

        return InternalResponse(response.json(), response.status_code)


class InternalRequestHandler(AbstractRequestHandler):
    LEAGUE_CONNECTION: Optional[LeagueConnection] = None
    MOBILE_CONNECTION: Optional[MobileConnection] = None

    def __init__(self, *args, **kwargs):
        for method in self.SUPPORTED_METHODS:
            setattr(self, 'do_' + method, self.do)

        super().__init__(*args, **kwargs)

    def do(self) -> None:
        self._respond(self._handle_request())

    def _handle_request(self) -> InternalResponse:
        data = self._get_body()

        if self.command == 'POST' and self.path == '/connection':
            self.MOBILE_CONNECTION.open = True
            self.MOBILE_CONNECTION.host = data['host']
            self.MOBILE_CONNECTION.port = 6969

            return InternalResponse(None, 204)

        if self.command == 'GET' and self.path == '/active-queues':
            queues_response = self._league_request('get', '/lol-game-queues/v1/queues')
            queues = [queue for queue in queues_response.json() if queue['queueAvailability'] == 'Available']

            return InternalResponse({'data': queues}, 200)

        return InternalResponse({'error': 'Method and route combination not found.'}, 404)
