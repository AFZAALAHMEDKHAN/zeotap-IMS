from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared SlowAPI limiter used by main.py and endpoint modules.
# Keeping it in a separate file avoids circular imports.
limiter = Limiter(key_func=get_remote_address)