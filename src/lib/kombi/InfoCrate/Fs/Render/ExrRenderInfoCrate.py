from ..Image import ExrInfoCrate

class ExrRenderInfoCrate(ExrInfoCrate):
    """
    Abstracted infoCrate used to detect renders.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Render object.
        """
        super(ExrRenderInfoCrate, self).__init__(*args, **kwargs)

        self.setVar('category', 'render')

        parts = self.var("name").split("_")
        self.setVar('renderType', parts[-1])
