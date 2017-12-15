import logging
from xml.etree.cElementTree import fromstring
from xmljson import gdata

import core
from core import proxy
from core.helpers import Url
from core.providers.providers import TorrentProvider
from core.providers.torrent import magnet

logging = logging.getLogger(__name__)


class TorrentDownloads(TorrentProvider):
    id = "torrentdownloads"
    name = "TorrentDownloads"

    def search(self, imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on TorrentDownloads for {}.'.format(imdbid))

        url = 'http://www.torrentdownloads.me/rss.xml?type=search&search={}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('http://www.torrentdownloads.me') is True:
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
            logging.error('TorrentDownloads search failed.', exc_info=True)
            return []

    def get_rss(self):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from TorrentDownloads.')

        url = 'http://www.torrentdownloads.me/rss2/last/4'

        try:
            if proxy_enabled and proxy.whitelist('http://www.torrentdownloads.me') is True:
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
            logging.error('TorrentDownloads RSS fetch failed.', exc_info=True)
            return []

    def parse(self, xml, imdbid=None, term=None):
        logging.info('Parsing TorrentDownloads results.')

        try:
            items = gdata.data(fromstring(xml))['rss']['channel']['item']
        except Exception as e:
            logging.error('Unexpected XML format from TorrentDownloads.', exc_info=True)
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
                result['indexer'] = 'TorrentDownloads'
                result['info_link'] = 'http://www.torrentdownloads.me{}'.format(i['link']['$t'])
                result['torrentfile'] = magnet(i['info_hash']['$t'])
                result['guid'] = i['info_hash']['$t']
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['freeleech'] = 0
                result['download_client'] = None
                result['seeders'] = int(i['seeders']['$t'])

                results.append(result)
            except Exception as e:
                logging.error('Error parsing TorrentDownloads XML.', exc_info=True)
                continue

        logging.info('Found {} results from TorrentDownloads.'.format(len(results)))
        return results
