from ...Crawler import CrawlerError
from .Image import Image

# check of openimageio is available
hasUnicodeSupport = True
hasOpenImageIO = False
try:
    import OpenImageIO
except ImportError:
    pass
else:
    hasOpenImageIO = True
    # check if oiio was built with support for unicode
    try:
        OpenImageIO.ImageInput.open(u'')
    except Exception:
        hasUnicodeSupport = False

class OiioReadFileError(CrawlerError):
    """Oiio Read File Error."""

class Oiio(Image):
    """
    Open image io crawler.
    """

    def var(self, name):
        """
        Return var value using lazy loading implementation for width and height.
        """
        if name in ('width', 'height') and name not in self.varNames():
            # alternatively width and height information could come from the
            # parent directory crawler "1920x1080". For more details take a look
            # at "Directory" crawler.
            if hasOpenImageIO:
                imageInput = OpenImageIO.ImageInput.open(self.supportedString(self.pathHolder().path()))

                # making sure the image has been successfully loaded
                if imageInput is None:
                    raise OiioReadFileError(
                        "Can't read information from file:\n{}".format(
                            self.pathHolder().path()
                        )
                    )

                spec = imageInput.spec()
                self.setVar('width', spec.full_width)
                self.setVar('height', spec.full_height)

                imageInput.close()

        return super(Oiio, self).var(name)

    @classmethod
    def supportedString(cls, text):
        """
        Return a string supported type in OIIO.
        """
        if not hasUnicodeSupport:
            text = str(text)

        return text
