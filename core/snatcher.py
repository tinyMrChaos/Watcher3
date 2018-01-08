import logging
import datetime
import urllib.parse
import core
import os
from core import plugins
from core.downloaders import deluge, qbittorrent, nzbget, sabnzbd, transmission, rtorrent, blackhole
from core.helpers import Torrent
logging = logging.getLogger(__name__)


class Snatcher():
    '''
    Handles snatching search results. This includes choosing the best result,
        retreiving the link, and sending it to the download client.

    Clarification notes:

    When snatching a torrent, the download id should *always* be the torrent hash.
    When snatching NZBs use the client-supplied download id if possible. If the client
        does not return a download id use None.

    '''

    def grab_all(self):
        ''' Grabs best result for all movies in library

        Automatically determines which movies can be grabbed or re-grabbed and
            executes self.best_release() to find best result then sends release
            dict to self.download()

        Returns bool (False is no movies to grab, True if any movies were attempted)
        '''
        logging.info('Running automatic snatcher for all movies.')

        today = datetime.datetime.today()
        keepsearching = core.CONFIG['Search']['keepsearching']
        keepsearchingscore = core.CONFIG['Search']['keepsearchingscore']
        keepsearchingdays = core.CONFIG['Search']['keepsearchingdays']
        keepsearchingdelta = datetime.timedelta(days=keepsearchingdays)

        movies = core.sql.get_user_movies()
        if not movies:
            return False
        for movie in movies:
            status = movie['status']
            if status == 'Disabled':
                logging.debug('{} is Disabled, skipping.'.format(movie['title']))
                continue
            title = movie['title']
            year = movie['year']

            if status == 'Found':
                logging.info('{} status is Found. Running automatic snatcher.'.format(title))
                best_release = self.best_release(movie)
                if best_release:
                    self.download(best_release)
                continue

            if status == 'Finished' and keepsearching is True:
                finished_date = movie['finished_date']
                if not finished_date:
                    continue
                finished_date_obj = datetime.datetime.strptime(finished_date, '%Y-%m-%d')
                if finished_date_obj + keepsearchingdelta >= today:
                    minscore = (movie.get('finished_score') or 0) + keepsearchingscore
                    logging.info('{} {} was marked Finished on {}. Checking for a better release (min score {}).'.format(title, year, finished_date, minscore))
                    best = self.best_release(movie, minscore=minscore)
                    if best:
                        self.download(best)
                    continue
                else:
                    continue
            else:
                continue
        logging.info('######### Automatic search/snatch complete #########')

    def best_release(self, movie, minscore=0):
        ''' Grabs the best scoring result that isn't 'Bad'
        movie (dict): movie info from local db
        minscore (int): minimum acceptable score for best release   <optional - default 0>

        Picks the best release that is available and above minscore threshold

        Returns dict of search result from local database
        '''

        logging.info('Selecting best release for {}'.format(movie['title']))

        try:
            imdbid = movie['imdbid']
            quality = movie['quality']
            year = movie['year']
            title = movie['title']
            release_date = movie['release_date']
        except Exception as e:
            logging.error('Invalid movie data.', exc_info=True)
            return {}

        search_results = core.sql.get_search_results(imdbid, quality)
        if not search_results:
            logging.warning('Unable to automatically grab {}, no results.'.format(imdbid))
            return {}

        # Filter out any results we don't want to grab
        search_results = [i for i in search_results if i['type'] != 'import']
        if not core.CONFIG['Downloader']['Sources']['usenetenabled']:
            search_results = [i for i in search_results if i['type'] != 'nzb']
        if not core.CONFIG['Downloader']['Sources']['torrentenabled']:
            search_results = [i for i in search_results if i['type'] not in ('torrent', 'magnet')]

        if not search_results:
            logging.warning('Unable to automatically grab {}, no results available for enabled download client.'.format(imdbid))
            return {}

        # Check if we are past the 'waitdays'
        today = datetime.datetime.today()
        release_weeks_old = (today - datetime.datetime.strptime(release_date, '%Y-%m-%d')).days / 7

        wait_days = core.CONFIG['Search']['waitdays']
        earliest_found = min([x['date_found'] for x in search_results])
        date_found = datetime.datetime.strptime(earliest_found, '%Y-%m-%d')
        if (today - date_found).days < wait_days:
            if core.CONFIG['Search']['skipwait'] and release_weeks_old > core.CONFIG['Search']['skipwaitweeks']:
                    logging.info('{} released {} weeks ago, skipping wait and grabbing immediately.'.format(title, release_weeks_old))
            else:
                logging.info('Earliest found result for {} is {}, waiting {} days to grab best result.'.format(imdbid, date_found, wait_days))
                return {}

        # Since seach_results comes back in order of score we can go through in
        # order until we find the first Available result and grab it.
        for result in search_results:
            result = dict(result)  # TODO why?
            status = result['status']
            result['year'] = year

            if status == 'Available' and result['score'] > minscore:
                logging.info('{} is best available result for {}'.format(result['title'], title))
                return result
            # if doing a re-search, if top ranked result is Snatched we have nothing to do.
            elif status in ('Snatched', 'Finished'):
                logging.info('Top-scoring release for {} has already been snatched.'.format(imdbid))
                return {}
            else:
                continue

        logging.warning('No Available results for {}.'.format(imdbid))
        return None

    def download(self, data):
        ''' Sends release to download client
        data (dict): search result from local database

        Sends data to helper method snatch_nzb or snatch_torrent based on download type

        Executes snatched plugins if successful

        Returns dict from helper method snatch_nzb or snatch_torrent
        '''
        logging.info('Sending {} to download client.'.format(data['title']))

        if data['type'] == 'import':
            return {'response': False, 'error': 'Cannot download imports.'}

        imdbid = data['imdbid']
        resolution = data['resolution']
        kind = data['type']
        info_link = urllib.parse.quote(data['info_link'], safe='')
        indexer = data['indexer']
        title = data['title']
        year = data['year']

        if data['type'] == 'nzb':
            if core.CONFIG['Downloader']['Sources']['usenetenabled']:
                response = self.snatch_nzb(data)
            else:
                return {'response': False, 'message': 'NZB submitted but nzb snatching is disabled.'}

        if data['type'] in ('torrent', 'magnet'):
            if core.CONFIG['Downloader']['Sources']['torrentenabled']:
                response = self.snatch_torrent(data)
            else:
                return {'response': False, 'message': 'Torrent submitted but torrent snatching is disabled.'}

        if response['response'] is True:
            download_client = response['download_client']
            downloadid = response['downloadid']

            plugins.snatched(title, year, imdbid, resolution, kind, download_client, downloadid, indexer, info_link)
            return response
        else:
            return response

    def snatch_nzb(self, data):
        ''' Sends nzb to download client
        data (dict): search result from local database

        Returns dict {'response': True, 'message': 'lorem impsum'}
        '''
        guid = data['guid']
        imdbid = data['imdbid']
        title = data['title']

        # If sending to SAB
        sab_conf = core.CONFIG['Downloader']['Usenet']['Sabnzbd']
        if sab_conf['enabled'] is True:
            logging.info('Sending nzb to Sabnzbd.')
            response = sabnzbd.Sabnzbd.add_nzb(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to Sabnzbd.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'SABnzbd'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to SABnzbd.', 'download_client': 'SABnzbd', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to NZBGET
        nzbg_conf = core.CONFIG['Downloader']['Usenet']['NzbGet']
        if nzbg_conf['enabled'] is True:
            logging.info('Sending nzb to NzbGet.')
            response = nzbget.Nzbget.add_nzb(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to NZBGet.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'NZBGet'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to NZBGet.', 'download_client': 'NZBGet', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

        # If sending to BLACKHOLE
        blackhole_conf = core.CONFIG['Downloader']['Usenet']['BlackHole']
        if blackhole_conf['enabled'] is True:
            d = blackhole_conf['directory']

            logging.info('Saving NZB as {}'.format(os.path.join(d, title)))
            response = blackhole.NZB.add_nzb(data)

            if response['response'] is True:
                logging.info('Successfully saved {} in BlackHole.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'BlackHole'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Saved to BlackHole.', 'download_client': 'BlackHole', 'downloadid': None}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

    def snatch_torrent(self, data):
        ''' Sends torrent or magnet to download client
        data (dict): search result from local database

        Returns dict {'response': True, 'message': 'lorem impsum'}
        '''
        guid = data['guid']
        imdbid = data['imdbid']
        title = data['title']
        kind = data['type']

        if urllib.parse.urlparse(guid).netloc:
            # if guid is not a url and not hash we'll have to get the hash now
            guid_ = Torrent.get_hash(data['torrentfile'])
            if guid_:
                core.sql.update('SEARCHRESULTS', 'guid', guid_, 'guid', guid)
                guid = guid_
            else:
                return {'response': False, 'error': 'Unable to get torrent hash from indexer.'}

        # If sending to Transmission
        transmission_conf = core.CONFIG['Downloader']['Torrent']['Transmission']
        if transmission_conf['enabled'] is True:
            logging.info('Sending {} to Transmission.'.format(kind))
            response = transmission.Transmission.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to Transmission.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'Transmission'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to Transmission.', 'download_client': 'Transmission', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

        # If sending to QBittorrent
        qbit_conf = core.CONFIG['Downloader']['Torrent']['QBittorrent']
        if qbit_conf['enabled'] is True:
            logging.info('Sending {} to QBittorrent.'.format(kind))
            response = qbittorrent.QBittorrent.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to QBittorrent.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'QBittorrent'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to QBittorrent.', 'download_client': 'QBittorrent', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

        # If sending to DelugeRPC
        delugerpc_conf = core.CONFIG['Downloader']['Torrent']['DelugeRPC']
        if delugerpc_conf['enabled'] is True:
            logging.info('Sending {} to DelugeRPC.'.format(kind))
            response = deluge.DelugeRPC.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to DelugeRPC.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'DelugeRPC'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to Deluge.', 'download_client': 'DelugeRPC', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

        # If sending to DelugeWeb
        delugeweb_conf = core.CONFIG['Downloader']['Torrent']['DelugeWeb']
        if delugeweb_conf['enabled'] is True:
            logging.info('Sending {} to DelugeWeb.'.format(kind))
            response = deluge.DelugeWeb.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to DelugeWeb.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'DelugeWeb'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to Deluge.', 'download_client': 'DelugeWeb', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

        # If sending to rTorrentSCGI
        rtorrent_conf = core.CONFIG['Downloader']['Torrent']['rTorrentSCGI']
        if rtorrent_conf['enabled'] is True:
            logging.info('Sending {} to rTorrent.'.format(kind))
            response = rtorrent.rTorrentSCGI.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to rTorrent.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'rTorrentSCGI'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to rTorrent.', 'download_client': 'rTorrentSCGI', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to rTorrentHTTP via ruTorrent plugin
        rtorrent_conf = core.CONFIG['Downloader']['Torrent']['rTorrentHTTP']
        if rtorrent_conf['enabled'] is True:
            logging.info('Sending {} to rTorrent.'.format(kind))
            response = rtorrent.rTorrentHTTP.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to rTorrent.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'rTorrentHTTP'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to rTorrent.', 'download_client': 'rTorrentHTTP', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response

        # If sending to BlackHole
        blackhole_conf = core.CONFIG['Downloader']['Torrent']['BlackHole']
        if blackhole_conf['enabled'] is True:
            d = blackhole_conf['directory']
            logging.info('Saving {} as {}'.format(kind, os.path.join(d, title)))
            response = blackhole.Torrent.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully saved {} in BlackHole.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'BlackHole'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                db_update = {'downloadid': response['downloadid'], 'download_client': 'BlackHole'}
                core.sql.update_multiple_values('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Saved to BlackHole.', 'download_client': 'BlackHole', 'downloadid': None}
                else:
                    return {'response': False, 'error': 'Could not mark search result as Snatched.'}
            else:
                return response
        else:
            return {'response': False, 'error': 'No download client enabled.'}

    def update_status_snatched(self, guid, imdbid):
        ''' Sets status to Snatched
        guid (str): guid for download link
        imdbid (str): imdb id #

        Updates MOVIES, SEARCHRESULTS, and MARKEDRESULTS to 'Snatched'

        Returns bool
        '''
        logging.info('Updating {} to Snatched.'.format(imdbid))

        if not core.manage.searchresults(guid, 'Snatched'):
            logging.error('Unable to update search result status to Snatched.')
            return False

        if not core.manage.markedresults(guid, 'Snatched', imdbid=imdbid):
            logging.error('Unable to store marked search result as Snatched.')
            return False

        if not core.manage.movie_status(imdbid):
            logging.error('Unable to update movie status to Snatched.')
            return False

        return True
