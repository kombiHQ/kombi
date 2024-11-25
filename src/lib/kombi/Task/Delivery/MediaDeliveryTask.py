import os
import json
from ..Task import Task
from ..ImageSequence import NukeTemplateTask

class MediaDeliveryTask(NukeTemplateTask):
    """
    Create a new media for delivery.
    """

    def _perform(self):
        """
        Return a json file the media under the delivery folder.
        """
        # calling the super class that knows how to produce a media
        super(NukeTemplateTask, self)._perform()

        targetElement = self.elements()[0]
        mediaInfoJson = self.templateOption('mediaInfo', element=targetElement)
        clientShot = self.templateOption('clientShot', element=targetElement)
        targetFilePath = self.target(targetElement)

        # updating any existing file
        mediaInfo = {}
        if os.path.exists(mediaInfoJson):
            with open(mediaInfoJson) as jsonFile:
                mediaInfo = json.load(jsonFile)

        createdFilePath = targetFilePath[len(mediaInfoJson[:-4]):]
        createdFilePath = createdFilePath[:createdFilePath.find("/")]

        mediaInfo[createdFilePath] = targetElement.var('sgShot')
        mediaInfo[createdFilePath]['clientShot'] = clientShot
        mediaInfo[createdFilePath]['step'] = targetElement.var('step')
        mediaInfo[createdFilePath]['isMatte'] = targetElement.var('isMatte')
        # Tag the current shot/version combo so we can match matte renders with their comp in the delivery spreadsheet.
        mediaInfo[createdFilePath]['internalVersion'] = '{}_{}'.format(
            targetElement.var('shot'),
            targetElement.var('version')
        )

        with open(mediaInfoJson, 'w') as outfile:
            json.dump(mediaInfo, outfile, indent=4)

        result = [targetElement.createFromPath(mediaInfoJson)]

        if os.path.exists(targetFilePath):
            result.append(targetElement.createFromPath(targetFilePath))

        return result


# registering task
Task.register(
    'mediaDelivery',
    MediaDeliveryTask
)
