from flask import Flask, request
from flask_socketio import SocketIO, emit
from game import Game
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
game = Game()

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f"{sid} connected")

@socketio.on('join')
def handle_join(data):
    sid = request.sid
    name = data['name']
    game.add_player(sid, name)
    emit('joined', {'message': f"{name} joined!"}, broadcast=True)

@socketio.on('ready')
def handle_ready():
    sid = request.sid
    game.set_ready(sid)
    emit('update', {'ready_players': [p['name'] for p in game.players.values() if p['ready']]}, broadcast=True)

    if game.all_ready() and not game.in_round:
        game.in_round = True
        socketio.start_background_task(start_round)

def start_round():
    socketio.emit('countdown', {'count': 3}, to=None)
    time.sleep(1)
    socketio.emit('countdown', {'count': 2}, to=None)
    time.sleep(1)
    socketio.emit('countdown', {'count': 1}, to=None)
    time.sleep(1)
    socketio.emit('choose', {'message': 'Choose rock, paper, or scissors!'}, to=None)

@socketio.on('choice')
def handle_choice(data):
    sid = request.sid
    game.record_choice(sid, data['choice'])

    if game.all_chosen():
        losers = game.evaluate()
        # emit('round_result', {
        #     'losers': losers,
        #     'loser_names': [game.players[sid]['name'] for sid in losers],
        #     'alive': game.get_alive()
        # }, broadcast=True)
        emit('round_result', {
            'losers': losers,
            'loser_names': [game.players[sid]['name'] for sid in losers],
            'alive': game.get_alive(),
            'alive_names': [game.players[sid]['name'] for sid in game.get_alive()]
        }, broadcast=True)
        game.reset_round()
        game.in_round = False

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    game.remove_player(sid)
    emit('update', {'message': f"{sid} disconnected"}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)