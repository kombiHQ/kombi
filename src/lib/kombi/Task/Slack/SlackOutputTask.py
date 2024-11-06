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
        self.setOption('messageCrawlers', True)
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
        crawler = self.crawlers()[0]
        header = self.templateOption('messageHeader', crawler)
        if header:
            content.append(header)

        if self.templateOption('messageCrawlers', crawler):
            content += list(map(lambda x: os.path.normpath(x.var('fullPath')).replace("\\", "/"), self.crawlers()))

        if self.templateOption('addExtraLineAtTheEnd', crawler):
            content.append('')

        client = slack.WebClient(token=self.templateOption('slackToken', crawler))

        # sending message to the channel
        channel = self.templateOption('channel', crawler)
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
        for user in self.templateOption('users', crawler):
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
