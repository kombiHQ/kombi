import os
import sys
import json
from datetime import datetime
from ..External.ExternalTask import ExternalTask
from ...InfoCrate.Fs.Video import VideoInfoCrate

class SGPublishTask(ExternalTask):
    """
    Generic shotgun version publishing task.
    """

    __shotgunToken = os.environ.get('KOMBI_SHOTGUN_TOKEN')
    __shotgunUrl = os.environ.get('KOMBI_SHOTGUN_URL')
    __shotgunUser = os.environ.get('KOMBI_SHOTGUN_USER', '(env KOMBI_USER)')
    __shotgunScriptName = os.environ.get('KOMBI_SHOTGUN_SCRIPTNAME')

    def __init__(self, *args, **kwargs):
        """
        Create a shotgun output task.
        """
        super(SGPublishTask, self).__init__(*args, **kwargs)
        self.setOption('user', self.__shotgunUser)
        self.setOption('shotgunVersionTrackFile', '')
        self.setOption('shotgunTask', '')
        self.setOption('addForInternalReview', False)
        self.setOption('outputType', 'internal')
        self.setOption('displayPath', '{name}')
        self.setOption('versionType', '')
        self.setOption('department', '{department}')
        self.setOption('comment', '')
        self.setOption('pathToFrames', '')
        self.setOption('thumbnail', '')

        self.setMetadata(
            'ui.options.addForInternalReview',
            {
                'main': True,
                'label': 'Add For Internal Review (Shotgun)'
            }
        )

        self.setMetadata('wrapper.name', 'python')
        self.setMetadata('wrapper.options', {})

    def _perform(self):
        """
        Perform the task.
        """
        import shotgun_api3

        infoCrate = self.infoCrates()[0]
        userName = self.templateOption('user', infoCrate)
        outputType = self.templateOption('outputType', infoCrate)
        comment = self.templateOption('comment', infoCrate)

        sg = shotgun_api3.Shotgun(
            self.__shotgunUrl,
            script_name=self.__shotgunScriptName,
            api_key=self.__shotgunToken
        )

        taskValue = self.templateOption('shotgunTask', infoCrate)
        filters = []
        if taskValue:
            if taskValue.isdigit():
                taskValue = int(taskValue)
            elif "#Task_" in taskValue:
                taskValue = int(taskValue.split("#Task_")[-1])
            else:
                taskValue = int(taskValue.split("/Task/")[-1])

            task = sg.find_one(
                'Task',
                [
                    ['id', 'is', taskValue]
                ],
                ['project', 'entity', 'step']
            )
            shotOrAsset = task['entity']
            department = task['step']['name']
        else:
            job = infoCrate.var('job')
            episode = infoCrate.var('episode') if 'episode' in infoCrate.varNames() and infoCrate.var('episode') else None
            seq = infoCrate.var('seq')
            shot = infoCrate.var('shot')
            department = self.templateOption('department', infoCrate)

            filters = [
                ['project.Project.name', 'is', job],
                ['code', 'is', shot]
            ]

            if seq != 'asset':
                filters.append(
                    ['sg_sequence', 'name_is', seq]
                )

                if episode:
                    filters.append(
                        ['sg_sequence.Sequence.episode', 'name_is', episode]
                    )

            # finding task
            shotOrAsset = sg.find_one('Asset' if seq == 'asset' else 'Shot', filters, ['code'])
            if not shotOrAsset:
                sys.stdout.write('Could not find shotOrAsset:\n{}\n'.format(filters))
                return []

            filters = [
                ['project.Project.name', 'is', job],
                ['entity', 'is', shotOrAsset]
            ]

            filters.append(
                ['step', 'name_is', department]
            )

            # finding task
            task = sg.find_one('Task', filters, fields=['project'])
            if not task:
                sys.stdout.write('Could not find task:\n{}\n'.format(filters))
                return []

        filters = [
            ['login', 'is', userName]
        ]
        user = sg.find_one('HumanUser', filters)

        # finding user
        if not user:
            sys.stdout.write('Could not find user:\n{}\n'.format(filters))
            return []

        data = {
            'project': task['project'],
            'code': '{} {}'.format(
                self.templateOption('versionType', infoCrate).capitalize(),
                self.templateOption('displayPath', infoCrate)
            ).strip(),
            'description': comment,
            'entity': shotOrAsset,
            'sg_task': task,
            'sg_department': department,
            'user': user
        }

        if isinstance(infoCrate, VideoInfoCrate):
            data['sg_path_to_movie'] = os.path.normpath(infoCrate.var('fullPath'))

        if outputType == 'client':
            data['client_code'] = infoCrate.var('name')

        versionType = ''
        if self.option('versionType'):
            versionType = self.templateOption(
                'versionType',
                infoCrate
            )
            data['sg_version_type'] = versionType

        pathToFrames = None
        if self.option('pathToFrames'):
            pathToFrames = self.templateOption(
                'pathToFrames',
                infoCrate
            )
            data['sg_path_to_frames'] = os.path.normpath(pathToFrames)

        data['sg_status_list'] = 'na'
        if self.option('addForInternalReview') and outputType != 'client':
            data['sg_status_list'] = 'rev'

        result = sg.create('Version', data)

        if pathToFrames:
            pathToFramesParts = pathToFrames.split('/')
            if 'output' in pathToFramesParts and pathToFramesParts.index('output') + 4 < len(pathToFramesParts):
                outputDirPath = '/'.join(pathToFramesParts[:pathToFramesParts.index('output') + 4])
                if os.path.basename(outputDirPath).startswith('v') and os.path.basename(outputDirPath)[1:].isdigit():
                    shotgunVersionFilePath = os.path.join(outputDirPath, 'shotgunVersionInfo.json')
                    versionContent = {}

                    try:
                        if os.path.exists(shotgunVersionFilePath):
                            with open(shotgunVersionFilePath) as f:
                                versionContent = json.load(f)

                        # https://yourstudio.shotgunstudio.com/detail/[Entity Type]/[Entity ID]
                        versionContent[datetime.now().strftime("%Y-%m-%d %H:%M:%S")] = {
                            'versionId': result['id'],
                            'versionType': versionType,
                            'description': result['description'],
                            'user': userName
                        }

                        with open(shotgunVersionFilePath, 'w') as f:
                            json.dump(versionContent, f, sort_keys=True, indent=4)

                        sys.stdout.write('Updated: {}\n'.format(shotgunVersionFilePath))
                        sys.stdout.flush()

                    except Exception as err:
                        sys.stderr.write('Error on writing shotgun file: {}\n'.format(str(err)))
                        sys.stderr.flush()

        # uploading custom thumbnail
        if self.option('thumbnail'):
            sg.upload_thumbnail(
                'Version',
                result['id'],
                self.templateOption('thumbnail', infoCrate)
            )

        # uploading quicktime
        if isinstance(infoCrate, VideoInfoCrate):
            sg.upload(
                'Version',
                result['id'],
                infoCrate.var('fullPath'),
                'sg_uploaded_movie'
            )

        return []


# registering task
ExternalTask.register(
    'sgPublish',
    SGPublishTask
)
