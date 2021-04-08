import requests
from itertools import cycle

if __name__ == '__main__':
    found = False
    SERVER_URL = "https://pwpcourse.eu.pythonanywhere.com"
    directions = ['maze:south', 'maze:north']

    directionCycle = cycle(directions)
    direction = next(directionCycle)

    with requests.Session() as s:
        resp = s.get(SERVER_URL + "/api/")
        body = resp.json()
        nextRoom = s.get(SERVER_URL + body['@controls']['maze:entrance']['href'])

    while not found:
        body = nextRoom.json()
        if body['content'] == "cheese":
            print('FOUND IT')
            print(body['@controls']['self']['href'])
            found = True
        try:
            nextRoom = s.get(SERVER_URL + body['@controls'][direction]['href'])
        except KeyError:
            nextRoom = s.get(SERVER_URL + body['@controls']['maze:east']['href'])
            body = nextRoom.json()
            direction = next(directionCycle)
            nextRoom = s.get(SERVER_URL + body['@controls'][direction]['href'])


