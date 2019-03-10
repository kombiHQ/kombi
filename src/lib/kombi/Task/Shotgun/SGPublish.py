import os
import getpass
import tempfile
from ..Task import Task
from ...TaskWrapper import TaskWrapper
from ...Crawler import Crawler
from ...Crawler.Fs.FsPath import FsPath
from ...Crawler.Fs.Image import Image

class SGPublish(Task):
    """
    Generic Shotgun publish task for data created by the CreateVersion task.
    """

    __shotgunUrl = os.environ.get('KOMBI_SHOTGUN_URL', '')
    __shotgunScriptName = os.environ.get('KOMBI_SHOTGUN_SCRIPTNAME', '')
    __shotgunApiKey = os.environ.get('KOMBI_SHOTGUN_APIKEY', '')

    def __init__(self, *args, **kwargs):
        """
        Create a RenderPublish object.
        """
        super(SGPublish, self).__init__(*args, **kwargs)

        # setting default options
        self.setOption("url", self.__shotgunUrl)
        self.setOption("scriptName", self.__shotgunScriptName)
        self.setOption("apiKey", self.__shotgunApiKey)

        self.__publishData = {}

    def _perform(self):
        """
        Perform the task.
        """
        import shotgun_api3

        # creating a singleton session object
        sg = shotgun_api3.Shotgun(
            self.option('url'),
            script_name=self.option('scriptName'),
            api_key=self.option('apiKey')
        )

        # Source crawler is a json crawler that points to published data
        sourceCrawler = self.crawlers()[0]
        filePath = self.target(sourceCrawler) if self.target(sourceCrawler) else sourceCrawler.var('filePath')

        self.__publishData["path"] = {"local_path": filePath}
        self.__publishData["description"] = self.templateOption('comment', crawler=sourceCrawler)
        self.__publishData["version_number"] = sourceCrawler.var('version')

        if "_sgTask" in sourceCrawler.varNames():
            self.__publishData["task"] = sourceCrawler.var("_sgTask")

        publishName = self.templateOption('publishName', crawler=sourceCrawler)
        self.__publishData["name"] = publishName
        self.__publishData["code"] = publishName

        self.__linkData(sg)
        self.__sgFileType(sg)
        self.__sgUser(sg)

        sgPublishFile = sg.create("PublishedFile", self.__publishData)
        self.__makeThumbnail(sgPublishFile, sg)
        self.__makeDaily(sgPublishFile, sg)

        # this task does not return any crawlers as result
        return []

    def __linkData(self, sg):
        """
        Find the data that needs to be linked to the publish in Shotgun.
        """
        sourceCrawler = self.crawlers()[0]

        project = sg.find_one('Project', [['name', 'is', sourceCrawler.var('job')]])
        self.__publishData['project'] = project

        if "shot" in sourceCrawler.varNames() or "assetName" in sourceCrawler.varNames():
            varName = "shot" if "shot" in sourceCrawler.varNames() else "assetName"
            varType = "Shot" if "shot" in sourceCrawler.varNames() else "Asset"

            filters = [
                ['code', 'is', sourceCrawler.var(varName)],
                ['project', 'is', project]
            ]
            entityData = sg.find(varType, filters)
            if len(entityData) != 1:
                raise Exception(
                    "[SGPublish] Cannot find unique {} {} in project {}. Skip Publish.".format(
                        varName,
                        sourceCrawler.var(varName),
                        sourceCrawler.var('job')
                    )
                )
            self.__publishData['entity'] = entityData[0]
        else:
            self.__publishData['entity'] = project

    def __sgFileType(self, sg):
        """
        Find the shotgun file type for the publish. Create it in Shotgun if it does not already exist.
        """
        publishedFileType = self.option('publishedFileType')
        sgFileType = sg.find_one('PublishedFileType', filters=[["code", "is", publishedFileType]])
        if not sgFileType:
            # create a published file type on the fly
            sgFileType = sg.create("PublishedFileType", {"code": publishedFileType})
        self.__publishData["published_file_type"] = sgFileType

    def __sgUser(self, sg):
        """
        Find the shotgun user information for the publish.
        """
        fields = ["id", "type", "email", "login", "name", "image"]
        user = os.environ.get("KOMBI_USER", getpass.getuser()),
        self.__publishData["created_by"] = sg.find_one("HumanUser", filters=[["login", "is", user]], fields=fields)

    def __makeThumbnail(self, sgPublishFile, sg):
        """
        Create a temporary thumbnail using images found in data to load as publish thumbnail in shotgun.
        """
        createThumbnail = False
        sourceCrawler = self.crawlers()[0]
        if "thumbnailFile" in self.optionNames():
            thumbnailFilePath = self.templateOption('thumbnailFile', crawler=sourceCrawler)
        else:
            # Look for an image sequence to create a thumbnail. If multiple sequences found, using the first one.
            createThumbnail = True
            imageCrawlers = sourceCrawler.globFromParent(filterTypes=[Image])
            if not imageCrawlers:
                # No images anywhere in the publish, nothing to use as a thumbnail
                return
            groups = Crawler.group(filter(lambda x: x.isSequence(), imageCrawlers))
            if groups:
                targetCrawler = groups[0][int(len(groups[0]) / 2)]
            else:
                targetCrawler = imageCrawlers[0]

            tempFile = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg",
                mode='w'
            )
            tempFile.close()
            thumbnailFilePath = tempFile.name
            # Remove file so the thumbnail task doesn't ask to overwrite it
            os.unlink(thumbnailFilePath)

            thumbnailTask = Task.create('imageThumbnail')
            thumbnailTask.add(targetCrawler, thumbnailFilePath)
            # Using python taskWrapper because the imageThumbnail task uses OIIO
            TaskWrapper.create('python').run(thumbnailTask)

        if os.path.exists(thumbnailFilePath):
            sg.upload_thumbnail("PublishedFile", sgPublishFile["id"], thumbnailFilePath)

        if createThumbnail:
            # removing the temporary file
            os.unlink(thumbnailFilePath)

    def __makeDaily(self, sgPublishFile, sg):
        """
        Create a version in Shotgun for this path and linked to this publish.
        """
        sourceCrawler = self.crawlers()[0]
        if 'movieFile' not in self.optionNames():
            # No movie provided, glob for a mov
            movCrawlers = sourceCrawler.globFromParent(filterTypes=["mov"])
            if not movCrawlers:
                return
            movieFilePath = movCrawlers[0].var("filePath")
        else:
            movieFilePath = self.templateOption('movieFile', crawler=sourceCrawler)
            if not movieFilePath or not os.path.exists(movieFilePath):
                raise Exception("Movie provided for daily creation does not exist: {}".format(movieFilePath))

        # create a name for the version based on the file name
        # grab the file name, strip off extension
        name = os.path.splitext(os.path.basename(movieFilePath))[0]
        # do some replacements
        name = name.replace("_", " ")
        # and capitalize
        name = name.capitalize()

        firstFrame = None
        lastFrame = None
        imageSeqPath = None
        movCrawler = FsPath.createFromPath(movieFilePath)
        if firstFrame in movCrawler.varNames():
            firstFrame = movCrawler.var('firstFrame')
            lastFrame = movCrawler.var('lastFrame')

        imageCrawlers = sourceCrawler.globFromParent(filterTypes=[Image])
        groups = Crawler.group(filter(lambda x: x.isSequence(), imageCrawlers))
        if groups:
            seqGroup = groups[0]
            imageSeqPath = os.path.join(
                os.path.dirname(seqGroup[0].var("filePath")),
                '{0}.%0{1}d.{2}'.format(
                    seqGroup[0].var('name'),
                    seqGroup[0].var('padding'),
                    seqGroup[0].var('ext')
                    )
                )
            if firstFrame is None:
                firstFrame = seqGroup[0].var('frame')
                lastFrame = seqGroup[-1].var('frame')

        # Create the version in Shotgun
        data = {
            "code": name,
            "sg_status_list": "rev",
            "entity": self.__publishData['entity'],
            "created_by": self.__publishData['created_by'],
            "user": self.__publishData['created_by'],
            "description": self.__publishData['description'],
            "project": self.__publishData['project']
        }

        if firstFrame is not None and lastFrame is not None:
            data["sg_first_frame"] = firstFrame
            data["sg_last_frame"] = lastFrame
            data["frame_count"] = (lastFrame - firstFrame + 1)
            data["frame_range"] = "%s-%s" % (firstFrame, lastFrame)
        if imageSeqPath:
            data["sg_path_to_frames"] = imageSeqPath

        data["published_files"] = [sgPublishFile]
        data["sg_path_to_movie"] = movieFilePath

        sgVersion = sg.create("Version", data)
        # upload files
        sg.upload("Version", sgVersion["id"], movieFilePath, "sg_uploaded_movie")

        return sgVersion


# registering task
Task.register(
    'sgPublish',
    SGPublish
)
