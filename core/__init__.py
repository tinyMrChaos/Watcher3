import ssl
import sys
import os
import cherrypy
import logging

logging = logging.getLogger(__name__)

# Paths to local things
PROG_PATH = None            # Absolute path to watcher.py parent dir
SCRIPT_PATH = None          # Absolute path to watcher.py file
CONF_FILE = os.path.join('userdata', 'config.cfg')
LOG_DIR = 'logs'
PLUGIN_DIR = 'plugins'
DB_FILE = os.path.join('userdata', 'watcher.sqlite')
THEME = 'Default'
MAKO_CACHE = 'templates/cache'

# Paths to internet things
GIT_URL = 'https://github.com/nosmokingbandit/watcher3'
GIT_REPO = 'https://github.com/nosmokingbandit/watcher3.git'
GIT_API = 'https://api.github.com/repos/nosmokingbandit/watcher3'

# Server settings
SERVER_ADDRESS = None
SERVER_PORT = None
URL_BASE = ''

# Update info
UPDATE_STATUS = None        # Dict of git update status ie {'status': 'current'}
UPDATE_LAST_CHECKED = None  # Obj datetime.datetime.now() when last check executed
UPDATING = False            # Bool if current running update process
CURRENT_HASH = None         # Current commit hash of install

# Dynamic info
NEXT_SEARCH = None                          # Obj datetime.datetime.now() + searchfrequency
CONFIG = {}                                 # Dict of config file
NOTIFICATIONS = []                          # List of dicts of notifications and individual settings
NO_VERIFY = ssl.create_default_context()    # Obj no verify context for requests
NO_VERIFY.check_hostname = False
NO_VERIFY.verify_mode = ssl.CERT_NONE
PLATFORM = None                             # Host OS ['windows', '*nix']
SESSION_KEY = '_cp_username'                # Key to use when generating login session
LANGUAGES = {}                              # Dict of language name: gettext object, ie {'es': <gettext_obj>}
LANGUAGE = 'en'                             # Str first two letters of language code

# Rate limiting
TMDB_TOKENS = 35        # Int begin amount of tokens for TMDB rate limiting
TMDB_LAST_FILL = None   # Obj datetime.datetime.now() of last time TMDB tokens have been filled

# Global Media Constants
SOURCES = ('BluRay-4K', 'BluRay-1080P', 'BluRay-720P', 'BluRay-SD',
           'WebDL-4K', 'WebDL-1080P', 'WebDL-720P', 'WebDL-SD',
           'WebRip-4K', 'WebRip-1080P', 'WebRip-720P', 'WebRip-SD',
           'DVD-SD',
           'Screener-1080P', 'Screener-720P',
           'Telesync-SD', 'CAM-SD')

# Module instances
sql = None
manage = None
updater = None

# Plugin instances
scheduler_plugin = None


# Methods
def restart():
    ''' Stops server and re-executes script
    '''
    cherrypy.engine.stop()
    python = sys.executable
    args = ['"{}"'.format(SCRIPT_PATH) if PLATFORM == 'windows' else SCRIPT_PATH] + sys.argv[1:]
    p = 'Server stopped -- respawning script as: \n {} {}'.format(python, *args)
    logging.info(p)
    print(p)
    os.execl(python, python, *args)


def shutdown():
    ''' Exits server and script
    '''
    logging.info('Shutting Down Server...')
    cherrypy.engine.exit()
    sys.exit(0)
