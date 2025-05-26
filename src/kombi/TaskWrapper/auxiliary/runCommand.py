#!/usr/bin/env python

import os
import sys
import json
import base64
import getpass
import subprocess

def runCommand(env, command):
    """
    This script is executed by the SubprocessTaskWrapper when a command needs to run under a different user.
    """
    removeVars = (
        "USER",
        "USERNAME",
        "HOME",
        "LOGNAME"
    )
    for removeVar in removeVars:
        if removeVar in env:
            del env[removeVar]

    for key, value in dict(os.environ).items():
        if key not in env:
            env[key] = value

    # when running with a different user setting a different cache location
    # to avoid having permissions issues later
    for updateCacheKey in ('REDSHIFT_LOCALDATAPATH', 'NUKE_DISK_CACHE'):
        if updateCacheKey not in env:
            continue

        env[updateCacheKey] = '{}-{}'.format(
            env[updateCacheKey],
            getpass.getuser()
        )

    env['KOMBI_TASKWRAPPER_PARENT_PID'] = str(os.getpid())

    # running command
    process = subprocess.Popen(
        command,
        stderr=subprocess.STDOUT,
        env=env,
        shell=True,
        preexec_fn=os.setsid
    )

    process.wait()

    # retuning with the subprocess exit code
    sys.exit(process.returncode)


if __name__ == "__main__":
    content = json.loads(
        base64.b64decode(
            sys.argv[1].encode('utf-8')
        )
    )

    runCommand(
        content['env'],
        content['command']
    )
