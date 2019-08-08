import os
from datetime import timedelta

SECRET_KEY = os.urandom(16)
# default expiration time of a permanent session
PERMANENT_SESSION_LIFETIME = timedelta(days=365*100)
# prevent sending the cookie every time
SESSION_REFRESH_EACH_REQUEST = False
# default expiration time of one-time session
SESSION_COOKIE_LIFETIME = 600
