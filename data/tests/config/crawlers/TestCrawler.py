import kombi

class TestCrawler(kombi.Crawler.Fs.Image.Exr):
    """
    Test crawler for unit tests.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a TestCrawler object.
        """
        super(TestCrawler, self).__init__(*args, **kwargs)

        self.setVar('testVariable', self.var('name') == "testSeq")

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a testCrawler file.
        """
        if not super(TestCrawler, cls).test(pathHolder, parentCrawler):
            return False

        name = pathHolder.baseName()
        return name.startswith('testSeq') or name.startswith("test_0")


# registering crawler
TestCrawler.register(
    'testCrawler',
    TestCrawler
)
