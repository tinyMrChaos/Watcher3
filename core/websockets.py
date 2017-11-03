import core


class WS(object):
    ''' Methods for websocket rpc

    Methods can return a json-compatible dict to send data to client.
    Return values should match the follow format for the given command:

        'set' > {'command': 'set',
                 'ref': <str>,
                 'data': <dict>
                 }
            'ref' is a string indicating the namespace in which to set data
                so that the client applies app.$refs.ref.key = value.
                If ref is None client applies data to app.key = value.
                Ref may be excluded and will default to None
            data is a dict containing key/val pairs to set in vue app.abs

        'notify' > {'command': 'notify',
                    'notification': {'title': <str>,
                                     'message': <str>,
                                     'type': <str>,
                                     'duration': <int>
                                     }
                    }
            Type may be one of None, 'success', 'info', 'warning', 'error'.
                May be excluded, defaults to None
            Duration is notif lifespan in ms. Use 0 to keep on screen until
                user closes. May be excluded, defaults to 4000.
            See at-ui docs for more notification properties.

    '''

    def movie_count(self):
        ''' Set movies_shown and movies_hidden '''
        total, hidden = core.sql.status_count(['Finished'])
        return {'command': 'set', 'ref': 'view', 'data': {'movies_hidden': hidden, 'movies_len': total - hidden}}

    def movie_page(self, sort_key, sort_direction, limit=50, offset=0):
        ''' set movies_slice to [<int> page num, <list> dicts of movies] '''
        p = (0 if offset == 0 else limit / offset) + 1
        movies = core.sql.get_user_movies(sort_key, sort_direction.upper(), limit=limit, offset=offset, hide_finished=core.CONFIG['Server']['hidefinished'])

        return {'command': 'set', 'ref': 'view', 'data': {'movies_splice': [p, movies]}}

    def qualities(self):
        r = [i for i in core.CONFIG['Quality']['Profiles'].keys()]

        return {'command': 'set', 'ref': 'view', 'data': {'qualities': r}}

    def search_results(self, imdbid, quality='Default'):
        results = core.sql.get_search_results(imdbid, quality=quality)

        if not core.CONFIG['Downloader']['Sources']['usenetenabled']:
            results = [res for res in results if res.get('type') != 'nzb']
        if not core.CONFIG['Downloader']['Sources']['torrentenabled']:
            results = [res for res in results if res.get('type') != 'torrent']

        return {'command': 'set', 'ref': 'status_modal', 'data': {'search_results': results}}
