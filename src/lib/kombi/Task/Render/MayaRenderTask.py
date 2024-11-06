import os
import subprocess
import tempfile
from ..External.MayaTask import MayaTask, MayaTaskError
from ...Crawler import Crawler
from ...Crawler.Fs import FsCrawler
from ...Crawler.Fs.Image import ImageCrawler

class MayaRenderTaskError(MayaTaskError):
    """Maya Render Task Error."""

class MayaRenderTask(MayaTask):
    """
    Render an image sequence in maya.
    """

    __renderExecutable = os.environ.get("KOMBI_MAYA_RENDER_EXECUTABLE", "render")
    __singletonRenderTask = None

    def __init__(self, *args, **kwargs):
        """
        Create a maya render task.
        """
        super(MayaRenderTask, self).__init__(*args, **kwargs)

        self.setMetadata("match.types", ('hashmap',))
        self.setMetadata('wrapper.name', 'python3')
        self.setMetadata('wrapper.options', {})

        # task input type
        self.setMetadata(
            "match.vars", {
                'dataLayout': "mayaRender"
            }
        )
        self.setMetadata("dispatch.split", True)

        # the settings below are translated and passed as options to the command-line
        # to the render executable (render --help)
        self.setOption(
            "settings",
            {
                "r": "sw",
                # it will render the renderLayers multiple times (power of two)
                "x": 1920,
                "y": 1080,
                "ard": 1.777,  # x/y
                "eaa": 0,  # maya software specific
                "depth": False,
                "alpha": True
            }
        )

        # this option disables the image-planes (iip). The reason
        # why this flag is not defined among the settings above is because
        # it does not require a value like everything else...
        self.setOption(
            'ignoreImagePlanes',
            True
        )

        # this options disables the background color for the cameras
        # (it does not seem to be provided as render-option)
        self.setOption(
            'ignoreCameraBackgroundColor',
            True
        )

        # the option below controls the motion blur
        self.setOption(
            'motionBlur',
            True
        )

        # required file path about the scene that will be used for
        # the rendering
        self.setOption("scene", "")

    def preRender(self):
        """
        For re-implementation: Callback executed before rendering.
        """
        from maya import cmds

        # making sure the camera does not  have a background color
        # (in case the background-color attribute is not locked)
        if self.option('ignoreCameraBackgroundColor'):
            for cameraShape in cmds.ls(type="camera", long=True):
                if not cmds.getAttr("{}.backgroundColor".format(cameraShape), lock=True):
                    cmds.delete(
                        "{}.backgroundColor".format(cameraShape),
                        channels=True
                    )
                    cmds.setAttr(
                        "{}.backgroundColor".format(cameraShape),
                        0.0,
                        0.0,
                        0.0,
                        type="double3"
                    )

    def postRender(self):
        """
        For re-implementation: Callback executed post rendering.
        """
        pass

    def preLayer(self):
        """
        For re-implementation: Callback executed pre-layer rendering.
        """
        pass

    def postLayer(self):
        """
        For re-implementation: Callback executed post-layer rendering.
        """
        pass

    def preFrame(self):
        """
        For re-implementation: Callback executed pre-frame rendering.
        """
        pass

    def postFrame(self):
        """
        For re-implementation: Callback executed post-frame rendering.
        """
        pass

    @classmethod
    def toRenderCrawlers(cls, outputImageCrawlers, startFrame=None, endFrame=None):
        """
        Return hashmap crawlers containing the render settings information used by this task.

        TODO: we want to have a specific application types to describe this information
        """
        result = []

        for crawlerGroup in Crawler.group(outputImageCrawlers):
            startFrame = startFrame if startFrame is not None else crawlerGroup[0].var('frame')
            endFrame = endFrame if endFrame is not None else crawlerGroup[-1].var('frame')

            for i, crawler in enumerate(crawlerGroup):
                currentFrame = startFrame + i

                assert isinstance(crawler, ImageCrawler), \
                    "Invalid output image crawler type!"

                result.append(
                    cls.__renderHashmapCrawler(
                        crawler,
                        currentFrame,
                        currentFrame
                    )
                )

        return result

    @classmethod
    def toInternal(cls):
        """
        Return the singleton render task used inside maya to trigger the callbacks.
        """
        if not cls.__singletonRenderTask:
            with open(os.environ['KOMBI_MAYA_RENDERTASK'], 'r') as f:
                cls.__singletonRenderTask = MayaTask.createFromJson(f.read())

        return cls.__singletonRenderTask

    def _perform(self):
        """
        Perform the task.
        """
        createdFiles = []

        # serializing the current task so it can be recreated again inside of the render executable
        seralizedTaskTempFile = tempfile.NamedTemporaryFile(
            mode='w',
            prefix='renderTask',
            suffix='.json',
            delete=False
        )
        env = dict(os.environ)
        env['KOMBI_MAYA_RENDERTASK'] = seralizedTaskTempFile.name

        seralizedTaskTempFile.write(self.toJson())
        seralizedTaskTempFile.close()

        for crawlerGroup in Crawler.group(self.crawlers()):
            startFrame = crawlerGroup[0]['settings']['s']
            endFrame = crawlerGroup[-1]['settings']['e']
            sceneFilePath = self.templateOption("scene", crawlerGroup[0])

            # making sure the scene is defined
            assert len(sceneFilePath), "scene option cannot be empty!"

            # building final render settings
            finalRenderSettings = dict(crawlerGroup[0]['settings'])
            for renderSettingName, renderSettingValue in self.templateOption('settings', crawlerGroup[0]).items():
                finalRenderSettings[renderSettingName] = renderSettingValue

            # registering callbacks
            for callbackPrefix in ('pre', 'post'):
                for callbackSuffix in ('Render', 'Layer', 'Frame'):
                    callbackName = '{}{}'.format(
                        callbackPrefix,
                        callbackSuffix
                    )
                    finalRenderSettings[callbackName] = 'python("from kombi.Task.Render import MayaRenderTask;MayaRenderTask.toInternal().{}()")'.format(
                        callbackName
                    )

            # building render command-line options
            args = [
                "-s {}".format(startFrame),
                "-e {}".format(endFrame)
            ]

            for optionName, optionValue in finalRenderSettings.items():
                if optionName in ('s', 'e'):
                    continue

                # converting boolean values to integer
                if isinstance(optionValue, bool):
                    optionValue = int(optionValue)

                # encapsuling string options under double quotes
                elif isinstance(optionValue, str):
                    optionValue = '"{}"'.format(
                        optionValue.replace('"', '\\"')
                    )

                args.append(
                    "-{} {}".format(
                        optionName,
                        optionValue
                    )
                )

            # executing render
            print(
                '{} {} "{}"'.format(
                    self.__renderExecutable,
                    ' '.join(args),
                    sceneFilePath
                )
            )

            p = subprocess.Popen(
                '{} {} "{}"'.format(
                    self.__renderExecutable,
                    ' '.join(args),
                    sceneFilePath
                ),
                shell=True,
                env=env
            )

            p.wait()

            if p.returncode:
                raise MayaRenderTaskError(
                    'Render process has retuned failure exit code: {}'.format(
                        p.returncode
                    )
                )

            # collecting output paths
            for crawler in crawlerGroup:
                createdFiles.append(
                    crawler['output']['fullPath']
                )

        return list(map(FsCrawler.createFromPath, createdFiles))

    @classmethod
    def __renderHashmapCrawler(cls, outputImageCrawler, startFrame, endFrame):
        """
        Return a hashmap crawler with the settings used to render this task.
        """
        assert isinstance(outputImageCrawler, ImageCrawler), "Invalid output image crawler type!"

        # maya render file name conventions: name, name.ext, name.#.ext, name.ext.#, name.#, name#.ext, name_#.ext
        # We don't want to support all those variations instead we only support the ones that make sense
        # for kombi
        supportedFormats = {
            'name.#.ext': 3,
            'name_#.ext': 7
        }
        sequenceFormat = 'name{}.ext'.format(
            outputImageCrawler.tag('group')[len(outputImageCrawler.var('name')):len(outputImageCrawler.var('name')) + 2]
        )
        assert sequenceFormat in supportedFormats, \
            "Non-supported image sequence format found it: {}".format(outputImageCrawler.var('fullPath'))

        # looking for tokens
        rd = os.path.dirname(outputImageCrawler.var('fullPath'))
        im = outputImageCrawler.var('name')
        if "<" in rd:
            splitPartIndex = rd.find("<")
            if splitPartIndex > 0:
                im = os.path.join(rd[splitPartIndex:], im)
                rd = rd[:splitPartIndex - 1]

        hashmapCrawler = Crawler.create(
            {
                'settings': {
                    'im': im,
                    'fnc': supportedFormats[sequenceFormat],
                    'of': outputImageCrawler.var('ext'),
                    'rd': rd,
                    'pad': outputImageCrawler.var('padding'),
                    's': startFrame,
                    'e': endFrame,
                    'b': 1
                },
                'output': {
                    'fullPath': outputImageCrawler.var('fullPath')
                }
            }
        )
        hashmapCrawler.setVar('dataLayout', 'mayaRender')
        hashmapCrawler.setTag('group', outputImageCrawler.tag('group'))
        hashmapCrawler.setVar(
            'fullPath',
            '{} {}-{}'.format(
                os.path.join(
                    hashmapCrawler['settings']['rd'],
                    hashmapCrawler['settings']['im']
                ),
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapCrawler


# registering task
MayaRenderTask.register(
    'mayaRender',
    MayaRenderTask
)
