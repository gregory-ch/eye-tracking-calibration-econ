from otree.api import *
import random
import numpy as np


doc = """
Interface test with number inputs and binary sequence generation
"""


class Constants(BaseConstants):
    name_in_url = 'interface_test'
    players_per_group = None
    num_rounds = 3
    
    # Sequence parameters
    sequence_length = 10
    start_value = 50
    up_change = 20
    down_change = -20
    
    # Probabilities
    asset_zero_prob_zero = 0.7  # P(0|asset=0)
    asset_zero_prob_one = 0.3   # P(1|asset=0)
    asset_hundred_prob_zero = 0.3  # P(0|asset=100)
    asset_hundred_prob_one = 0.7   # P(1|asset=100)
    
    signal_accuracy = 0.8  # Probability of correct signal movement

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


def generate_binary_sequence(asset_value, length):
    """Generate binary sequence based on asset value"""
    if asset_value == 0:
        prob_one = Constants.asset_zero_prob_one
    else:  # asset_value == 100
        prob_one = Constants.asset_hundred_prob_one
    
    return [1 if random.random() < prob_one else 0 for _ in range(length)]


def generate_value_sequence(binary_sequence, start_value):
    """Generate value sequence based on binary signals"""
    values = [start_value]
    current_value = start_value
    
    for signal in binary_sequence:
        # Determine direction of movement
        if signal == 1:
            # Move up with 80% probability
            if random.random() < Constants.signal_accuracy:
                change = Constants.up_change
            else:
                change = Constants.down_change
        else:
            # Move down with 80% probability
            if random.random() < Constants.signal_accuracy:
                change = Constants.down_change
            else:
                change = Constants.up_change
        
        # Calculate new value and ensure it's within bounds
        new_value = max(0, min(100, current_value + change))
        values.append(new_value)
        current_value = new_value
    
    return values[1:]  # Remove start value


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        # Generate asset value (0 or 100) for each round
        asset_value = random.choice([0, 100])
        
        # Generate binary sequence
        binary_sequence = generate_binary_sequence(
            asset_value, 
            Constants.sequence_length
        )
        
        # Generate value sequence
        value_sequence = generate_value_sequence(
            binary_sequence, 
            Constants.start_value
        )
        
        # Generate random number from 1 to sequence_length
        random_number = random.randint(1, Constants.sequence_length)
        
        # Store values in player fields
        p.asset_value = asset_value
        p.binary_sequence = str(binary_sequence)  # Convert list to string for storage
        p.value_sequence = str(value_sequence)    # Convert list to string for storage
        p.random_number = random_number
            
        # Create bot for current round
        MyBot.create(
            player=p,
            agent_id=1,
            binary_value=binary_sequence[subsession.round_number - 1],
            predicted_value=value_sequence[subsession.round_number - 1]
        )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    first_number = models.IntegerField(
        min=0, 
        max=100,
        doc="First number input"
    )
    second_number = models.IntegerField(
        min=0, 
        max=100,
        doc="Second number input"
    )
    asset_value = models.IntegerField(doc="True asset value for this round")
    random_number = models.IntegerField(doc="Random number for sequence display")
    binary_sequence = models.StringField(doc="Binary sequence for this round")
    value_sequence = models.StringField(doc="Value sequence for this round")


class MyBot(ExtraModel):
    player = models.Link(Player)
    binary_value = models.IntegerField()
    predicted_value = models.IntegerField()
    agent_id = models.IntegerField()


# def set_bot_choice(player: Player):
#     bot = MyBot.filter(player=player)[0]
#     current_matrix = get_current_matrix(player)
#     # Use same modulo logic for matrix type
#     matrix_index = (player.round_number - 1) % len(Constants.matrix_types)
#     matrix_type = Constants.matrix_types[matrix_index]
    
#     # Get strategy from bot and save to player
#     strategy_type = bot.strategy
#     player.opponent_type = strategy_type  # Save strategy type
    
#     # Select row based on strategy
#     possible_rows = [
#         row for row, strat in Constants.matrix_strategies[matrix_type].items()
#         if strat == strategy_type
#     ]
#     bot.row = possible_rows[0] if possible_rows else random.choice(['I', 'II', 'III'])
    
#     # Calculate payoffs
#     player.payoff = current_matrix[bot.row][player.column]['col']


# def get_current_matrix(player: Player):
#     # Use modulo to cycle through matrices
#     matrix_index = (player.round_number - 1) % len(Constants.matrix_types)
#     matrix_type = Constants.matrix_types[matrix_index]
    
#     if matrix_type == 'matrix_1':
#         return Constants.matrix_1
#     elif matrix_type == 'matrix_2':
#         return Constants.matrix_2
#     return Constants.matrix_3


# class Cell:
#     def __init__(self, number='', value=None, is_input=False, is_reserved=False, signal=None):
#         self.number = number
#         self.value = value if value is not None else "—"
#         self.is_input = is_input
#         self.is_reserved = is_reserved
#         self.signal = signal


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1  # show only in round 1


class Calibration(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def vars_for_template(player: Player):
        # Get values from config
        resolution = float(player.session.config.get('screen_resolution', 1920))
        width = float(player.session.config.get('screen_width', 531))
        distance = float(player.session.config.get('eye_distance', 700))
        error_show = player.session.config.get('error_show', True)
        
        # Calculate PPD and error radius
        ppd = Constants.calculate_ppd(resolution, width, distance)
        error_radius = Constants.calculate_error_radius(ppd)
        
        return {
            'error_show': error_show,
            'error_radius': error_radius
        }


def generate_cells_for_template(player, page_type='decision'):
    """Helper function to generate cells for both pages"""
    try:
        binary_sequence = eval(player.binary_sequence)  # Convert string back to list
        value_sequence = eval(player.value_sequence)    # Convert string back to list
        random_number = player.random_number
        signal = binary_sequence[random_number - 1]
        
        cells = []
        for i in range(12):
            # Adjust number display logic
            display_number = None
            if not (i == 8 or i == 11):  # Not reserved and not input cell
                display_number = i + 1 if i < 8 else i  # Decrease numbers after reserved cell by 1
            
            # Get value from value_sequence for non-special cells
            cell_value = None
            if i < 8:
                cell_value = value_sequence[i] if i < random_number else "—"
            elif i > 8 and i < 11:  # Cells 10 and 11
                adjusted_index = i - 1  # Adjust index due to reserved cell
                cell_value = value_sequence[adjusted_index] if adjusted_index < random_number else "—"
            
            cell = {
                'is_input': i == 11,
                'is_reserved': i == 8,
                'number': display_number,
                'value': cell_value,
                'signal': signal if i == 8 else None
            }
            cells.append(cell)
        
        return cells
    except (AttributeError, ValueError) as e:
        print(f"Debug: Error in generate_cells_for_template - {e}")
        return []


class Decision(Page):
    form_model = 'player'
    form_fields = ['first_number']
    
    @staticmethod
    def vars_for_template(player):
        cells = generate_cells_for_template(player, 'decision')
        return {
            'cells': cells,
            'default_value': random.randint(1, 100),  # Generate random start value
            'asset_value': player.asset_value,
            'random_number': player.random_number
        }


class SecondPage(Page):
    form_model = 'player'
    form_fields = ['second_number']
    
    @staticmethod
    def vars_for_template(player):
        cells = generate_cells_for_template(player, 'second')
        return {
            'cells': cells,
            'default_value': random.randint(1, 100),  # Generate random start value
            'asset_value': player.asset_value,
            'random_number': player.random_number
        }


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == Constants.num_rounds
    
    @staticmethod
    def vars_for_template(player: Player):
        # Get all rounds data
        all_rounds = player.in_all_rounds()
        rounds_data = []
        
        for round_player in all_rounds:
            # Calculate prediction error for each round
            prediction_error = abs(round_player.asset_value - round_player.second_number)
            
            rounds_data.append({
                'round_number': round_player.round_number,
                'asset_value': round_player.asset_value,
                'first_guess': round_player.first_number,
                'second_guess': round_player.second_number,
                'error': prediction_error
            })
            
        return {
            'rounds_data': rounds_data,
            'current_round': player.round_number
        }


page_sequence = [Introduction, Calibration, Decision, SecondPage, Results]

