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

    LEAGUE_CONNECTION: Optional[LeagueConnection] = None
    MOBILE_CONNECTION: Optional[MobileConnection] = None

    def _get_body(self) -> Optional[dict]:
        if 'Content-Length' not in self.headers:
            return None

        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length).decode()

        return loads(content) if content else None

    def _respond(self, response: InternalResponse) -> None:
        self.send_response(response.status_code)
        self.end_headers()
        self.wfile.write(dumps(response.body).encode())

    def log_message(self, format, *args) -> None:
        return

    @staticmethod
    def league_request(method: str, path: str, data: Optional[dict] = None) -> requests.Response:
        return requests.request(
            method,
            f'https://127.0.0.1:{AbstractRequestHandler.LEAGUE_CONNECTION.port}{path}',
            json=data,
            auth=HTTPBasicAuth('riot', AbstractRequestHandler.LEAGUE_CONNECTION.password),
            verify='./riotgames.pem'
        )

    def validate_league_connection(self):
        if not self.LEAGUE_CONNECTION.open:
            self._respond(InternalResponse({'error': 'LCU connection is not yet open.'}, 502))
            return False

        return True


class RequestHandler(AbstractRequestHandler):
    def __init__(self, *args, **kwargs):
        for method in self.SUPPORTED_METHODS:
            setattr(self, 'do_' + method, self.do)

        super().__init__(*args, **kwargs)

    def do(self) -> None:
        if not self.validate_league_connection():
            return

        self._respond(self._pass_request())

    def _pass_request(self) -> InternalResponse:
        data = self._get_body()
        response = self.league_request(self.command, self.path, data)

        if response.status_code > 299:
            print(response.json())

        body = {} if int(response.headers.get('Content-Length')) == 0 else response.json()

        return InternalResponse(body, response.status_code)


class InternalRequestHandler(AbstractRequestHandler):
    def __init__(self, *args, **kwargs):
        for method in self.SUPPORTED_METHODS:
            setattr(self, 'do_' + method, self.do)

        super().__init__(*args, **kwargs)

    def do(self) -> None:
        response = self._handle_request()
        if response:
            self._respond(response)

    def _handle_request(self) -> Optional[InternalResponse]:
        data = self._get_body()

        if self.command == 'POST' and self.path == '/connection':
            self.MOBILE_CONNECTION.open = True
            self.MOBILE_CONNECTION.host = self.headers.get('Host').split(':')[0]
            self.MOBILE_CONNECTION.port = data['port']

            return InternalResponse(None, 204)

        if self.command == 'GET' and self.path == '/queues':
            if not self.validate_league_connection():
                return

            queues_response = self.league_request('get', '/lol-game-queues/v1/queues')
            raw_queues = [
                queue for queue in queues_response.json()
                if queue['queueAvailability'] == 'Available'
                   and queue['gameMode'] != 'TFT'
                   and 1 in queue['allowablePremadeSizes']
                   and queue['category'] == 'PvP'
            ]

            queues = {'ranked': [], 'unranked': [], 'other': []}
            for queue in raw_queues:
                if queue['gameMode'] == 'CLASSIC':
                    mode = 'ranked' if queue['isRanked'] else 'unranked'
                    queues[mode].append(queue)
                elif queue['gameMode'].split('_')[0] != 'TUTORIAL':
                    queues['other'].append(queue)

            return InternalResponse({'data': queues}, 200)

        # if self.command == 'POST' and re.match('^\/queues/\d+/join$', self.path):
        if self.command == 'POST' and self.path == '/lobby':
            if not self.validate_league_connection():
                return
            self.league_request('post', '/lol-lobby/v2/lobby', {
                'queueId': data['queueId']
            })
            self.league_request('post', '/lol-lobby/v2/lobby/matchmaking/search')

            return InternalResponse(None, 204)

        if self.command == 'DELETE' and self.path == '/lobby':
            if not self.validate_league_connection():
                return
            self.league_request('delete', '/lol-lobby/v2/lobby/matchmaking/search')

            return InternalResponse(None, 204)

        if self.command == 'POST' and self.path == '/queue/accept':
            if not self.validate_league_connection():
                return
            self.league_request('post', '/lol-matchmaking/v1/ready-check/accept')

            return InternalResponse(None, 204)

        if self.command == 'POST' and self.path == '/queue/decline':
            if not self.validate_league_connection():
                return
            self.league_request('post', '/lol-matchmaking/v1/ready-check/decline')

            return InternalResponse(None, 204)

        return InternalResponse({'error': 'Method and route combination not found.'}, 404)
