import os
import sys
import time
import json
from random import random
from glob import glob
from kombi.Task import Task
from kombi.Crawler import Crawler

class UnlockTask(Task):
    """
    Implements a task that unlocks the flow and in case it is all clear return the incoming crawlers as result.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a touch with info object.
        """
        super(UnlockTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', False)
        self.setMetadata('dispatch.splitSize', 1)

    def _perform(self):
        """
        Implement the execution of the task.
        """
        crawlers = self.crawlers()
        targetLock = self.target(crawlers[0])
        ext = os.path.splitext(targetLock)[-1]
        assert ext == '.lock', 'Invalid lock!'

        # unlocking
        if os.path.exists(targetLock):
            unlockedFileName = '{}.unlock'.format(
                os.path.splitext(targetLock)[0]
            )

            # dumping crawler info under the lock
            with open(targetLock, 'w') as f:
                json.dump(list(map(lambda x: x.toJson(), crawlers)), f)

            time.sleep(random() * 60)
            os.rename(
                targetLock,
                unlockedFileName
            )

        missingLocks = glob(
            os.path.join(
                os.path.dirname(targetLock),
                '*.lock'
            )
        )

        if missingLocks:
            sys.stdout.write('Pending locks:\n')
            for lockName in missingLocks:
                sys.stdout.write(
                    '    - {}\n'.format(lockName)
                )

            return []

        allunlocked = os.path.join(os.path.dirname(targetLock), 'allunlocked')
        allUnlockExists = False
        for i in range(10):
            time.sleep(1)
            if os.path.exists(allunlocked):
                allUnlockExists = True
                break

        if not allUnlockExists:
            # touching the file
            with open(allunlocked, 'a'):
                os.utime(allunlocked)
        else:
            sys.stdout.write(
                'Skipping unlock (it has already been done by another unlock all)\n'
            )
            return []

        # otherwise lets read all crawlers under the unlocks. They are
        # gonna become the result of the task
        unlocks = glob(
            os.path.join(
                os.path.dirname(targetLock),
                '*.unlock'
            )
        )

        result = []
        for unlockName in unlocks:
            with open(unlockName) as f:
                result.extend(
                    map(Crawler.createFromJson, json.load(f))
                )

        return result


# registering task
Task.register(
    'unlock',
    UnlockTask
)
