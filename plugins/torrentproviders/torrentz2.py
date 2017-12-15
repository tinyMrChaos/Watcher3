import logging
from xml.etree.cElementTree import fromstring
from xmljson import gdata

import core
from core import proxy
from core.helpers import Url
from core.providers.providers import TorrentProvider
from core.providers.torrent import magnet

logging = logging.getLogger(__name__)


class Torrentz2(TorrentProvider):
    id = "torrentz2"
    name = "Torrentz2"

    def search(self, imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on Torrentz2 for {}.'.format(imdbid))

        url = 'https://www.torrentz2.eu/feed?f={}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.torrentz2.e') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return self.parse(response, imdbid, term)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Torrentz2 search failed.', exc_info=True)
            return []

    def get_rss(self):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from Torrentz2.')

        url = 'https://www.torrentz2.eu/feed?f=movies'

        try:
            if proxy_enabled and proxy.whitelist('https://www.torrentz2.e') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return self.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Torrentz2 RSS fetch failed.', exc_info=True)
            return []

    def parse(self, xml, imdbid=None, term=None):
        logging.info('Parsing Torrentz2 results.')

        try:
            items = gdata.data(fromstring(xml))['rss']['channel']['item']
        except Exception as e:
            logging.error('Unexpected XML format from Torrentz2.', exc_info=True)
            return []

        results = []
        for i in items:
            result = {}
            try:
                desc = i['description']['$t'].split(' ')
                hash_ = desc[-1]

                m = (1024 ** 2) if desc[2] == 'MB' else (1024 ** 3)

                result['score'] = 0
                result['size'] = int(desc[1]) * m
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i['title']['$t']
                result['imdbid'] = imdbid
                result['indexer'] = 'Torrentz2'
                result['info_link'] = i['link']['$t']
                result['torrentfile'] = magnet(hash_)
                result['guid'] = hash_
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['seeders'] = int(desc[4])
                result['download_client'] = None
                result['freeleech'] = 0

                results.append(result)
            except Exception as e:
                logging.error('Error parsing Torrentz2 XML.', exc_info=True)
                continue

        logging.info('Found {} results from Torrentz2.'.format(len(results)))
        return results
