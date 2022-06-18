import ssl
import websockets
from typing import Optional
from app.struct.connection import LeagueConnection
from time import sleep
import base64
import asyncio
from app.connector.connectors import MobileConnector


class WebsocketHandler:
    LEAGUE_CONNECTION: Optional[LeagueConnection] = None

    def __init__(self):
        self.shutdown = False

    def run(self):
        while not self.LEAGUE_CONNECTION.open:
            sleep(.5)

        asyncio.run(WebsocketHandler._run_websocket())
        self.run()

    @staticmethod
    async def _run_websocket():
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations('./riotgames.pem')

        url = f'wss://localhost:{WebsocketHandler.LEAGUE_CONNECTION.port}'

        auth = f'riot:{WebsocketHandler.LEAGUE_CONNECTION.password}'
        auth = 'Basic ' + base64.b64encode(auth.encode()).decode()

        async with websockets.connect(url, extra_headers={'Authorization': auth}, ssl=ssl_context) as websocket:
            await websocket.send('[5, "OnJsonApiEvent"]')
            async for message in websocket:
                WebsocketHandler._handle_message(message)

    @staticmethod
    def _handle_message(message):
        if len(message) > 2:
            content = message[3]
            data = content['data']
            if content['uri'] == '/lol-matchmaking/v1/search':
                MobileConnector.send({
                    'type': 'queue-timer',
                    'estimated-time': data['estimatedQueueTime'],
                    'current-time': data['timeInQueue'],
                })
            elif content['uri'] == '/lol-matchmaking/v1/ready-check':
                MobileConnector.send({
                    'type': 'accept-queue-timer',
                    'state': data['state'],
                    'timer': data['timer'],
                })
        print(message)
        print()
