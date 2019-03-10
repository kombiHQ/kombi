from .ExrRender import ExrRender

class NukeRender(ExrRender):
    """
    Custom crawler to parse information from a Nuke render.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a NukeRender object.
        """
        super(NukeRender, self).__init__(*args, **kwargs)

        parts = self.var("name").split("_")
        locationParts = parts[0].split("-")

        # Add the job var once job names on disk match job code names in shotgun
        self.setVar('seq', locationParts[1])
        self.setVar('shot', '-'.join(locationParts))
        self.setVar('step', parts[-5])
        self.setVar('renderName', parts[-4])
        self.setVar('output', parts[-3])
        self.setVar('versionName', parts[-2])
        self.setVar('version', int(parts[-2][1:]))

        # Keep track of if the render is a matte to use later in deliveries
        # \todo: Find a better way to detect if a render is a matte
        isMatte = 'matte' in self.var('output').lower()
        self.setVar('isMatte', int(isMatte))

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a shotgun nuke render.
        """
        if not super(NukeRender, cls).test(pathHolder, parentCrawler):
            return False

        renderType = pathHolder.baseName().split(".")[0].split("_")[-1]

        return renderType == "tk"


# registering crawler (backwards compatibility)
NukeRender.register(
    'tkNukeRender',
    NukeRender
)

# registering crawler
NukeRender.register(
    'nukeRender',
    NukeRender
)
