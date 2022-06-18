import ssl
import websockets
from typing import Optional
from app.struct.connection import LeagueConnection
from time import sleep
import base64
import asyncio
from app.connector.connectors import MobileConnector
import json
import requests


class WebsocketHandler:
    LEAGUE_CONNECTION: Optional[LeagueConnection] = None

    def __init__(self):
        self.shutdown = False

    def run(self):
        while not self.LEAGUE_CONNECTION.open:
            sleep(.5)

        asyncio.run(self._run_websocket())

    async def _run_websocket(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations('./riotgames.pem')

        url = f'wss://localhost:{WebsocketHandler.LEAGUE_CONNECTION.port}'

        auth = f'riot:{WebsocketHandler.LEAGUE_CONNECTION.password}'
        auth = 'Basic ' + base64.b64encode(auth.encode()).decode()

        async with websockets.connect(url, extra_headers={'Authorization': auth}, ssl=ssl_context, max_size=None) as websocket:
            await websocket.send('[5, "OnJsonApiEvent"]')
            while True:
                try:
                    async for message in websocket:
                        WebsocketHandler._handle_message(message)
                except BaseException:
                    continue

    @staticmethod
    def _handle_message(message):
        if not message:
            return

        message = json.loads(message)
        if len(message) > 2 and type(message[2]) is dict:
            print(message[2])
            content = message[2]
            data = content['data']
            if content['uri'] == '/lol-matchmaking/v1/search' and content['eventType'] == 'Update':
                MobileConnector.send({
                    'type': 'queue-timer',
                    'estimatedTime': data['estimatedQueueTime'],
                    'currentTime': data['timeInQueue'],
                })
            elif content['uri'] == '/lol-matchmaking/v1/ready-check' and content['eventType'] == 'Update':
                MobileConnector.send({
                    'type': 'accept-queue-timer',
                    'playerResponse': data['playerResponse'],
                    'state': data['state'],
                    'timer': data['timer'],
                })
            elif content['uri'] == '/lol-lobby-team-builder/champ-select/v1/session' and content['eventType'] == 'Update':
                cells_completion = {}
                for cell_id, cell in enumerate(data['actions'][0]):
                    cells_completion[cell_id] = cell['completed']

                my_team = []
                for summoner in data['myTeam']:
                    my_team.append({
                        'cellId': summoner['cellId'],
                        'championId': summoner['championId'],
                        'summonerId': summoner['summonerId'],
                        'picked': cells_completion[summoner['cellId']],
                    })

                enemy_team = []
                for summoner in data['theirTeam']:
                    enemy_team.append({
                        'cellId': summoner['cellId'],
                        'championId': summoner['championId'],
                        'summonerId': summoner['summonerId'],
                        'picked': cells_completion[summoner['cellId']],
                    })

                MobileConnector.send({
                    'type': 'champ-select-state',
                    'myTeam': my_team,
                    'enemyTeam': enemy_team,
                })
            elif content['uri'] == '/lol-lobby-team-builder/champ-select/v1/pickable-champion-ids' and content['eventType'] == 'Create':
                champions = []
                champion_data = requests.request('get', 'https://ddragon.leagueoflegends.com/cdn/12.11.1/data/en_US/champion.json').json()['data']
                for internal_id in champion_data:
                    champion = champion_data[internal_id]
                    champions.append({
                        'id': champion['key'],
                        'name': champion['name'],
                        'internalId': champion['id'],
                        'pickable': int(champion['key']) in data,
                    })

                MobileConnector.send({
                    'type': 'champions-grid',
                    'champions': champions
                })
            elif '/'.join(content['uri'].split('/')[:-1]) == '/lol-champ-select/v1/grid-champions' and content['eventType'] == 'Update':
                pickable = not (
                        data['selectionStatus']['pickedByOtherOrBanned'] and
                        not data['selectionStatus']['pickIntented']
                ) and (data['owned'] or data['freeToPlay'])
                MobileConnector.send({
                    'type': 'champion-selected',
                    'champion': {
                        'id': data['id'],
                        'name': data['name'],
                    },
                    'picked': data['selectionStatus']['pickedByOtherOrBanned'],
                    'intended': data['selectionStatus']['pickIntented'],
                    'pickable': pickable
                })
