from ..Crawler import Crawler

class HashmapCrawler(Crawler):
    """
    Hashmap crawler to store key/value data.
    """

    def __init__(self, data, parentCrawler=None):
        """
        Create a hashmap crawler.
        """
        assert isinstance(data, dict), "Invalid dict!"

        super(HashmapCrawler, self).__init__("hashmap", parentCrawler)
        self.setVar('data', data.copy())

    def __getitem__(self, key):
        """
        Return the value stored in the data for the given key.
        """
        return self.var('data')[key]

    def __setitem__(self, key, item):
        """
        Set a key and value inside of the data.
        """
        self.var('data')[key] = item

    def __delitem__(self, key):
        """
        Remove an item from the data.
        """
        del self.var('data')[key]

    def __len__(self):
        """
        Return the length of the data.
        """
        return len(self.var('data'))

    def __contains__(self, key):
        """
        Return a boolean telling if the input key is part of the data.
        """
        return key in self.var('data')

    def __iter__(self):
        """
        Return an iterator for the data.
        """
        return iter(self.var('data'))

    def __repr__(self):
        """
        Return a string representation of the crawler.
        """
        return 'Hashmap{}'.format(repr(self.var('data')))

    def clear(self):
        """
        Clear the data.
        """
        return self.var('data').clear()

    def items(self):
        """
        Return the data in (key, value) pairs.
        """
        return self.var('data').items()

    def keys(self):
        """
        Return the keys for the data.
        """
        return self.var('data').keys()

    def values(self):
        """
        Return the values for the data.
        """
        return self.var('data').values()

    def initializationData(self):
        """
        Define the data passed during the initialization of the crawler.
        """
        return self.var('data')

    @classmethod
    def test(cls, data=None, parentCrawler=None):
        """
        Tests if the data is dictionary.
        """
        return isinstance(data, dict)


Crawler.register(
    'hashmap',
    HashmapCrawler
)
