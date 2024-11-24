from ...BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.Generic import HashmapInfoCrate

class HashmapInfoCrateTest(BaseTestCase):
    """Test hashmap infoCrate."""

    def testCreation(self):
        """
        Test hashmap creation.
        """
        hashmap = InfoCrate.create({})
        assert isinstance(hashmap, HashmapInfoCrate)
        self.assertEqual(len(hashmap), 0)

    def testData(self):
        """
        Test data passed to the constructor.
        """
        data = {
            'a': 1,
            'b': 2
        }

        hashmap = InfoCrate.create(data)
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

        hashmap = InfoCrate.create(data)
        self.assertIn('a', hashmap)

        del hashmap['a']
        self.assertEqual(len(hashmap), 0)

    def testInsertData(self):
        """
        Test insert data in the hashmap.
        """
        hashmap = InfoCrate.create({})
        hashmap["a"] = 1

        self.assertEqual(len(hashmap), 1)
        self.assertIn('a', hashmap)
        self.assertEqual(hashmap['a'], 1)

    def testClearData(self):
        """
        Test clear the data in the hashmap.
        """
        hashmap = InfoCrate.create({"a": 1, "b": 2})
        hashmap.clear()

        self.assertEqual(len(hashmap), 0)

    def testItemsData(self):
        """
        Test items, keys and values for the data.
        """
        hashmap = InfoCrate.create({"a": 1})
        self.assertEqual(list(hashmap.items()), [("a", 1)])
        self.assertEqual(list(hashmap.keys()), ["a"])
        self.assertEqual(list(hashmap.values()), [1])

    def testStrRepresentation(self):
        """
        Test str representation of the hashmap.
        """
        hashmap = InfoCrate.create({})
        self.assertEqual(str(hashmap), "Hashmap{}")
