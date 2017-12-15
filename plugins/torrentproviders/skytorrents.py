import logging
import xml.etree.cElementTree as ET

import core
from core import proxy
from core.helpers import Url
from core.providers.providers import TorrentProvider

logging = logging.getLogger(__name__)


class SkyTorrents(TorrentProvider):
    ''' Does not supply rss feed -- backlog searches only. '''

    id = "skytorrents"
    name = "SkyTorrents"

    def search(self, imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on SkyTorrents for {}.'.format(imdbid))

        url = 'https://www.skytorrents.in/rss/all/ed/1/{}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.skytorrents.in') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return self.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('SkyTorrents search failed.', exc_info=True)
            return []

    def parse(self, xml, imdbid=None, term=None):
        logging.info('Parsing SkyTorrents results.')

        tree = ET.fromstring(xml)

        items = tree[0].findall('item')

        results = []
        for i in items:
            result = {}
            try:
                result['score'] = 0
                desc = i.find('description').text.split(' ')

                m = (1024 ** 2) if desc[-2] == 'MB' else (1024 ** 3)
                result['size'] = int(float(desc[-3]) * m)

                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i.find('title').text
                result['imdbid'] = imdbid
                result['indexer'] = 'SkyTorrents'
                result['info_link'] = i.find('guid').text
                result['torrentfile'] = i.find('link').text
                result['guid'] = result['torrentfile'].split('&')[0].split(':')[-1]
                result['type'] = 'torrent'
                result['download_client'] = None
                result['downloadid'] = None
                result['freeleech'] = 0

                result['seeders'] = desc[0]

                results.append(result)
            except Exception as e:
                logging.error('Error parsing SkyTorrents XML.', exc_info=True)
                continue

        logging.info('Found {} results from SkyTorrents.'.format(len(results)))
        return results

    def get_rss(self):
        return []