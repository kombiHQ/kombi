import csv
import os
from ...InfoCrate.Fs import FsInfoCrate
from ...InfoCrate.Fs.Image import ImageInfoCrate
from ...InfoCrate.Fs.Video import VideoInfoCrate
from ..Task import Task

class SubmissionSheetTask(Task):
    """
    A task to create a cvs file for client deliveries.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a submission sheet object.
        """
        super(SubmissionSheetTask, self).__init__(*args, **kwargs)

        self.__rows = {}
        self.__deliveryData = {}
        self.__clientDeliveryPath = ""

    def _perform(self):
        """
        Perform the task.
        """
        jsonInfoCrate = self.infoCrates()[0]
        self.__getDeliveryData(jsonInfoCrate)
        if self.option('mergeMattes'):
            self.__findMattes()

        self.__columnLabels = list(map(lambda x: x[0], self.option("_columns")))

        internalDeliveryFolder = os.path.dirname(jsonInfoCrate.var('filePath'))
        self.__clientDeliveryPath = os.path.join(internalDeliveryFolder, jsonInfoCrate.var('name'))
        infoCrate = FsInfoCrate.createFromPath(self.__clientDeliveryPath)
        # Add rows for all images found first, so the resolution and other info is added in priority
        for infoCrate in infoCrate.glob(filterTypes=[ImageInfoCrate]):
            self.__setRow(infoCrate)
        # Add rows for all videos next, so if images were already written, it'll just update the extensions, otherwise
        # it'll add the full video info
        for infoCrate in infoCrate.glob(filterTypes=[VideoInfoCrate]):
            self.__setRow(infoCrate)

        self.__writeSpreadsheet()
        if self.option("includeLogFile"):
            self.__writeLogFile()

        return []

    def __getDeliveryData(self, jsonInfoCrate):
        """
        Get the delivery data stored in a json file in the parent folder of the client delivery folder.
        """
        self.__deliveryData = jsonInfoCrate.contents()

    def __findMattes(self):
        """
        Look for delivery data tagged as mattes and set their name on their matching internalVersion entry.
        """
        mattes = {}
        toDelete = []
        for name in self.__deliveryData:
            if not self.__deliveryData[name].get('isMatte', 0):
                continue
            internalVersion = self.__deliveryData[name].get('internalVersion')
            mattes[internalVersion] = name
            toDelete.append(name)
        for name in self.__deliveryData:
            internalVersion = self.__deliveryData[name].get('internalVersion')
            self.__deliveryData[name]['matteName'] = mattes.get(internalVersion, '')
        # Remove mattes from dictionary so they don't get added on their own line in the spreadsheet
        for name in toDelete:
            del self.__deliveryData[name]

    def __setRow(self, infoCrate):
        """
        Get the data expected to be in a spreadsheet row for the given file infoCrate.
        """
        name = infoCrate.var("name")

        isProxy = (name.endswith("_h264") or name.endswith("_prores"))
        if isProxy and not self.option('includeProxies'):
            return

        shortName = name if not isProxy else "_".join(name.split("_")[:-1])
        if self.option('mergeMattes') and shortName not in self.__deliveryData:
            return

        if shortName not in self.__rows:
            self.__addRow(shortName, infoCrate)
        else:
            self.__updateRow(shortName, infoCrate)

    def __addRow(self, name, infoCrate):

        self.__rows[name] = {}
        for label, fieldName in self.option("_columns"):
            # Deal with fields that require custom processing
            if fieldName == "name":
                self.__rows[name][label] = name

            elif fieldName == "clientStatus":
                extraVars = {"sg_status_list": self.__deliveryData[name].get('sg_status_list')}
                self.__rows[name][label] = self.templateOption('clientStatus', extraVars=extraVars)

            else:
                self.__rows[name][label] = self.__getFieldValue(name, fieldName, infoCrate)

    def __updateRow(self, name, infoCrate):

        for label, fieldName in self.option("_columns"):
            if fieldName == "clientFileType":
                currentExt = self.__rows[name].get(label)
                extName = self.__getFieldValue(name, fieldName, infoCrate)
                if extName not in currentExt.split(","):
                    self.__rows[name][label] = "{},{}".format(currentExt, extName)

    def __getFieldValue(self, name, fieldName, infoCrate):
        # Look for a value in the delivery data first
        if fieldName in self.__deliveryData[name]:
            return self.__deliveryData[name].get(fieldName)
        # Next, it could be a task option
        elif fieldName in self.optionNames():
            return self.templateOption(fieldName, infoCrate=infoCrate)
        # Finally, the value would be in the infoCrate
        elif fieldName in infoCrate.varNames():
            return infoCrate.var(fieldName)

    def __writeSpreadsheet(self):
        """
        Write a cvs file at the target path.
        """
        targetPath = os.path.join(self.__clientDeliveryPath, "{}.csv".format(self.infoCrates()[0].var('name')))
        with open(targetPath, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.__columnLabels)
            writer.writeheader()
            for rowName in sorted(self.__rows):
                writer.writerow(self.__rows[rowName])

    def __writeLogFile(self):
        name = os.path.basename(self.__clientDeliveryPath)
        logFile = os.path.join(self.__clientDeliveryPath, "{}_log.txt".format(name))
        os.system("cd {0};ls -1R > {1}".format(self.__clientDeliveryPath, logFile))


# registering task
Task.register(
    'submissionSheet',
    SubmissionSheetTask
)
