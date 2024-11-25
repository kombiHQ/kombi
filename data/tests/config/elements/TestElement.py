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
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a testElement file.
        """
        if not super(TestElement, cls).test(pathHolder, parentElement):
            return False

        name = pathHolder.baseName()
        return name.startswith('testSeq') or name.startswith("test_0")


# registering element
TestElement.register(
    'testElement',
    TestElement
)
