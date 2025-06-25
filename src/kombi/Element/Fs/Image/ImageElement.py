import re
import pathlib
from glob import glob
from ...Element import Element
from ..FileElement import FileElement

class ImageElement(FileElement):
    """
    Abstracted image element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create an image element.
        """
        super(ImageElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'image')

        # setting a image tag
        self.setVar('imageType', 'single')
        self.setTag('previewFilePath', self.var('filePath'))

        # setting icon
        self.setTag('icon', 'icons/elements/image.png')

        self.__computeImageSequence()

    def isSequence(self):
        """
        Return if path holder is holding a file that is part of a image sequence.
        """
        # first test is to test against the conventional image seq abc.0001.ext
        isImageSeq = self.__isStandardSequence()

        # second test is to check against the non-conventional image seq abc_0001.ext
        if not isImageSeq:
            isImageSeq = self.__isAmbiguousSequence()

        return isImageSeq
    
    def sequenceElements(self):
        """
        Returns all elements that are part of a sequence, sorted by frame number.
        """
        if not self.isSequence():
            return [self]

        groupFullPath = pathlib.Path(
            self.var('filePath')
        ).parent.joinpath(
            re.sub(r"#+", "*", self.tag('group'))
        ).as_posix()

        return sorted(
            map(lambda x: Element.create(pathlib.Path(x)), glob(groupFullPath)),
            key=lambda x: x.var('frame', 0)
        )

    def __computeImageSequence(self):
        """
        Compute the image sequence tags and vars.
        """
        nameParts = self.path().name.split(".")
        frame = None
        name = None
        frameSep = None
        if self.__isStandardSequence():
            frame = nameParts[-2]
            name = '.'.join(nameParts[:-2])
            frameSep = "."
        elif self.__isAmbiguousSequence():
            nameParts = nameParts[0].split("_")
            frame = nameParts[-1]
            name = '_'.join(nameParts[:-1])
            frameSep = "_"

        if frame is not None:
            self.setVar('imageType', 'sequence')
            self.setVar('name', name)
            self.setVar('frame', int(frame))
            self.setVar('padding', len(frame))

            # image sequence tag:
            # this information is used to group files, we don't necessary
            # need to obey the information about the padding from the file itself,
            # since the sequence can be unpadded.
            self.setTag(
                'group',
                '{0}{1}{2}.{3}'.format(
                    name,
                    frameSep,
                    '#' * len(frame),
                    self.var('ext')
                )
            )

            # sprintf group notation tag
            self.setTag(
                'groupSprintf',
                '{0}{1}{2}.{3}'.format(
                    name,
                    frameSep,
                    '%0{}d'.format(len(frame)),
                    self.var('ext')
                )
            )
        else:
            self.setTag('image', self.path().name)

    def __isStandardSequence(self):
        """
        Return a boolean telling if the element contains a standard image sequence.

        The element must follow the standard seq convention: abc.0001.ext
        """
        nameParts = self.path().name.split(".")
        isImageSeq = (len(nameParts) >= 3 and self.path().name.split(".")[-2].isdigit())

        return isImageSeq

    def __isAmbiguousSequence(self):
        """
        Return a boolean telling if the element contains an ambiguous image sequence.

        This element must follow the ambiguous seq convention: abc_0001.ext
        """
        nameParts = self.path().name.split(".")
        parts = nameParts[0].split("_")
        isImageSeq = False
        if len(parts) > 1:
            isImageSeq = (parts[-1].isdigit() and len(parts[-1]) >= 4)

        return isImageSeq
