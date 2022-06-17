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
        if message[3]['uri'] == '/lol-matchmaking/v1/search':
            MobileConnector.send({
                'type': 'queue-timer',
                'estimated-time': message[3]['data']['estimatedQueueTime'],
                'current-time': message[3]['data']['timeInQueue'],
            })
        elif message[3]['uri'] == '/lol-matchmaking/v1/ready-check':
            MobileConnector.send({
                'type': 'accept-queue-timer',
                'state': message[3]['data']['state'],
                'timer': message[3]['data']['timer'],
            })
        print(message)
        print()
