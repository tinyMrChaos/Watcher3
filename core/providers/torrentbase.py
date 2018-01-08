import core


class TorrentProvider(object):
    """Plugins of this class convert plain text to HTML"""

    id = "baseprovider"
    name = "Base Provider"
    fields = {}

    @staticmethod
    def search(imdbid, term):
        pass

    @staticmethod
    def get_rss():
        pass

    @staticmethod
    def parse(data, imdbbid=None, term=None):
        pass

    @staticmethod
    def getConfig(name):
        if "Indexers" not in core.CONFIG:
            return None

        if "Config" not in core.CONFIG["Indexers"]:
            return None

        if name not in core.CONFIG["Indexers"]["Config"]:
            return None

        return core.CONFIG["Indexers"]["Config"][name]