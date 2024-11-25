import os
import sys
from collections import OrderedDict
from ..External.ExternalTask import ExternalTask

class FtrackPublishAssetVersionTask(ExternalTask):
    """
    Generic ftrack publish asset version task.
    """

    __ftrackToken = os.environ.get('KOMBI_FTRACK_TOKEN', '')
    __ftrackUrl = os.environ.get('KOMBI_FTRACK_URL', '')
    __ftrackUser = os.environ.get('KOMBI_FTRACK_USER', '')

    def __init__(self, *args, **kwargs):
        """
        Create a ftrack ouput task.
        """
        super(FtrackPublishAssetVersionTask, self).__init__(*args, **kwargs)
        self.setOption('user', self.__ftrackUser)

        self.setOption('addForInternalReview', False)
        self.setOption('outputType', '{outputType}')
        self.setOption('department', '{department}')
        self.setOption('comment', '{slateDescription}')

        self.setMetadata(
            'ui.options.addForInternalReview',
            {
                'main': True,
                'label': 'Add For Internal Review (F-Track)'
            }
        )
        self.setMetadata('wrapper.name', 'python')
        self.setMetadata('wrapper.options', {})

        # task input type
        self.setMetadata(
            "match.types", [
                'mov'
            ]
        )

    def _perform(self):
        """
        Perform the task.
        """
        import ftrack_api

        element = self.elements()[0]
        user = self.templateOption('user', element)
        department = self.templateOption('department', element).lower()
        outputType = self.templateOption('outputType', element)
        comment = self.templateOption('comment', element)

        session = ftrack_api.Session(
            self.__ftrackUrl,
            self.__ftrackToken,
            user
        )

        # building fields used to query the task
        fields = OrderedDict()

        # job
        job = element.var('clientJobName') if 'clientJobName' in element.varNames() else element.var('job')
        fields['project.name'] = job

        # season (optional)
        if 'season' in element.varNames() and element.var('season'):
            season = element.var('originalSeason') if 'originalSeason' in element.varNames() else element.var('season')

            # converting season format from 210 to S02E10
            seasonFormated = "S{}E{}".format(
                season[:-2].zfill(2),
                season[-2:].zfill(2)
            )
            fields['parent.parent.parent.name'] = seasonFormated

        # seq
        seq = element.var('originalSeq') if 'originalSeq' in element.varNames() else element.var('seq')
        fields['parent.parent.name'] = seq

        # shot
        shot = element.var('originalShot') if 'originalShot' in element.varNames() else element.var('shot')
        fields['parent.name'] = shot

        # special case for archer
        # TODO: remove this mapping in future releases
        if element.var('job').lower() == 'arc':
            charName = element.var('name').split('_')[-2].split('-')[0]
            fields['parent.parent.name'] = charName

        # task name
        fields['name'] = department

        # building query
        queryItems = []
        for key, value in fields.items():
            queryItems.append(
                '{} is "{}" '.format(
                    key,
                    value
                )
            )

        query = 'Task where {}'.format(
            'and '.join(queryItems)
        )

        assetType = session.query('AssetType where name is "Upload"').one()
        departmentTask = session.query(query).first()

        # when shot has not task for the department
        if not departmentTask:
            sys.stderr.write(
                '{}\n\nCould not find a task for the department: "{}"\n'.format(
                    query,
                    department
                )
            )
            return []

        # creating asset (if needed)
        fields['parent.project.name'] = fields['project.name']
        del fields['project.name']
        assetName = "_".join(element.var('name').split("_")[:-1])

        # adding the output as part of the asset name
        assetName += "_{}".format(outputType)

        fields['name'] = assetName

        # building query for asset
        queryItems = []
        for key, value in fields.items():
            queryItems.append(
                '{} is "{}" '.format(
                    key,
                    value
                )
            )

        assetQuery = 'Asset where {}'.format(
            'and '.join(queryItems)
        )

        # executing query
        asset = session.query(assetQuery).first()
        if not asset:
            asset = session.create(
                'Asset', {
                    'name': assetName,
                    'type': assetType,
                    'parent': departmentTask['parent']
                }
            )
            session.commit()

        assetVersion = session.query(
            'AssetVersion where version is {} and asset_id is "{}"'.format(
                element.var('version'),
                asset['id']
            )
        ).first()

        # creating new asset version
        if not assetVersion:
            assetVersion = session.create(
                'AssetVersion',
                {
                    'asset': asset,
                    'task': departmentTask,
                    'comment': comment,
                    'version': element.var('version')
                }
            )
            session.commit()

        # adding component to the asset version
        # (limiting to a single quicktime)
        assetVersion.encode_media(
            element.var('fullPath')
        )

        # updating task status
        if self.option('addForInternalReview') and outputType != 'client':
            for status in departmentTask['project']['project_schema'].get_statuses('Task'):
                if status['name'].lower() == 'internal review':
                    departmentTask['status'] = status
                    session.commit()
                    break

        return []


# registering task
ExternalTask.register(
    'ftrackPublishAssetVersion',
    FtrackPublishAssetVersionTask
)
