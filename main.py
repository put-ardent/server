import subprocess
from http.server import HTTPServer
from request_handler import RequestHandler
import request_handler
import socket

if __name__ == '__main__':
    with subprocess.Popen('ps -x | grep LeagueClientUx', shell=True, stdout=subprocess.PIPE).stdout as processes:
        client_process = processes.readline().decode('utf-8')

    if not client_process:
        exit(1)

    raw_flags = client_process.split(' --')[1::]
    flags = {}
    for raw_flag in raw_flags:
        flag = raw_flag.split('=')

        if len(flag) == 2:
            flags[flag[0]] = flag[1]
        else:
            flags[flag[0]] = None

    request_handler.PORT = int(flags['app-port'])
    request_handler.PASSWORD = flags['remoting-auth-token']

    print('Running the server on 0.0.0.0:2137')
    server = HTTPServer(('0.0.0.0', 2137), RequestHandler)

    hostname = socket.gethostname()
    possible_ips = socket.gethostbyname_ex(hostname)[2]
    local_ip = possible_ips.pop()
    while local_ip == '127.0.0.1':
        local_ip = possible_ips.pop()

    print('Awaiting connections')
    print('To connect via the mobile app, provide it with the address ' + local_ip + ':2137')
    server.serve_forever()

    # summoner_id = requester.request('GET', '/lol-summoner/v1/current-summoner').json()['summonerId']
    # team_members = requester.request('GET', '/lol-champ-select/v1/session').json()['myTeam']
