from __future__ import unicode_literals

import json
import logging
import re
from hashlib import md5
from json import JSONDecodeError
from requests.compat import urljoin
from core.helpers import Url
from core.providers.torrentbase import TorrentProvider

logging = logging.getLogger(__name__)

classname = "Torrentday"
class Torrentday(TorrentProvider):
    id = "torrentday"
    name = "Torrentday"

    fields = {
        "cookies": "Cookies"
    }

    url = 'https://www.torrentday.com'
    urls = {
        'login': urljoin(url, '/t'),
        'search': urljoin(url, '/V3/API/API.php'),
        'download': urljoin(url, '/download.php/'),
        'details': urljoin(url, "/details.php?id=")
    }

    categories = {
        'Season': {'c14': 1},
        'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c34': 1},
        'Movie': {'c11': 1, 'c5':1, 'c48':1, 'c44': 1},
        'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c34': 1, 'c14': 1}
    }

    enable_cookies = True

    @staticmethod
    def convert_size(size, default=None, use_decimal=False, **kwargs):
        result = None
        try:
            sep = kwargs.pop('sep', ' ')
            scale = kwargs.pop('units', ['B', 'KB', 'MB', 'GB', 'TB', 'PB'])
            default_units = kwargs.pop('default_units', scale[0])

            if sep:
                size_tuple = size.strip().split(sep)
                scalar, units = size_tuple[0], size_tuple[1:]
                units = units[0].upper() if units else default_units
            else:
                regex_scalar = re.search(r'([\d. ]+)', size, re.I)
                scalar = regex_scalar.group() if regex_scalar else -1
                units = size.strip(scalar) if scalar != -1 else 'B'

            scalar = float(scalar)
            scalar *= (1024 if not use_decimal else 1000) ** scale.index(units)

            result = scalar

        # TODO: Make sure fallback methods obey default units
        except AttributeError:
            result = size if size is not None else default

        except ValueError:
            result = default

        finally:
            try:
                if result != default:
                    result = max(int(result), 0)
            except (TypeError, ValueError):
                pass

        return result

    @staticmethod
    def search(imdbid, term):
        search_url = Torrentday.urls['search']

        post_data = {'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': imdbid}
        post_data.update(Torrentday.categories['Movie'])

        headers = {"Cookie": Torrentday.getConfig('torrentday')['cookie']}
        print(headers)

        response = Url.open(search_url, post_data=post_data, headers=headers)
        try:
            parsed_json = json.loads(response.text)
        except JSONDecodeError:
            logging.error("Torrentday did not get a proper response. Check cookies")
            return []

        if not parsed_json:
            logging.debug('No data returned from provider')
            return []


        try:
            items = parsed_json.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
        except Exception:
            logging.debug('Data returned from provider does not contain any torrents')
            return []

        return Torrentday.parse(items, imdbid)



    @staticmethod
    def get_rss():
        logging.info('Fetching latest RSS from Torrentday.')
        return []

    @staticmethod
    def parse(data, imdbid=None, term=None):
        logging.info('Parsing Torrentday results.')

        results = []
        for i in data:
            result = {}

            try:
                title = re.sub(r'\[.*\=.*\].*\[/.*\]', '', i['name']) if i['name'] else None
                torrent_url = urljoin(Torrentday.urls['download'], '{0}/{1}'.format(i['id'], i['fname'])) if i['id'] and i['fname'] else None

                result['score'] = 0
                result['size'] = Torrentday.convert_size(i['size']) or -1
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = title
                result['imdbid'] = imdbid
                result['indexer'] = 'TorrentDay'
                result['info_link'] = urljoin(Torrentday.urls['details'], "?id="+str(i['id']))
                result['torrentfile'] = torrent_url
                result['guid'] = md5("torrentday:{}".format(id).encode(('utf-8'))).hexdigest()
                result['type'] = 'torrent'
                result['downloadid'] = None
                result['freeleech'] = i['free']
                result['download_client'] = None
                result['seeders'] = i['seed']
                results.append(result)

            except Exception as e:
                logging.error('Error parsing Torrentday json.', exc_info=True)
                continue
            continue


        logging.info('Found {} results from Torrentday.'.format(len(results)))

        return results

