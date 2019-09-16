from ..Image import ExrCrawler

class ExrRenderCrawler(ExrCrawler):
    """
    Abstracted crawler used to detect renders.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Render object.
        """
        super(ExrRenderCrawler, self).__init__(*args, **kwargs)

        self.setVar('category', 'render')

        parts = self.var("name").split("_")
        self.setVar('renderType', parts[-1])
