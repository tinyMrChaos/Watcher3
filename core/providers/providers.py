import core


class TorrentProvider(object):
    """Plugins of this class convert plain text to HTML"""

    id = "baseprovider"
    name = "Base Provider"
    fields = {}

    def search(self, imdbid, term):
        pass

    def get_rss(self):
        pass

    def parse(self, data, imdbbid=None, term=None):
        pass

    def getConfig(self, name):
        if "Indexers" not in core.CONFIG:
            return None

        if "Config" not in core.CONFIG["Indexers"]:
            return None

        if self.id not in core.CONFIG["Indexers"]["Config"]:
            return None

        return core.CONFIG["Indexers"]["Config"][self.id]