import os
import subprocess
import tempfile
from ..External.MayaTask import MayaTask, MayaTaskError
from ...Element import Element
from ...Element.Fs import FsElement
from ...Element.Fs.Image import ImageElement

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
    def toRenderElements(cls, outputImageElements, startFrame=None, endFrame=None):
        """
        Return hashmap elements containing the render settings information used by this task.

        TODO: we want to have a specific application types to describe this information
        """
        result = []

        for elementGroup in Element.group(outputImageElements):
            startFrame = startFrame if startFrame is not None else elementGroup[0].var('frame')
            endFrame = endFrame if endFrame is not None else elementGroup[-1].var('frame')

            for i, element in enumerate(elementGroup):
                currentFrame = startFrame + i

                assert isinstance(element, ImageElement), \
                    "Invalid output image element type!"

                result.append(
                    cls.__renderHashmapElement(
                        element,
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

        for elementGroup in Element.group(self.elements()):
            startFrame = elementGroup[0]['settings']['s']
            endFrame = elementGroup[-1]['settings']['e']
            sceneFilePath = self.templateOption("scene", elementGroup[0])

            # making sure the scene is defined
            assert len(sceneFilePath), "scene option cannot be empty!"

            # building final render settings
            finalRenderSettings = dict(elementGroup[0]['settings'])
            for renderSettingName, renderSettingValue in self.templateOption('settings', elementGroup[0]).items():
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
            for element in elementGroup:
                createdFiles.append(
                    element['output']['fullPath']
                )

        return list(map(FsElement.createFromPath, createdFiles))

    @classmethod
    def __renderHashmapElement(cls, outputImageElement, startFrame, endFrame):
        """
        Return a hashmap element with the settings used to render this task.
        """
        assert isinstance(outputImageElement, ImageElement), "Invalid output image element type!"

        # maya render file name conventions: name, name.ext, name.#.ext, name.ext.#, name.#, name#.ext, name_#.ext
        # We don't want to support all those variations instead we only support the ones that make sense
        # for kombi
        supportedFormats = {
            'name.#.ext': 3,
            'name_#.ext': 7
        }
        sequenceFormat = 'name{}.ext'.format(
            outputImageElement.tag('group')[len(outputImageElement.var('name')):len(outputImageElement.var('name')) + 2]
        )
        assert sequenceFormat in supportedFormats, \
            "Non-supported image sequence format found it: {}".format(outputImageElement.var('fullPath'))

        # looking for tokens
        rd = os.path.dirname(outputImageElement.var('fullPath'))
        im = outputImageElement.var('name')
        if "<" in rd:
            splitPartIndex = rd.find("<")
            if splitPartIndex > 0:
                im = os.path.join(rd[splitPartIndex:], im)
                rd = rd[:splitPartIndex - 1]

        hashmapElement = Element.create(
            {
                'settings': {
                    'im': im,
                    'fnc': supportedFormats[sequenceFormat],
                    'of': outputImageElement.var('ext'),
                    'rd': rd,
                    'pad': outputImageElement.var('padding'),
                    's': startFrame,
                    'e': endFrame,
                    'b': 1
                },
                'output': {
                    'fullPath': outputImageElement.var('fullPath')
                }
            }
        )
        hashmapElement.setVar('dataLayout', 'mayaRender')
        hashmapElement.setTag('group', outputImageElement.tag('group'))
        hashmapElement.setVar(
            'fullPath',
            '{} {}-{}'.format(
                os.path.join(
                    hashmapElement['settings']['rd'],
                    hashmapElement['settings']['im']
                ),
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapElement


# registering task
MayaRenderTask.register(
    'mayaRender',
    MayaRenderTask
)
