import datetime
import json
import logging
import time

import core
from core import proxy
from core.helpers import Url
from core.providers.torrentbase import TorrentProvider

logging = logging.getLogger(__name__)


class RarbgTokenError(Exception):
    ''' Raised when a Rarbg token cannot be retrieved '''
    def __init__(self, msg=None):
        self.msg = msg if msg else 'Failed to retrieve new token from Rarbg\'s torrentapi.org.'

classname = "RarBG"
class RarBG(TorrentProvider):
    '''
    This api is limited to one request every 2 seconds.
    '''

    id = "rarbg"
    name = "Rarbg"

    timeout = None
    _token = None
    _token_timeout = datetime.datetime.now()

    @staticmethod
    def token():
        ''' Gets/sets token and monitors token timeout

        Returns str rarbg token
        '''
        if not RarBG._token:
            RarBG._token = RarBG._get_token()
        else:
            now = datetime.datetime.now()
            if (now - RarBG._token_timeout).total_seconds() > 900:
                RarBG._token = RarBG._get_token()
                RarBG._token_timeout = now
        return RarBG._token

    @staticmethod
    def search(imdbid, term):
        ''' Search api for movie
        imdbid (str): imdb id #

        Returns list of dicts of parsed releases
        '''

        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on Rarbg for {}.'.format(imdbid))
        if RarBG.timeout:
            now = datetime.datetime.now()
            while RarBG.timeout > now:
                time.sleep(1)
                now = datetime.datetime.now()

        try:
            url = (
                'https://www.torrentapi.org/pubapi_v2.php'
                '?token={}'
                '&mode=search'
                '&search_imdb={}'
                '&category=movies'
                '&format=json_extended'
                '&app_id=Watcher'.format(RarBG.token(), imdbid)
            )

            RarBG.timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)

            if proxy_enabled and proxy.whitelist('https://www.torrentapi.org') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            results = json.loads(response).get('torrent_results')
            if results:
                return RarBG.parse(results, imdbid=imdbid)
            else:
                logging.info('Nothing found on Rarbg.')
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Rarbg search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        ''' Gets latest rss feed from api

        Returns list of dicts of parsed releases
        '''
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from Rarbg.')
        if RarBG.timeout:
            now = datetime.datetime.now()
            while RarBG.timeout > now:
                time.sleep(1)
                now = datetime.datetime.now()

        try:
            url = (
                'https://www.torrentapi.org/pubapi_v2.php'
                '?token={}'
                '&mode=list'
                '&category=movies'
                '&format=json_extended'
                '&app_id=Watcher'.format(RarBG.token())
            )
            RarBG.timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)

            if proxy_enabled and proxy.whitelist('https://www.torrentapi.org') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            results = json.loads(response).get('torrent_results')
            if results:
                return RarBG.parse(results)
            else:
                logging.info('Nothing found in Rarbg RSS.')
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Rarbg RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def _get_token():
        ''' Get api access token

        Returns str or None
        '''
        logging.info('Getting RarBG access token.')
        url = 'https://www.torrentapi.org/pubapi_v2.php?get_token=get_token'

        try:
            result = json.loads(Url.open(url).text)
            token = result.get('token')
            return token
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Failed to get Rarbg token.', exc_info=True)
            raise RarbgTokenError(str(e))

    @staticmethod
    def parse(results, imdbid=None, term=None):
        ''' Parse api response
        results (list): dicts of releases

        Returns list of dicts
        '''

        logging.info('Parsing {} Rarbg results.'.format(len(results)))
        item_keep = (
            'size',
            'pubdate',
            'title',
            'indexer',
            'info_link',
            'guid',
            'torrentfile',
            'resolution',
            'type',
            'seeders'
        )

        parsed_results = []

        for result in results:
            result['indexer'] = 'Rarbg'
            result['info_link'] = result['info_page']
            result['torrentfile'] = result['download']
            result['guid'] = result['download'].split('&')[0].split(':')[-1]
            result['type'] = 'magnet'
            result['pubdate'] = None

            result = {k: v for k, v in result.items() if k in item_keep}

            result['imdbid'] = imdbid or result.get('episode_info', {}).get('imdb')
            result['status'] = 'Available'
            result['score'] = 0
            result['downloadid'] = None
            result['freeleech'] = 0
            result['download_client'] = None
            parsed_results.append(result)
        logging.info('Found {} results from Rarbg.'.format(len(parsed_results)))
        return parsed_results
