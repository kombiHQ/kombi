import re
import os
import subprocess
from ...Element import ElementError
from .ImageElement import ImageElement

# check of openimageio is available
hasOpenImageIO = False
try:
    import OpenImageIO
    hasOpenImageIO = True
except ImportError:
    pass

class OiioElementReadFileError(ElementError):
    """Oiio Read File Error."""

class OiioElement(ImageElement):
    """
    Open image io element.
    """

    __oiiotoolExecutable = os.environ.get(
        'KOMBI_OIIOTOOL_EXECUTABLE',
        'oiiotool'
    )

    def var(self, name, *args, **kwargs):
        """
        Return var value using lazy loading implementation for width and height.
        """
        if name in ('width', 'height') and name not in self.varNames():
            # alternatively width and height information could come from the
            # parent directory element "1920x1080". For more details take a look
            # at "Directory" element.
            if hasOpenImageIO:
                imageInput = OpenImageIO.ImageInput.open(str(self.path()))

                # making sure the image has been successfully loaded
                if imageInput is None:
                    raise OiioElementReadFileError(
                        "Can't read information from file:\n{}".format(
                            self.path()
                        )
                    )

                spec = imageInput.spec()
                self.setVar('width', spec.full_width)
                self.setVar('height', spec.full_height)

                imageInput.close()
            else:
                self.__computeWidthHeight()

        return super(OiioElement, self).var(name, *args, **kwargs)

    def __computeWidthHeight(self):
        """
        Query width and height using oiiotool and set them as element variables.
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
        output, _ = process.communicate()
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

        if width is not None and height is not None:
            self.setVar('width', int(width))
            self.setVar('height', int(height))
