from otree.api import *
import random


doc = """
3x3 Matrix Game for eye-tracking calibration
"""


class Constants(BaseConstants):
    name_in_url = 'benchmark'
    players_per_group = None  # Changed to None since we're using bots
    num_rounds = 6
    BOTS_PER_GROUP = 1
    AGENTS_PER_GROUP = BOTS_PER_GROUP + 1

    # Matrix 1
    matrix_1 = {
        'I': { 
            'left': {'row': 28, 'col': 49},
            'middle': {'row': 78, 'col': 67},
            'right': {'row': 43, 'col': 75}
        },
        'II': { 
            'left': {'row': 60, 'col': 27},
            'middle': {'row': 22, 'col': 21},
            'right': {'row': 68, 'col': 38}
        },
        'III': { 
            'left': {'row': 82, 'col': 33},
            'middle': {'row': 73, 'col': 41},
            'right': {'row': 35, 'col': 78}
        }
    }

    # Matrix 2
    matrix_2 = {
        'I': {  
            'left': {'row': 82, 'col': 68},
            'middle': {'row': 33, 'col': 47},
            'right': {'row': 41, 'col': 76}
        },
        'II': {  
            'left': {'row': 67, 'col': 40},
            'middle': {'row': 79, 'col': 33},
            'right': {'row': 39, 'col': 84}
        },
        'III': {  
            'left': {'row': 17, 'col': 19},
            'middle': {'row': 57, 'col': 29},
            'right': {'row': 65, 'col': 40}
        }
    }

    # Matrix 3
    matrix_3 = {
        'I': {  
            'left': {'row': 32, 'col': 79},
            'middle': {'row': 66, 'col': 36},
            'right': {'row': 78, 'col': 29}
        },
        'II': { 
            'left': {'row': 44, 'col': 77},
            'middle': {'row': 82, 'col': 71},
            'right': {'row': 28, 'col': 52}
        },
        'III': { 
            'left': {'row': 63, 'col': 39},
            'middle': {'row': 21, 'col': 20},
            'right': {'row': 58, 'col': 33}
        }
    }

    # Strategy types for each matrix
    matrix_strategies = {
        'matrix_1': {
            'I': 'coordination',    # dash line
            'III': 'naive',         # solid line
            'II': 'nash'          # no line
        },
        'matrix_2': {
            'III': 'nash',           # no line
            'I': 'coordination',   # dash line
            'II': 'naive'         # solid line
        },
        'matrix_3': {
            'I': 'naive',          # solid line
            'III': 'nash',          # no line
            'II': 'coordination'   # dash line
        }
    }

    matrix_types = ['matrix_1', 'matrix_2', 'matrix_3']
    opponent_types = ['coordination', 'naive', 'nash']
    strategy_descriptions = {
        'coordination': "Your opponent follows coordination strategy",
        'naive': "Your opponent follows naive strategy",
        'nash': "Your opponent follows Nash strategy"
    }

    @staticmethod
    def calculate_ppd(resolution, width, distance):
        """Calculate Pixels Per Degree"""
        return ((resolution/width) * 3.14) / 180 * distance
    
    @staticmethod
    def calculate_error_radius(ppd):
        """Calculate error radius in pixels"""
        return 2 * ppd


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        # Create list with repeated strategies
        strategies = Constants.opponent_types * (Constants.num_rounds // len(Constants.opponent_types))
        strategies += Constants.opponent_types[:Constants.num_rounds % len(Constants.opponent_types)]
        
        # For each participant create shuffled copy of strategies
        for p in subsession.get_players():
            participant_strategies = strategies.copy()
            random.shuffle(participant_strategies)
            # Store directly in participant
            p.participant.opponent_strategies = participant_strategies
    
    # Create/update bot for each player in every round
    for p in subsession.get_players():
        # Get strategy from participant
        current_strategy = p.participant.opponent_strategies[subsession.round_number - 1]
        MyBot.create(
            player=p, 
            agent_id=1,
            strategy=current_strategy
        )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    column = models.StringField(
        choices=['left', 'middle', 'right'],
        doc="Selected column in the matrix"
    )
    decision_time = models.FloatField(doc="Decision time in seconds")
    opponent_type = models.StringField(doc="Type of opponent strategy")


class MyBot(ExtraModel):
    player = models.Link(Player)
    row = models.StringField(choices=['I', 'II', 'III'])
    strategy = models.StringField()
    agent_id = models.IntegerField()


def set_bot_choice(player: Player):
    bot = MyBot.filter(player=player)[0]
    current_matrix = get_current_matrix(player)
    # Use same modulo logic for matrix type
    matrix_index = (player.round_number - 1) % len(Constants.matrix_types)
    matrix_type = Constants.matrix_types[matrix_index]
    
    # Get strategy from bot and save to player
    strategy_type = bot.strategy
    player.opponent_type = strategy_type  # Save strategy type
    
    # Select row based on strategy
    possible_rows = [
        row for row, strat in Constants.matrix_strategies[matrix_type].items()
        if strat == strategy_type
    ]
    bot.row = possible_rows[0] if possible_rows else random.choice(['I', 'II', 'III'])
    
    # Calculate payoffs
    player.payoff = current_matrix[bot.row][player.column]['col']


def get_current_matrix(player: Player):
    # Use modulo to cycle through matrices
    matrix_index = (player.round_number - 1) % len(Constants.matrix_types)
    matrix_type = Constants.matrix_types[matrix_index]
    
    if matrix_type == 'matrix_1':
        return Constants.matrix_1
    elif matrix_type == 'matrix_2':
        return Constants.matrix_2
    return Constants.matrix_3


# PAGES
class Introduction(Page):
    @staticmethod
    def vars_for_template(player: Player):
        bot = MyBot.filter(player=player)[0]
        return {
            'round_number': player.round_number,
            'opponent_description': Constants.strategy_descriptions[bot.strategy]
        }


class Calibration(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def vars_for_template(player: Player):
        # Calculate PPD and error radius
        ppd = Constants.calculate_ppd(
            player.session.config['screen_resolution'],
            player.session.config['screen_width'],
            player.session.config['eye_distance']
        )
        error_radius = Constants.calculate_error_radius(ppd)
        
        return {
            'error_show': player.session.config['error_show'],
            'error_radius': error_radius
        }


class Decision(Page):
    form_model = 'player'
    form_fields = ['column', 'decision_time']
    
    @staticmethod
    def vars_for_template(player: Player):
        bot = MyBot.filter(player=player)[0]
        matrix_index = (player.round_number - 1) % len(Constants.matrix_types)
        return {
            'matrix': get_current_matrix(player),
            'matrix_type': Constants.matrix_types[matrix_index],
            'opponent_strategy': bot.strategy
        }
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        set_bot_choice(player)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        bot = MyBot.filter(player=player)[0]
        current_matrix = get_current_matrix(player)
        matrix_index = (player.round_number - 1) % len(Constants.matrix_types)
        return {
            'matrix': current_matrix,
            'matrix_type': Constants.matrix_types[matrix_index],
            'my_column': player.column,
            'robot_row': bot.row,
            'my_payoff': player.payoff,
            'other_payoff': current_matrix[bot.row][player.column]['row']
        }


page_sequence = [Introduction, Calibration, Decision, Results]

