import core
from core import searcher, snatcher
import logging
import os

logging = logging.getLogger(__name__)

searcher = searcher.Searcher()
snatcher = snatcher.Snatcher()


class WS(object):
    ''' Methods for websocket rpc

        Methods can communicate back to client with the following commands
            using self from the inheriting class (core.app.WebSocketHandler).
            All values passed must be json-encodable.

        send_set(<dict>, ref=<str>)
            <dict> is a dict containing key/val pairs to set in vue app.$refs.ref
            'ref' is a string indicating the namespace in which to set data
                so that the client applies app.$refs.ref.key = value.
                If ref is None client applies data to app.key = value.
                Depth can be achieved by concatenating with periods so that
                when ref is 'parent.child' data is written to
                app.$refs.parent.$refs.child
                Ref may be excluded and will default to None

        send_notification(<dict>)
            <dict> is a dict matching elementui's notification format.
                http://element.eleme.io/#/en-US/component/notification

        self in methods refers to the WebSocketHandler instance defined in
            core.app, so that self.send, self.send_set, self.notify
            communicates with the client.
    '''

    def movie_count(self):
        ''' Set movies_shown and movies_hidden '''
        if core.CONFIG['Server']['hidefinished']:
            total, hidden = core.sql.status_count(['Finished'])
        else:
            total, hidden = core.sql.status_count()
        self.send_set({'movies_hidden': hidden, 'movies_len': total - hidden}, ref='view')

    def movie_page(self, sort_key, sort_direction, limit=50, offset=0):
        ''' set movies_slice to [<int> page num, <list> dicts of movies] '''
        p = (0 if offset == 0 else offset / limit) + 1
        movies = core.sql.get_user_movies(sort_key, sort_direction.upper(), limit=limit, offset=offset, hide_finished=core.CONFIG['Server']['hidefinished'])

        self.send_set({'movies_splice': [p, movies]}, ref='view')

    def qualities(self):
        r = [i for i in core.CONFIG['Quality']['Profiles'].keys()]
        self.send_set({'qualities': r}, ref='view')

    def search_results(self, imdbid, quality='Default'):
        results = core.sql.get_search_results(imdbid, quality=quality)

        if not core.CONFIG['Downloader']['Sources']['usenetenabled']:
            results = [res for res in results if res.get('type') != 'nzb']
        if not core.CONFIG['Downloader']['Sources']['torrentenabled']:
            results = [res for res in results if res.get('type') != 'torrent']

        self.send_set({'search_results': results}, ref='view.status_modal')

    def set_movie_settings(self, imdbid, managed, quality):
        '''
        imdbid (str):
        managed (bool): True if movie status is automatic, False is Disabled
        quality (str): quality profile to apply
        '''
        s = True

        if not core.sql.update('MOVIES', 'quality', quality, 'imdbid', imdbid):
            self.send_notification({'title': 'Error', 'message': 'Unable to write quality profile to database.', 'type': 'error'})
            s = False

        if managed:
            logging.info('Updating management to Automatic for {}.'.format(imdbid))
            new_status = core.manage.movie_status(imdbid, reset_disabled=True)
            if new_status:
                # TODO: Should this be called in movie_status method?
                self.send_all('update_movie', imdbid, {'status': new_status})
            else:
                self.send_notification({'title': 'Error', 'message': 'Unable to write status to database.', 'type': 'error'})
                s = False

        else:
            if core.sql.update('MOVIES', 'status', 'Disabled', 'imdbid', imdbid):
                self.send_all('update_movie', imdbid, {'status': 'Disabled'})
            else:
                self.send_notification({'title': 'Error', 'message': 'Unable to write status to database.', 'type': 'error'})
                s = False

        if s:
            self.send_notification({'title': 'Movie settings saved.', 'type': 'success'})

    def backlog_search(self, imdbid):
        ''' Search indexers for specific movie.
        imdbid (str): imdb id #

        Gets movie data from database and sends to searcher.search()
        '''

        movie = core.sql.get_movie_details('imdbid', imdbid)

        if movie:
            success = searcher.search(imdbid, movie['title'], movie['year'], movie['quality'])

            if success:
                results = core.sql.get_search_results(imdbid, movie['quality'])
                self.send_set({'search_results': results}, ref='view.status_modal')
            else:
                self.send_notification({'type': 'error', 'message': 'Unable to read database'})
        else:
            self.send_notification({'type': 'error', 'message': 'Unable to read database'})

    def trash_movie(self, imdbid, delete):
        ''' Removes movie
        imdbid (str): imdb id #
        delete (bool): delete movie file as well
        '''
        print(imdbid, delete)

        m = core.sql.get_movie_details('imdbid', imdbid)
        f = m.get('finished_file')
        title = m['title']
        if core.manage.remove_movie(imdbid):
            pass
        else:
            # TODO: send notification
            return

        if delete:
            try:
                logging.debug('Deleting file for {} -- {}'.format(imdbid, f))
                os.unlink(f)
            except Exception as e:
                logging.error('Unable to delete file {}'.format(f), exc_info=True)
                # TODO: Send notification
                return
        print('SENDING MESSAGE')
        self.send_all('send_message', {'message': '{} removed from library.'.format(title), 'type': 'info'})
        self.send_all('remove_movie', imdbid)

    def download_release(self, release, year):
        torrent_enabled = core.CONFIG['Downloader']['Sources']['torrentenabled']

        usenet_enabled = core.CONFIG['Downloader']['Sources']['usenetenabled']

        if release['type'] == 'nzb' and not usenet_enabled:
            self.send_notification({'type': 'warning', 'message': 'Release is NZB but no Usent client is enabled.'})
            return
        elif release['type'] in ('torrent', 'magnet') and not torrent_enabled:
            self.send_notification({'type': 'warning', 'message': 'Release is Torrent but no Usent client is enabled.'})
            return

        release['year'] = year
        if snatcher.download(release):
            self.send_notification({'type': 'success', 'message': '{} snatched.'.format(release['title'])})
            self.send_all('release_status', release['guid'], 'Snatched')
            return
        else:
            self.send_notification({'type': 'error', 'message': 'Unable to read database'})
            return
