import kombi

class TestInfoCrate(kombi.InfoCrate.Fs.Image.ExrInfoCrate):
    """
    Test infoCrate for unit tests.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a TestInfoCrate object.
        """
        super(TestInfoCrate, self).__init__(*args, **kwargs)

        self.setVar('testVariable', self.var('name') == "testSeq")

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a testInfoCrate file.
        """
        if not super(TestInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        name = pathHolder.baseName()
        return name.startswith('testSeq') or name.startswith("test_0")


# registering infoCrate
TestInfoCrate.register(
    'testInfoCrate',
    TestInfoCrate
)
