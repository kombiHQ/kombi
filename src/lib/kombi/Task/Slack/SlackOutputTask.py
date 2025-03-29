import os
import sys
from ..External.ExternalTask import ExternalTask

class SlackOutputTask(ExternalTask):
    """
    Generic slack output task.
    """

    __slackToken = os.environ.get('KOMBI_SLACK_TOKEN', '')

    def __init__(self, *args, **kwargs):
        """
        Create a slack ouput task.
        """
        super(SlackOutputTask, self).__init__(*args, **kwargs)

        self.setOption('channel', '')
        self.setOption('users', [])
        self.setOption('messageHeader', '')
        self.setOption('messageElements', True)
        self.setOption('addExtraLineAtTheEnd', True)
        self.setOption('slackToken', self.__slackToken)
        self.setMetadata('wrapper.name', 'python')
        self.setMetadata('wrapper.options', {})

        self.setMetadata(
            'ui.options.users',
            {
                'visual': 'checkList',
                'main': True,
                'label': 'Inform users on Slack',
                'values': []
            }
        )

        self.setMetadata(
            'ui.options.enableDaily',
            {
                'main': False,
                'label': 'Enable Daily'
            }
        )

        self.setMetadata(
            'ui.options._slateDescription',
            {
                'main': False,
                'label': 'Description',
                'visual': 'longText'
            }
        )

        self.setMetadata(
            'ui.options._internalBurnins',
            {
                'main': False,
                'label': 'Animism Burn-in'
            }
        )

        self.setMetadata(
            'ui.options._clientBurnins',
            {
                'main': False,
                'label': 'Client Burn-in'
            }
        )

        self.setMetadata(
            'ui.options._enableCdl',
            {
                'main': False,
                'label': 'Apply Client Cdl'
            }
        )

    def _perform(self):
        """
        Perform the task.
        """
        import slack

        content = []
        element = self.elements()[0]
        header = self.option('messageHeader', element)
        if header:
            content.append(header)

        if self.option('messageElements', element):
            content += list(map(lambda x: os.path.normpath(x.var('fullPath')).replace("\\", "/"), self.elements()))

        if self.option('addExtraLineAtTheEnd', element):
            content.append('')

        client = slack.WebClient(token=self.option('slackToken', element))

        # sending message to the channel
        channel = self.option('channel', element)
        if channel:
            try:
                client.chat_postMessage(
                    channel=channel,
                    text='\n'.join(content),
                    user=''
                )
            except Exception as err:
                sys.stderr.write("Error on posting message to channel {}:\n{}\n".format(channel, str(err)))
                sys.stderr.flush()
            else:
                sys.stdout.write('Success on sending message to channel {}\n'.format(channel))
                sys.stdout.flush()

        # sending slack messages
        for user in self.option('users', element):
            try:
                client.chat_postMessage(
                    channel="@{}".format(user),
                    text="Output created by {}: {}".format(
                        os.environ['KOMBI_USER'],
                        '\n'.join(content)
                    )
                )
            except Exception as err:
                sys.stderr.write("Error on sending message to user {}:\n{}\n".format(user, str(err)))
                sys.stderr.flush()
            else:
                sys.stdout.write('Success on sending message to user {}\n'.format(user))
                sys.stdout.flush()

        return []


# registering task
ExternalTask.register(
    'slackOutput',
    SlackOutputTask
)
