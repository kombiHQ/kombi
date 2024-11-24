import re
import os
import subprocess
from ...InfoCrate import InfoCrateError
from .ImageInfoCrate import ImageInfoCrate

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

class OiioInfoCrateReadFileError(InfoCrateError):
    """Oiio Read File Error."""

class OiioInfoCrate(ImageInfoCrate):
    """
    Open image io infoCrate.
    """

    __oiiotoolExecutable = os.environ.get(
        'KOMBI_OIIOTOOL_EXECUTABLE',
        'oiiotool'
    )

    def var(self, name):
        """
        Return var value using lazy loading implementation for width and height.
        """
        if name in ('width', 'height') and name not in self.varNames():
            # alternatively width and height information could come from the
            # parent directory infoCrate "1920x1080". For more details take a look
            # at "Directory" infoCrate.
            if hasOpenImageIO:
                imageInput = OpenImageIO.ImageInput.open(self.supportedString(self.pathHolder().path()))

                # making sure the image has been successfully loaded
                if imageInput is None:
                    raise OiioInfoCrateReadFileError(
                        "Can't read information from file:\n{}".format(
                            self.pathHolder().path()
                        )
                    )

                spec = imageInput.spec()
                self.setVar('width', spec.full_width)
                self.setVar('height', spec.full_height)

                imageInput.close()
            else:
                self.__computeWidthHeight()

        return super(OiioInfoCrate, self).var(name)

    @classmethod
    def supportedString(cls, text):
        """
        Return a string supported type in OIIO.
        """
        if not hasUnicodeSupport:
            text = str(text)

        return text

    def __computeWidthHeight(self):
        """
        Query width and height using oiiotool and set them as infoCrate variables.
        """
        # Get width and height from movie using oiiotool
        cmd = '{} --info -v "{}"'.format(
            self.__oiiotoolExecutable,
            self.var('filePath')
        )

        # calling oiiotool
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ,
            shell=True
        )

        # capturing the output
        output, error = process.communicate()
        infoLines = output.decode('utf-8', errors='ignore').splitlines()
        if not infoLines:
            return

        width = None
        height = None

        # by default we use the resolution provided in the second line of
        # information of the file
        match = re.search(':[ ]*([0-9]+)[ ]*x[ ]*([0-9]+)', infoLines[1])
        if match:
            width = match.group(1)
            height = match.group(2)

        # however, in case there is the display size defined we use that instead
        for infoLine in infoLines[2:]:
            match = re.search('full/display size:[ ]*([0-9]+)[ ]*x[ ]*([0-9]+)', infoLine)
            if match:
                width = match.group(1)
                height = match.group(2)
                break

        if width is not None:
            self.setVar('width', int(width))
            self.setVar('height', int(height))
