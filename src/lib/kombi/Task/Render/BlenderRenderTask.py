import os
import sys
import subprocess
from ...Element import Element
from ..External.ExternalTask import ExternalTask


class BlenderRenderTask(ExternalTask):
    """
    Render the task nodes in blender.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a blender render task.
        """
        super(BlenderRenderTask, self).__init__(*args, **kwargs)

        self.setMetadata('match.types', ('hashmap',))
        self.setMetadata(
            'match.vars', {
                'dataLayout': 'blenderRender'
            }
        )
        self.setMetadata('dispatch.split', True)
        self.setMetadata('dispatch.renderFarm.pool', 'blender')

    @classmethod
    def toRenderElements(cls, blenderScenePath=None, startFrame=None, endFrame=None):
        """
        Return hashmap elements containing the write node information used by this task.
        """
        import bpy

        # blender global script variable
        blenderScenePath = blenderScenePath if blenderScenePath is not None else bpy.data.filepath
        startFrame = startFrame if startFrame is not None else bpy.context.scene.frame_start
        endFrame = endFrame if endFrame is not None else bpy.context.scene.frame_end

        result = []
        for i in range(startFrame, endFrame + 1):
            result.append(
                cls.__renderHashmapElement(
                    blenderScenePath,
                    i,
                    i
                )
            )

        return result

    def _perform(self):
        """
        Perform the task.
        """
        elements = self.elements()

        for elementGroup in Element.group(elements):
            startFrame = elementGroup[0]['startFrame']
            endFrame = elementGroup[-1]['endFrame']

            renderCommand = 'blender -b "{}" -s {} -e {} -F OPEN_EXR_MULTILAYER -a --python {}'.format(
                elementGroup[0].var('fullPathScene'),
                int(startFrame),
                int(endFrame),
                os.path.realpath(__file__)
            )
            sys.stdout.write(
                "{}\n".format(renderCommand)
            )

            env = dict(os.environ)

            if 'PYTHONHOME':
                del env['PYTHONHOME']

            if 'LD_LIBRARY_PATH':
                del env['LD_LIBRARY_PATH']

            p = subprocess.Popen(
                renderCommand,
                shell=True,
                env=env
            )
            p.wait()

            if p.returncode:
                raise Exception(
                    "Process returned error code: {}".format(
                        p.returncode
                    )
                )

        return self.elements()

    @classmethod
    def __renderHashmapElement(cls, blenderScenePath, startFrame, endFrame):
        """
        Return a hashmap element for the input write node start and end frame.
        """
        sceneBaseName = os.path.basename(blenderScenePath)
        hashmapElement = Element.create(
            {
                'name': sceneBaseName,
                'startFrame': startFrame,
                'endFrame': endFrame,
            }
        )
        hashmapElement.setVar('dataLayout', 'blenderRender')
        hashmapElement.setVar('baseName', sceneBaseName)
        hashmapElement.setVar('fullPathScene', blenderScenePath)
        hashmapElement.setTag('group', sceneBaseName)
        hashmapElement.setVar('startFrame', str(startFrame).zfill(10))
        hashmapElement.setVar('endFrame', str(endFrame).zfill(10))

        hashmapElement.setVar(
            'fullPath',
            '{} {}-{}'.format(
                blenderScenePath,
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapElement


# registering task
ExternalTask.register(
    'blenderRender',
    BlenderRenderTask
)

if __name__ == "__main__":
    import bpy

    prefs = bpy.context.preferences
    scene = bpy.context.scene
    scene.cycles.device = 'GPU'

    try:
        cprefs = prefs.addons['cycles'].preferences
        cprefs.compute_device_type = 'CUDA'
        cuda_devices, opencl_devices, optix_devices = cprefs.get_devices()
        for index, device in enumerate(cuda_devices):
            device.use = device.type in ('OPTIX', 'CUDA')

    except Exception:
        sys.stderr.write("Cycles device not available\n")
