import os
import traceback
import platform
import subprocess
from pathlib import Path
from kombi.Element.Fs.Image import ImageElement
from kombi.Element.Fs.Video import VideoElement
from kombi.Element.Fs.Audio import AudioElement
from kombi.Task.Desktop.LaunchWithDefaultApplicationTask import LaunchWithDefaultApplicationTask
from kombi.Element import Element
from kombi.Task import Task
from ..Resource import Resource
from Qt import QtCore, QtGui, QtWidgets

class ElementViewerWidget(QtWidgets.QLabel):
    """
    This widget is designed to display media element types (image, movie and audio).

    It functions by detecting the preview tag associated with the element and
    loading the corresponding content into the viewer for display.
    """
    __loadingSize = 80

    def __init__(
        self,
        elements,
        previewTag='previewFilePath',
        backgroundColor='#000000',
        centerAlignment=True
    ):
        """
        Create an ElementViewerWidget object.
        """
        super(ElementViewerWidget, self).__init__()
        self.setMouseTracking(True)

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setAlignment(QtCore.Qt.AlignCenter if centerAlignment else QtCore.Qt.AlignHCenter)

        self.__loadMediaThread = LoadMediaThread()
        self.__loading = False
        self.__currentElement = None
        self.__loadMediaThread.loadedSignal.connect(self.__finishedLoad)
        self.__loadingMovie = Resource.qmovie("icons/loading.gif")
        loadingSize = QtCore.QSize(self.__loadingSize, self.__loadingSize)
        self.__loadingMovie.setScaledSize(loadingSize)
        self.__loadingIndicator = QtWidgets.QLabel()
        self.__loadingIndicator.setMovie(self.__loadingMovie)
        self.__loadingIndicator.resize(loadingSize)
        self.__loadingIndicator.setVisible(False)

        self.__slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.__slider.setObjectName('viewer')
        self.__slider.setParent(self)
        self.__slider.setTickInterval(1)
        self.__loadingIndicator.setParent(self)

        self.__slider.valueChanged.connect(self.__onSliderChange)
        self.setStyleSheet('QLabel {{background-color: {}}}'.format(backgroundColor))

        self.__setPreviewTag(previewTag)
        self.setElements(elements)

    def previewTag(self):
        """
        Return the name of the tag used for preview.
        """
        return self.__previewTag

    def mouseMoveEvent(self, ev):
        """
        Adjust the element sequence based on the mouse position.
        """
        self.__slider.setValue(
            QtWidgets.QStyle.sliderValueFromPosition(
                self.__slider.minimum(),
                self.__slider.maximum(),
                ev.x(),
                self.__slider.width()
            )
        )

    def mouseReleaseEvent(self, ev):
        """
        Triggered when the user has clicked on the viewer.
        """
        if self.__elements and ev.button() == QtCore.Qt.LeftButton:
            task = Task.create('elementViewerLaunch')
            task.add(self.__currentElement)
            task.output()

    def resizeEvent(self, event):
        """
        Reset the current display.
        """
        self.__reset()
        self.__onSliderChange(self.__slider.value())

    def setElements(self, elements):
        """
        Set the elements that should be loaded.
        """
        self.__reset()
        self.__elements = list(sorted(elements, key=lambda x: x.var('fullPath')))
        self.__update()

    def __update(self):
        """
        Update the slider information.
        """
        self.setCursor(QtCore.Qt.ArrowCursor)
        if self.__elements:
            self.__slider.setMaximum(len(self.__elements) - 1)
            self.__slider.setValue(0)
            self.__onSliderChange(0)
            self.setCursor(QtCore.Qt.PointingHandCursor)

    def __reset(self):
        """
        Reset the display.
        """
        self.setPixmap(QtGui.QPixmap())
        self.__currentElement = None
        self.__loadingIndicator.setVisible(False)
        self.__loadingMovie.stop()
        self.__slider.setVisible(False)
        self.setToolTip('')
        self.setPixmap(Resource.pixmap("icons/noPreviewAvailable.png"))

    def __finishedLoad(self, element, qimage):
        """
        Slot called when the thread finishes loading the image.
        """
        self.__loading = False
        self.__loadingIndicator.setVisible(False)
        self.__loadingMovie.stop()

        if not qimage.isNull():
            pixmap = QtGui.QPixmap.fromImage(qimage)
        else:
            pixmap = Resource.pixmap("icons/noPreviewAvailable.png")

        self.setPixmap(pixmap)
        self.setToolTip(os.path.basename(element.tag(self.previewTag(), '')))
        self.__currentElement = element

        self.__slider.setFixedWidth(self.width())

        height = self.pixmap().height()
        if self.alignment() == QtCore.Qt.AlignCenter:
            height /= 2
            height += self.height() / 2

        self.__slider.move(0, int(height) - 10)
        self.__slider.setVisible(len(self.__elements) > 1)

    def __showLoadingIndicator(self):
        """
        Triggered after a few ms to display the loading indicator in case the element has not being loaded yet.
        """
        if not self.__loading:
            return
        self.__loadingMovie.start()
        self.__loadingIndicator.setVisible(True)

    def __onSliderChange(self, value):
        """
        Slot called when the slider is changed.
        """
        if not self.__elements:
            self.__reset()
            return

        element = self.__elements[value]
        self.__loadMediaThread.setElement(element, self.width(), self.height())
        self.__loadingIndicator.move(
            int((self.width() - self.__loadingSize) / 2),
            int((self.height() - self.__loadingSize) / 2)
        )

        # in case the data is loaded under 250ms we don't even bother showing the
        # loading indicator
        self.__loading = True
        QtCore.QTimer.singleShot(250, self.__showLoadingIndicator)

        self.__loadMediaThread.start()

    def __setPreviewTag(self, tagName):
        """
        Sets the name of the tag that should be used by the viewer.
        """
        self.__previewTag = tagName

class LoadMediaThread(QtCore.QThread):
    """
    Thread to load the file in background.
    """
    loadedSignal = QtCore.Signal(object, QtGui.QImage)
    __elementCache = {}
    __ffmpegExecutable = os.environ.get('KOMBI_FFMPEG_EXECUTABLE', 'ffmpeg')

    def __init__(self, element=None, previewTag='previewFilePath'):
        """
        Create a LoadMediaThread object.
        """
        super(LoadMediaThread, self).__init__()
        self.setElement(element)
        self.setPreviewTag(previewTag)
        self.__abort = False

    def setPreviewTag(self, tagName):
        """
        Sets the name of the tag that should be loaded.
        """
        self.__previewTag = tagName

    def previewTag(self):
        """
        Return the name of the tag used to load the media.
        """
        return self.__previewTag

    def setElement(self, element, width=None, height=None):
        """
        Set the full path that should be loaded by the thread.
        """
        self.__element = element
        self.__width = width
        self.__height = height

    def run(self):
        """
        Implement the thread execution.
        """
        resultImage = QtGui.QImage()

        loadElement = self.__element
        previewTagValue = self.__element.tag(self.previewTag(), None)
        if previewTagValue and os.path.exists(previewTagValue):
            try:
                loadElement = Element.create(Path(previewTagValue))
            except Exception:
                traceback.print_exc()

        if loadElement.var('filePath') in self.__elementCache:
            resultImage = self.__elementCache[loadElement.var('filePath')]
        else:
            if isinstance(loadElement, ImageElement):
                resultImage = QtGui.QImage(loadElement.var('filePath'))
                if resultImage.isNull():
                    resultImage = self.__ffmpegFetchImage(loadElement.var('filePath'))
            elif isinstance(loadElement, (VideoElement, AudioElement)):
                resultImage = self.__ffmpegFetchImage(loadElement.var('filePath'))
            self.__elementCache[loadElement.var('filePath')] = resultImage

        if not resultImage.isNull() and self.__width is not None and self.__height is not None:
            resultImage = resultImage.scaled(
                self.__width,
                self.__height,
                QtCore.Qt.KeepAspectRatio
            )

        if not self.__abort:
            self.loadedSignal.emit(self.__element, resultImage)

    def __ffmpegFetchImage(self, filePath):
        """
        Load a frame from the video/image (raw formats) or generate a waveform from the input audio.
        """
        extraArgs = []
        if isinstance(self.__element, AudioElement):
            extraArgs += [
                '-filter_complex',
                'showwavespic=colors=green|yellow'
            ]

        ffmpegCommand = [
            self.__ffmpegExecutable,
            "-v",
            "quiet",
            "-i",
            filePath,
            *extraArgs,
            "-vframes",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-"
        ]

        extraArgs = {}
        if platform.system().lower() == 'windows':
            extraArgs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(ffmpegCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **extraArgs)
        stdout, _ = process.communicate()

        if process.returncode == 0:
            return QtGui.QImage.fromData(QtCore.QByteArray(stdout))

        return QtGui.QImage()

    def __del__(self):
        """
        We need to wait for the thread to be finished before destroying it.
        """
        self.__abort = True
        try:
            if self.isRunning():
                self.quit()
                self.wait()

        # We intentionally ignore any runtime errors that may occur at this point, as
        # they could be caused by the internal C++ object already being deleted. For example:
        # RuntimeError: Internal C++ object (LoadMediaThread) has already been deleted.
        except RuntimeError:
            pass


# This is registered as a custom task, enabling you to override it with a
# different task if you need a custom procedure or behavior.
Task.register('elementViewerLaunch', LaunchWithDefaultApplicationTask)
