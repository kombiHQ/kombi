import kombi

class TestElement(kombi.Element.Fs.Image.ExrElement):
    """
    Test element for unit tests.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a TestElement object.
        """
        super(TestElement, self).__init__(*args, **kwargs)

        self.setVar('testVariable', self.var('name') == "testSeq")

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a testElement file.
        """
        if not super(TestElement, cls).test(path, parentElement):
            return False

        return path.name.startswith('testSeq') or path.name.startswith("test_0")


# registering element
TestElement.register(
    'testElement',
    TestElement
)
