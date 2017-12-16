import datetime
import logging

import core
from core import searchresults, snatcher, proxy
from core.providers import torrent, newznab
from core.rss import predb
from stringscore import liquidmetal as lm

logging = logging.getLogger(__name__)


class Searcher():

    def __init__(self):
        self.nn = newznab.NewzNab()
        self.score = searchresults.Score()
        self.predb = predb.PreDB()
        self.snatcher = snatcher.Snatcher()
        self.torrent = torrent.Torrent()

    def verify(self, movie, today=None):
        ''' Checks for verfied releases based on config
        movie (dict): movie info
        today (obj): datetime.datetime.today() object   <optional>

        Checks (in order):
            If verify releases is enabled
            If movie has a theatrical release date
            If theatrical release date is older than skip weeks per user config
            If predb verification -- check predb
            If home media release verification - check if release is in the past

            If all enabled conditions fail, return False

        Returns Bool
        '''
        today = today or datetime.datetime.today()

        if core.CONFIG['Search']['verifyreleases'] == '':
            verified = True
        elif not movie.get('release_date'):
            logging.info('{} does not have a theatrical release date, skipping verification check as Unverified.'.format(movie['title']))
            verified = False
        elif core.CONFIG['Search']['verifyreleasesskip'] and datetime.datetime.strptime(movie['release_date'], '%Y-%m-%d') + datetime.timedelta(days=7 * core.CONFIG['Search']['verifyreleasesskipweeks']) < today:
            logging.info('{} is older than {}, skipping verification check as Verified.'.format(movie['title'], core.CONFIG['Search']['verifyreleasesskipweeks']))
            verified = True

        elif core.CONFIG['Search']['verifyreleases'] == 'predb':
            if movie.get('predb') == 'found':
                verified = True
            else:
                verified = False

        elif core.CONFIG['Search']['verifyreleases'] == 'mediareleasedate':
            if not movie.get('predb') and movie.get('predb_backlog'):
                logging.debug('Resetting predb backlog status for unfound movie {} {}'.format(movie['title'], movie['year']))
                core.sql.update('MOVIES', 'predb_backlog', None, 'imdbid', movie['imdbid'])
            if not movie.get('media_release_date'):
                logging.info('{} does not yet have a home media release date.')
                verified = False
            else:
                media_release = datetime.datetime.strptime(movie['media_release_date'], '%Y-%m-%d')
                if media_release < today:
                    verified = True
                else:
                    verified = False
        else:
            verified = False

        if verified and movie['status'] == 'Waiting':
            logging.info('Verification criteria met for {} {}, setting status to Wanted'.format(movie['title'], movie['year']))
            core.sql.update('MOVIES', 'status', 'Wanted', 'imdbid', movie['imdbid'])
        elif not verified and movie['status'] not in ('Waiting', 'Disabled'):
            logging.info('Verified criteria not met for {} {}, resetting setting status to Waiting'.format(movie['title'], movie['year']))
            core.sql.update('MOVIES', 'status', 'Waiting', 'imdbid', movie['imdbid'])

        if verified:
            logging.info('{} passes verification checks, will include title in search.'.format(movie['title']))
        else:
            logging.info('{} does not pass verification checks, will ignore for now.'.format(movie['title']))

        return verified

    def _t_search_grab(self, movie):
        ''' Run verify/search/snatch chain
        movie (dict): movie to run search for

        Meant to be executed *IN ITS OWN THREAD* after adding a movie from user-input (ie api, search)
            so the main thread is not tied up.

        Does not return
        '''
        logging.info('Executing automatic search/grab for {}.'.format(movie['title']))

        imdbid = movie['imdbid']
        title = movie['title']
        year = movie['year']
        quality = movie['quality']

        if core.CONFIG['Search']['verifyreleases'] == 'predb':
            movie = self.predb.backlog_search(movie)

        if not self.verify(movie):
            return

        if core.CONFIG['Search']['searchafteradd'] and self.search(imdbid, title, year, quality) and core.CONFIG['Search']['autograb']:
            best_release = self.snatcher.best_release(movie)
            if best_release:
                self.snatcher.download(best_release)

    def search_all(self):
        ''' Searches for all movies
        Should never run in the main thread.
        Automatically runs as scheduled task.

        Searches only for movies that are Wanted, Found,
            or Finished -- if inside user-set date range.

        For each movie:
            If backlog status is 0:
                Executes self.search()
            Else:
                Parses rss feeds for matches

        If autograb is enabled calls snatcher.grab_all()

        Does not return
        '''
        logging.info('Executing search/grab for all movies.')

        today = datetime.datetime.today().replace(second=0, microsecond=0)

        movies = core.sql.get_user_movies()
        if not movies:
            return

        if core.CONFIG['Search']['verifyreleases'] == 'predb':
            self.predb.check_all()

        # backlog_movies = [i for i in movies if i['backlog'] != 1 and i['status'] is not 'Disabled' and self.verify(i, today=today)]
        backlog_movies = [i for i in movies if i['status'] is not 'Disabled' and self.verify(i, today=today)]
        if backlog_movies:
            logging.debug('Backlog movies: {}'.format(', '.join(i['title'] for i in backlog_movies)))
            for movie in backlog_movies:
                imdbid = movie['imdbid']
                title = movie['title']
                year = movie['year']
                quality = movie['quality']

                logging.info('Performing backlog search for {} {}.'.format(title, year))
                self.search(imdbid, title, year, quality)
                continue

        rss_movies = [i for i in self._get_rss_movies(movies) if self.verify(i, today=today)]
        if rss_movies:
            logging.info('Checking RSS feeds for {} movies.'.format(len(rss_movies)))
            self.rss_sync(rss_movies)

        if core.CONFIG['Search']['autograb']:
            self.snatcher.grab_all()
        return

    def search(self, imdbid, title, year, quality):
        ''' Executes backlog search for required movies
        imdbid (str): imdb identification number
        title (str): movie title
        year (str/int): year of movie release
        quality (str): name of quality profile

        Gets new search results from newznab providers.
        Pulls existing search results and updates new data with old. This way the
            found_date doesn't change and scores can be updated if the quality profile
            was modified since last search.

        Sends ALL results to searchresults.Score.score() to be (re-)scored and filtered.

        Checks if guid matches entries in MARKEDRESULTS and
            sets status if found. Default status Available.

        Finally stores results in SEARCHRESULTS

        Returns Bool if movie is found.
        '''

        logging.info('Performing backlog search for {} {}.'.format(title, year))
        proxy.create()

        results = []

        if core.CONFIG['Downloader']['Sources']['usenetenabled']:
            for i in self.nn.search_all(imdbid):
                results.append(i)
        if core.CONFIG['Downloader']['Sources']['torrentenabled']:
            for i in self.torrent.search_all(imdbid, title, year):
                results.append(i)

        proxy.destroy()

        old_results = core.sql.get_search_results(imdbid, quality)

        for old in old_results:
            if old['type'] == 'import':
                results.append(old)

        active_old_results = self.remove_inactive(old_results)

        # update results with old info if guids match
        for idx, result in enumerate(results):
            for old in active_old_results:
                if old['guid'] == result['guid']:
                    result.update(old)
                    results[idx] = result

        for idx, result in enumerate(results):
            results[idx]['resolution'] = self.get_source(result)

        scored_results = self.score.score(results, imdbid=imdbid)

        # sets result status based off marked results table
        marked_results = core.sql.get_marked_results(imdbid)
        if marked_results:
            for result in scored_results:
                if result['guid'] in marked_results:
                    result['status'] = marked_results[result['guid']]

        if not self.store_results(scored_results, imdbid, backlog=True):
            logging.error('Unable to store search results for {}'.format(imdbid))
            return False

        if not core.manage.movie_status(imdbid):
            logging.error('Unable to update movie status for {}'.format(imdbid))
            return False

        if not core.sql.update('MOVIES', 'backlog', '1', 'imdbid', imdbid):
            logging.error('Unable to flag backlog search as complete for {}'.format(imdbid))
            return False

        return True

    def rss_sync(self, movies):
        ''' Gets latests RSS feed from all indexers
        movies (list): dicts of movies to look for

        Gets latest rss feed from all supported indexers.

        Looks through rss for anything that matches a movie in 'movies'

        Only stores new results. If you need to update scores or old results
            force a backlog search.

        Finally stores results in SEARCHRESULTS

        Returns bool
        '''
        logging.info('Syncing indexer RSS feeds.')

        newznab_results = []
        torrent_results = []

        proxy.create()

        if core.CONFIG['Downloader']['Sources']['usenetenabled']:
            newznab_results = self.nn.get_rss()
        if core.CONFIG['Downloader']['Sources']['torrentenabled']:
            torrent_results = self.torrent.get_rss()

        proxy.destroy()

        for movie in movies:
            imdbid = movie['imdbid']
            title = movie['title']
            year = movie['year']

            logging.info('Parsing RSS for {} {}'.format(title, year))

            nn_found = [i for i in newznab_results if i['imdbid'] == imdbid]

            tor_found = [i for i in torrent_results if self._match_torrent_name(title, year, i['title'])]
            for idx, result in enumerate(tor_found):
                result['imdbid'] = imdbid
                tor_found[idx] = result

            results = nn_found + tor_found

            if not results:
                logging.info('Nothing found in RSS for {} {}'.format(title, year))
                continue

            # Ignore results we've already stored
            old_results = core.sql.get_search_results(imdbid)
            new_results = []
            for res in results:
                guid = res['guid']
                if all(guid != i['guid'] for i in old_results):
                    new_results.append(res)
                else:
                    continue

            logging.info('Found {} new results for {} {}.'.format(len(new_results), title, year))

            # Get source media and resolution
            for idx, result in enumerate(new_results):
                new_results[idx]['resolution'] = self.get_source(result)

            scored_results = self.score.score(new_results, imdbid=imdbid)

            if len(scored_results) == 0:
                logging.info('No acceptable results found for {}'.format(imdbid))
                continue

            if not self.store_results(scored_results, imdbid):
                return False

            if not core.manage.movie_status(imdbid):
                return False

        return True

    def remove_inactive(self, results):
        ''' Removes results from indexers no longer enabled
        results (list): dicts of search results

        Pulls active indexers from config, then removes any
            result that isn't from an active indexer.

        Does not filter Torrent results.
            Since torrent names don't always match their domain
            ie demonoid == dnoid.me, we can't filter out disabled torrent
            indexers since all would be removed

        Returns list of search results to keep
        '''

        logging.info('Filtering releases based on enabled newznab indexers.')

        active = []
        for i in core.CONFIG['Indexers']['NewzNab'].values():
            if i[2] is True:
                active.append(i[0])

        keep = []
        for result in results:
            if result['type'] in ('torrent', 'magnet', 'import'):
                keep.append(result)
            for indexer in active:
                if indexer in result['guid']:
                    keep.append(result)

        return keep

    def store_results(self, results, imdbid, backlog=False):
        ''' Stores search results in database.
        results (list): of dicts of search results
        imdbid (str): imdb identification number
        backlog (bool): if this call is from a backlog search       <optional - default False>

        Writes batch of search results to table.

        If storing backlog search results, will purge existing results. This is because
            backlog searches pull all existing results from the table and re-score them
            as to not change the found_date. Purging lets us write old results back in
            with updated scores and other info.

        Returns bool
        '''
        today = datetime.date.today()

        logging.info('{} results found for {}. Storing results.'.format(len(results), imdbid))

        BATCH_DB_STRING = []

        for result in results:
            if 'date_found' not in result:
                result['date_found'] = today
            BATCH_DB_STRING.append(result)

        if backlog:
            logging.info('Storing backlog search results -- purging existing results before writing to database.')
            core.sql.purge_search_results(imdbid=imdbid)

        if BATCH_DB_STRING:
            if core.sql.write_search_results(BATCH_DB_STRING):
                return True
            else:
                return False
        else:
            return True

    def get_source(self, result):
        ''' Parses release resolution and source from title.
        result (dict): individual search result info

        Returns str source based on core.SOURCES
        '''

        logging.info('Determining source media for {}'.format(result['title']))

        title = result['title']
        if any(i in title for i in ('4K', 'UHD', '2160P')):
            resolution = '4K'
        elif '1080' in title:
            resolution = '1080P'
        elif '720' in title:
            resolution = '720P'
        else:
            resolution = 'SD'

        delimiters = ('.', '_', ' ', '-', '+')
        for source, aliases in core.CONFIG['Quality']['Aliases'].items():
            for a in aliases:
                aliases_delimited = ['{}{}'.format(d, a) for d in delimiters]
                if any(i in title.lower() for i in aliases_delimited):
                    src = '{}-{}'.format(source, resolution)
                    logging.info('Source media determined as {}'.format(src))
                    return src

        src = 'Unknown-{}'.format(resolution)
        logging.info('Source media determined as {}'.format(src))
        return src

    def _get_rss_movies(self, movies):
        ''' Gets list of movies that we'll look in the rss feed for
        movies (list): dicts of movie rows in movies

        Filters movies so it includes movies where backlog == 1 and
            status is Wanted, Found, Snatched, or Finished
        If status is Finished checks if it is within the KeepSearching window

        Returns list of dicts of movies that require backlog search
        '''
        logging.info('Picking movies to look for in RSS feed.')

        today = datetime.datetime.today()
        keepsearching = core.CONFIG['Search']['keepsearching']
        keepsearchingdays = core.CONFIG['Search']['keepsearchingdays']
        keepsearchingdelta = datetime.timedelta(days=keepsearchingdays)

        rss_movies = []

        for i in movies:
            if i['backlog'] != 1:
                continue

            title = i['title']
            year = i['year']
            status = i['status']

            if status in ('Wanted', 'Found', 'Snatched'):
                rss_movies.append(i)
                logging.info('{} {} is {}. Will look for new releases in RSS feed.'.format(title, year, status))
            elif status == 'Finished' and keepsearching is True:
                if not i['finished_date']:
                    continue
                finished_date_obj = datetime.datetime.strptime(i['finished_date'], '%Y-%m-%d')
                if finished_date_obj + keepsearchingdelta >= today:
                    logging.info('{} {} was marked Finished on {}, will keep checking RSS feed for new releases.'.format(title, year, i['finished_date']))
                    rss_movies.append(i)
                continue

        return rss_movies

    def _match_torrent_name(self, movie_title, movie_year, torrent_title):
        ''' Checks if movie_title and torrent_title are a good match
        movie_title (str): title of movie
        movie_year (str/int): year of movie release
        torrent_title (str): title of torrent

        Helper function for rss_sync.

        Since torrent indexers don't supply imdbid like NewzNab does we have to compare
            the titles to find a match. This should be fairly accurate since a backlog
            search uses name and year to find releases.

        Checks if the year is in the title, promptly ignores it if the year is not found.
        Then does a fuzzy title match looking for 70+ token set ratio. Fuzzy match is done
            with movie title vs torrent name split on the year. This removes release
            information and matches just on the movie title in the torrent title.

        Returns bool on match success
        '''

        if movie_year not in torrent_title:
            return False
        else:
            movie = movie_title.replace(':', '.').replace(' ', '.').lower()
            torrent = torrent_title.replace(' ', '.').replace(':', '.').split(movie_year)[0].lower()
            match = lm.score(torrent, movie) * 100
            if match > 70:
                return True
            else:
                return False
