from ...BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.Generic import HashmapCrawler

class HashmapCrawlerTest(BaseTestCase):
    """Test hashmap crawler."""

    def testCreation(self):
        """
        Test hashmap creation.
        """
        hashmap = Crawler.create({})
        assert(isinstance(hashmap, HashmapCrawler))
        self.assertEqual(len(hashmap), 0)

    def testData(self):
        """
        Test data passed to the constructor.
        """
        data = {
            'a': 1,
            'b': 2
        }

        hashmap = Crawler.create(data)
        self.assertEqual(len(hashmap), 2)
        self.assertEqual(hashmap['a'], 1)
        self.assertEqual(hashmap['b'], 2)

    def testRemoveData(self):
        """
        Test removing data in the hashmap.
        """
        data = {
            "a": 1
        }

        hashmap = Crawler.create(data)
        self.assertIn('a', hashmap)

        del hashmap['a']
        self.assertEqual(len(hashmap), 0)

    def testInsertData(self):
        """
        Test insert data in the hashmap.
        """
        hashmap = Crawler.create({})
        hashmap["a"] = 1

        self.assertEqual(len(hashmap), 1)
        self.assertIn('a', hashmap)
        self.assertEqual(hashmap['a'], 1)

    def testClearData(self):
        """
        Test clear the data in the hashmap.
        """
        hashmap = Crawler.create({"a": 1, "b": 2})
        hashmap.clear()

        self.assertEqual(len(hashmap), 0)

    def testItemsData(self):
        """
        Test items, keys and values for the data.
        """
        hashmap = Crawler.create({"a": 1})
        self.assertEqual(list(hashmap.items()), [("a", 1)])
        self.assertEqual(list(hashmap.keys()), ["a"])
        self.assertEqual(list(hashmap.values()), [1])

    def testStrRepresentation(self):
        """
        Test str representation of the hashmap.
        """
        hashmap = Crawler.create({})
        self.assertEqual(str(hashmap), "Hashmap{}")
