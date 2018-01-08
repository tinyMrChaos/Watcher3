import logging
from xml.etree.cElementTree import fromstring
from xmljson import gdata

import core
from core import proxy
from core.helpers import Url
from core.providers.torrentbase import TorrentProvider

logging = logging.getLogger(__name__)

classname = "LimeTorrents"
class LimeTorrents(TorrentProvider):

    id = "limetorrents"
    name = "LimeTorrents"

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on LimeTorrents for {}.'.format(imdbid))

        url = 'https://www.limetorrents.cc/searchrss/{}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.limetorrents.cc') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return LimeTorrents.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('LimeTorrent search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from LimeTorrents.')

        url = 'https://www.limetorrents.cc/rss/16/'

        try:
            if proxy_enabled and proxy.whitelist('https://www.limetorrents.cc') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return LimeTorrents.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('LimeTorrent RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid=None, term=None):
        logging.info('Parsing LimeTorrents results.')

        try:
            items = gdata.data(fromstring(xml))['rss']['channel']['item']
        except Exception as e:
            logging.error('Unexpected XML format from LimeTorrents.', exc_info=True)
            return []

        results = []
        for i in items:
            result = {}
            try:
                result['score'] = 0
                result['size'] = i['size']['$t']
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i['title']['$t']
                result['imdbid'] = imdbid
                result['indexer'] = 'LimeTorrents'
                result['info_link'] = i['link']['$t']
                result['torrentfile'] = i['enclosure']['url']
                result['guid'] = result['torrentfile'].split('.')[1].split('/')[-1].lower()
                result['type'] = 'torrent'
                result['downloadid'] = None
                result['freeleech'] = 0
                result['download_client'] = None

                s = i['description']['$t'].split('Seeds: ')[1]
                seed_str = ''
                while s[0].isdigit():
                    seed_str += s[0]
                    s = s[1:]

                result['seeders'] = int(seed_str)

                results.append(result)
            except Exception as e:
                logging.error('Error parsing LimeTorrents XML.', exc_info=True)
                continue

        logging.info('Found {} results from LimeTorrents.'.format(len(results)))
        return results