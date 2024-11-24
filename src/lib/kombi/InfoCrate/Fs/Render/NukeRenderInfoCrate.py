from .ExrRenderInfoCrate import ExrRenderInfoCrate

class NukeRenderInfoCrate(ExrRenderInfoCrate):
    """
    Custom infoCrate to parse information from a Nuke render.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a NukeRenderInfoCrate object.
        """
        super(NukeRenderInfoCrate, self).__init__(*args, **kwargs)

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
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a shotgun nuke render.
        """
        if not super(NukeRenderInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        renderType = pathHolder.baseName().split(".")[0].split("_")[-1]

        return renderType == "tk"


# registering infoCrate (backwards compatibility)
NukeRenderInfoCrate.register(
    'tkNukeRenderInfoCrate',
    NukeRenderInfoCrate
)

# registering infoCrate
NukeRenderInfoCrate.register(
    'nukeRender',
    NukeRenderInfoCrate
)
