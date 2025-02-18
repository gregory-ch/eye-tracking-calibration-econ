from otree.api import *
import random
import numpy as np


doc = """
Interface test with number inputs and binary sequence generation
"""


class Constants(BaseConstants):
    name_in_url = 'interface_test'
    players_per_group = None
    num_rounds = 1
    
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
        if subsession.round_number == 1:
            # Generate asset value (0 or 100)
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
            
            # Generate random number from 1 to sequence_length (не +1)
            random_number = random.randint(1, Constants.sequence_length)
            
            # Store sequences and random number in participant vars
            p.participant.asset_value = asset_value
            p.participant.binary_sequence = binary_sequence
            p.participant.value_sequence = value_sequence
            p.participant.random_number = random_number
            
        # Create bot for current round
        MyBot.create(
            player=p,
            agent_id=1,
            binary_value=p.participant.binary_sequence[subsession.round_number - 1],
            predicted_value=p.participant.value_sequence[subsession.round_number - 1]
        )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    first_number = models.IntegerField(
        min=1, 
        max=100,
        doc="First number input"
    )
    second_number = models.IntegerField(
        min=1, 
        max=100,
        doc="Second number input"
    )


class MyBot(ExtraModel):
    player = models.Link(Player)
    binary_value = models.IntegerField()
    predicted_value = models.IntegerField()
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


class Cell:
    def __init__(self, number='', value=None, is_input=False, is_reserved=False, signal=None):
        self.number = number
        self.value = value if value is not None else "—"
        self.is_input = is_input
        self.is_reserved = is_reserved
        self.signal = signal


# PAGES
class Introduction(Page):
    pass


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


class Decision(Page):
    form_model = 'player'
    form_fields = ['first_number']
    
    @staticmethod
    def vars_for_template(player: Player):
        try:
            value_sequence = player.participant.value_sequence
            random_number = player.participant.random_number
            
            cells = []
            # Первые 8 ячеек всегда показываем
            for i in range(8):
                cells.append(Cell(
                    number=str(i + 1),
                    value=value_sequence[i] if i < random_number else None
                ))
            
            # 9-я ячейка всегда для ввода
            cells.append(Cell(is_input=True))
            
            # 10-я ячейка показывает 9-е значение, если random_number > 8
            if random_number > 8:
                cells.append(Cell(
                    number='10',  # Номер ячейки
                    value=value_sequence[8]  # 9-е значение последовательности
                ))
            else:
                cells.append(Cell(number='10'))
            
            cells.append(Cell(number='11'))  # 11-я ячейка
            cells.append(Cell(is_reserved=True))  # 12-я ячейка
            
            return {
                'cells': cells,
                'default_value': random.randint(1, 100)
            }
        except AttributeError:
            print("Debug: participant fields not found")
            return {
                'cells': [],
                'default_value': 50
            }


class SecondPage(Page):
    form_model = 'player'
    form_fields = ['second_number']
    
    @staticmethod
    def vars_for_template(player: Player):
        try:
            value_sequence = player.participant.value_sequence
            binary_sequence = player.participant.binary_sequence
            random_number = player.participant.random_number
            signal = binary_sequence[random_number - 1]
            
            cells = []
            # Первые 8 ячеек всегда показываем
            for i in range(8):
                cells.append(Cell(
                    number=str(i + 1),
                    value=value_sequence[i] if i < random_number else None
                ))
            
            # 9-я ячейка всегда для ввода
            cells.append(Cell(is_input=True))
            
            # 10-я ячейка - значение, если random_number > 8
            if random_number > 8:
                cells.append(Cell(
                    number='10',  # Номер ячейки
                    value=value_sequence[8]  # 9-е значение последовательности
                ))
            else:
                cells.append(Cell(number='10'))
            
            cells.append(Cell(number='11'))  # 11-я ячейка
            cells.append(Cell(is_reserved=True, signal=signal))  # 12-я ячейка
            
            return {
                'cells': cells,
                'default_value': random.randint(1, 100)
            }
        except AttributeError:
            return {
                'cells': [],
                'default_value': 50
            }


page_sequence = [Introduction, Calibration, Decision, SecondPage]

