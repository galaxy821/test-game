import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")
    name = input("Enter your name: ")
    sio.emit('join', {'name': name})

@sio.event
def joined(data):
    print(data['message'])

@sio.event
def update(data):
    print("Game status:", data)

@sio.event
def countdown(data):
    print(f"Countdown: {data['count']}")

@sio.event
def choose(data):
    print(data['message'])
    choice = input("Your choice (rock/paper/scissors): ")
    sio.emit('choice', {'choice': choice})

@sio.event
def round_result(data):
    losers = data.get('loser_names', [])
    alive_names = data.get('alive_names', [])

    if not losers:
        print("\n이번 라운드는 무승부입니다! 아무도 탈락하지 않았습니다.")
    else:
        print("\n이번 라운드에서 탈락한 플레이어:")
        for name in losers:
            print(f" - {name}")

    print("\n현재 생존자:")
    for name in alive_names:
        print(f" - {name}")

def play_game():
    sio.connect('http://127.0.0.1:5000')
    while True:
        cmd = input("Type 'ready' when you're ready: ")
        if cmd.lower() == 'ready':
            sio.emit('ready')

if __name__ == '__main__':
    play_game()