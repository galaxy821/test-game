class Game:
    def __init__(self):
        self.players = {}  # {sid: {'name': str, 'choice': None, 'ready': False, 'alive': True}}
        self.in_round = False

    def add_player(self, sid, name):
        self.players[sid] = {'name': name, 'choice': None, 'ready': False, 'alive': True}

    def remove_player(self, sid):
        if sid in self.players:
            del self.players[sid]

    def set_ready(self, sid):
        if sid in self.players:
            self.players[sid]['ready'] = True

    def all_ready(self):
        return all(p['ready'] for p in self.players.values() if p['alive'])

    def reset_round(self):
        for p in self.players.values():
            if p['alive']:
                p['choice'] = None
                p['ready'] = False

    def record_choice(self, sid, choice):
        self.players[sid]['choice'] = choice

    def all_chosen(self):
        return all(p['choice'] for p in self.players.values() if p['alive'])

    def evaluate(self):
        result_map = {'rock': 0, 'scissors': 1, 'paper': 2}
        reverse_map = {0: 'rock', 1: 'scissors', 2: 'paper'}

        alive_players = {sid: p for sid, p in self.players.items() if p['alive']}
        choices = {sid: result_map[p['choice']] for sid, p in alive_players.items()}

        unique_choices = set(choices.values())
        
        # 비김: 전부 같은 거거나 세 종류 다 나왔을 때
        if len(unique_choices) == 1 or len(unique_choices) == 3:
            return []

        # 승자 결정
        winning_choice = None
        if 0 in unique_choices and 1 in unique_choices:
            winning_choice = 0  # rock wins
        elif 1 in unique_choices and 2 in unique_choices:
            winning_choice = 1  # scissors wins
        elif 0 in unique_choices and 2 in unique_choices:
            winning_choice = 2  # paper wins

        losers = []
        for sid, choice in choices.items():
            if choice != winning_choice:
                self.players[sid]['alive'] = False
                losers.append(sid)

        return losers

    def get_alive(self):
        return [sid for sid, p in self.players.items() if p['alive']]