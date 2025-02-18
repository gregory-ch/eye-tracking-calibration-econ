from os import environ

SESSION_CONFIGS = [
    dict(
        name='benchmark',
        display_name="Matrix Game Benchmark",
        app_sequence=['benchmark'],
        num_demo_participants=2,
        # Calibration settings
        error_show=True,
        screen_resolution=1920,
        screen_width=531,
        eye_distance=700,
    ),
    dict(
        name='interface_test',
        display_name='Interface Test',
        app_sequence=['interface_test'],
        num_demo_participants=1,
        error_show=True,
        screen_resolution=1920,
        screen_width=531,
        eye_distance=700,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc="",
    # Calibration settings
    error_show=True,
    screen_resolution=1920,
    screen_width=531,
    eye_distance=700,
)

PARTICIPANT_FIELDS = [
    'opponent_strategies',
    'random_number',
    'asset_value',
    'binary_sequence',
    'value_sequence'
]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'GBP'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'password')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '{{ secret_key }}'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']

ROOMS = [
    dict(
        name='eye_tracking_lab',
        display_name='Eye Tracking Laboratory',
    ),
    dict(
        name='interface_test',
        display_name='Interface Test',
    ),
]

# Add this to prevent database issues
EXTENSION_APPS = []
