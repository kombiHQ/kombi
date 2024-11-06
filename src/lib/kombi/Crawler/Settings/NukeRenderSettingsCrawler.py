from .SettingsCrawler import SettingsCrawler

class NukeRenderSettingsCrawler(SettingsCrawler):
    """
    Nuke render settings crawler.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a nuke render settings crawler.
        """
        super(NukeRenderSettingsCrawler, self).__init__(*args, **kwargs)
