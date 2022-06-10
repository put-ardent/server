from http.server import BaseHTTPRequestHandler
from json import dumps, loads
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth
from app.struct.connection import LeagueConnection, MobileConnection


class RequestHandler(BaseHTTPRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    CONNECTION: Optional[LeagueConnection] = None

    def __init__(self, *args, **kwargs):
        for method in self.SUPPORTED_METHODS:
            setattr(self, 'do_' + method, self.do)

        super().__init__(*args, **kwargs)

    def do(self) -> None:
        if not self.CONNECTION.open:
            self._response(502, {'error': 'LCU connection is not yet open.'})
            return

        response = self._pass_request()

        self._response(response.status_code, response.json())

    def _pass_request(self) -> requests.Response:
        data = self._get_body()
        response = requests.request(
            self.command,
            f'https://127.0.0.1:{self.CONNECTION.port}{self.path}',
            json=data,
            auth=HTTPBasicAuth('riot', self.CONNECTION.password),
            verify='./riotgames.pem'
        )

        if response.status_code > 299:
            print(response.json())

        return response

    def _get_body(self) -> Optional[dict]:
        if 'Content-Length' not in self.headers:
            return None

        content_length = int(self.headers['Content-Length'])
        
        return loads(self.rfile.read(content_length).decode())

    def _response(self, status_code: int, body: dict):
        self.send_response(status_code)
        self.end_headers()
        self.wfile.write(dumps(body).encode())

    def log_message(self, format, *args):
        return


class InternalResponse:
    def __init__(self, body: Optional[dict], status_code: int = 200):
        self.body = body
        self.status_code = status_code


class InternalRequestHandler(BaseHTTPRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    LEAGUE_CONNECTION: Optional[LeagueConnection] = None
    MOBILE_CONNECTION: Optional[MobileConnection] = None

    def __init__(self, *args, **kwargs):
        for method in self.SUPPORTED_METHODS:
            setattr(self, 'do_' + method, self.do)

        super().__init__(*args, **kwargs)

    def do(self) -> None:
        response = self._handle_request()

        self._respond(response)

    def _handle_request(self) -> InternalResponse:
        data = self._get_body()

        if self.command == 'POST' and self.path == '/connection':
            self.MOBILE_CONNECTION.open = True
            self.MOBILE_CONNECTION.host = data['host']
            self.MOBILE_CONNECTION.port = 6969

            return InternalResponse(None, 204)

        return InternalResponse({'error': 'Method and route combination not found.'}, 404)

    def _get_body(self) -> Optional[dict]:
        if 'Content-Length' not in self.headers:
            return None

        content_length = int(self.headers['Content-Length'])

        return loads(self.rfile.read(content_length).decode())

    def _respond(self, response: InternalResponse):
        self.send_response(response.status_code)
        self.end_headers()
        self.wfile.write(dumps(response.body).encode())

    def log_message(self, format, *args):
        return
