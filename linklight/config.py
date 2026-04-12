HEAD_BASE_ADDR = 400
STROBE_BASE_ADDR = 1
PAR_BASE_ADDR = 200

DEFAULT_HEAD_BRIGHTNESS = 100
DEFAULT_STROBE_BRIGHTNESS = 10
DEFAULT_PAR_BRIGHTNESS = 100
DMX_UNIVERSE = 1
OLA_HOST = "localhost"
OLA_PORT = 9090

# Usable pan/tilt range (0-255 DMX values).
# Adjust these to the physical subset your fixture can actually reach.
PAN_MIN = 118
PAN_MAX = 140
TILT_MIN = 234
TILT_MAX = 234

# Mover home position (absolute DMX values) — where it parks when idle
HOME_PAN = 50
HOME_TILT = 130

# Disco ball position (relative 0.0-1.0 within PAN/TILT range)
DISCO_BALL_PAN = 0.6
DISCO_BALL_TILT = 0.5

PAN_SPEED = 230
SLOW_PAN_SPEED = 253

INITIAL_BPM = 120

# Seconds to wait after BPM stops changing before re-arming song detection
SONG_CHANGE_COOLDOWN_S = 4.0
