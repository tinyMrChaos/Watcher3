class TorrentProvider(object):
    """Plugins of this class convert plain text to HTML"""

    id = "baseprovider"
    name = "Base Provider"

    def search(self, imdbid, term):
        pass

    def get_rss(self):
        pass

    def parse(self, data, imdbbid=None, term=None):
        pass