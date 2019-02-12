import os
import json
from ..Task import Task
from ..ImageSequence import NukeScene

class MediaDelivery(NukeScene):
    """
    Create a new media for delivery.
    """

    def _perform(self):
        """
        Return a json file the media under the delivery folder.
        """
        # calling the super class that knows how to produce a media
        super(NukeScene, self)._perform()

        targetCrawler = self.crawlers()[0]
        mediaInfoJson = self.templateOption('mediaInfo', crawler=targetCrawler)
        clientShot = self.templateOption('clientShot', crawler=targetCrawler)
        targetFilePath = self.target(targetCrawler)

        # updating any existing file
        mediaInfo = {}
        if os.path.exists(mediaInfoJson):
            with open(mediaInfoJson) as jsonFile:
                mediaInfo = json.load(jsonFile)

        createdFilePath = targetFilePath[len(mediaInfoJson[:-4]):]
        createdFilePath = createdFilePath[:createdFilePath.find("/")]

        mediaInfo[createdFilePath] = targetCrawler.var('sgShot')
        mediaInfo[createdFilePath]['clientShot'] = clientShot
        mediaInfo[createdFilePath]['step'] = targetCrawler.var('step')
        mediaInfo[createdFilePath]['isMatte'] = targetCrawler.var('isMatte')
        # Tag the current shot/version combo so we can match matte renders with their comp in the delivery spreadsheet.
        mediaInfo[createdFilePath]['internalVersion'] = '{}_{}'.format(
            targetCrawler.var('shot'),
            targetCrawler.var('version')
        )

        with open(mediaInfoJson, 'w') as outfile:
            json.dump(mediaInfo, outfile, indent=4)

        result = [targetCrawler.createFromPath(mediaInfoJson)]

        if os.path.exists(targetFilePath):
            result.append(targetCrawler.createFromPath(targetFilePath))

        return result


# registering task
Task.register(
    'mediaDelivery',
    MediaDelivery
)
