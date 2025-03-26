import os
import sys
import argparse
import subprocess
import fileinput
from .Element.Fs.FsElement import FsElement
from .Element.Fs.DirectoryElement import DirectoryElement
from .Element import Element
from .TaskHolder.Loader import Loader
from .Dispatcher import Dispatcher
from .KombiError import KombiError

class CliError(KombiError):
    """Cli Error."""

class Cli(object):
    """
    Runs a kombi configuration through command-line.
    """

    def __init__(self):
        """
        Create a cli object.
        """
        self.__parser = argparse.ArgumentParser(
            description='Executes a configuration in kombi'
        )

        self.__parser.add_argument(
            'config',
            help='path for a configuration file or a directory containing configurations files.'
        )

        self.__parser.add_argument(
            'source',
            metavar='FILE',
            nargs='*',
            help='path for a file or directory. If empty it uses stdin.'
        )

    def run(self, args, outStream=sys.stdout, errStream=subprocess.STDOUT):
        """
        Execute the configuration.
        """
        # printing ascii banner when help is invoked
        if '-h' in args or '--help' in args:
            sys.stdout.write(self.asciiBanner() + '\n')
            sys.stdout.flush()

        parseArgs = self.__parser.parse_args(args)

        loader = Loader()

        # loading configuration
        if os.path.isfile(parseArgs.config):
            loader.loadFromFile(parseArgs.config)
        else:
            loader.loadFromDirectory(parseArgs.config)

        # checking for task holders
        if not loader.taskHolders():
            raise CliError(
                "No task holders were found in the config path!"
            )

        # collecting elements
        elements = self.__loadElements(parseArgs.source)

        # creating dispatcher
        dispatcher = Dispatcher.create('local')
        dispatcher.setOption('defaultReporter', 'columns')
        dispatcher.setOption('awaitExecution', True)
        dispatcher.setStdout(outStream)
        dispatcher.setStderr(errStream)

        # dispatching task holders
        for taskHolder in loader.taskHolders():
            for elementsGroup in Element.group(elements):
                dispatcher.dispatch(
                    taskHolder,
                    elementsGroup
                )

    @classmethod
    def asciiBanner(cls, includeInfo=True):
        """
        Return the kombi ascii banner.
        """
        # This ASCII art is based on the original design found at
        # (credit to the creator, you rock!):
        # https://ascii.co.uk/art/vw
        asciiArt = [
            "  .---------------------------",
            "/--| |--| |--|  |-- \\----\\----\\",
            "|__| |__| |__|  |___ \\____\\____\\",
            "|=====================----------\\",
            "| === []   ._    ._   o\\      /o|",
            "|  __           __    ()\\    /()|",
            "| /  \\         /  \\      \\  /   |",
            "[] ( |--------| ( |_[==0======0==]",
            "  \\_/_/ \\_/_/  \\_/_/     \\_/_/"
        ]

        if includeInfo:
            asciiArt[4] += '  Kombi'
            asciiArt[5] += '  https://github.com/kombiHQ/kombi'

        return '\n'.join(asciiArt)

    def __loadElements(self, sourcePaths):
        """
        Return the source elements.
        """
        elements = []
        globDirectoryElements = True

        # source through argument
        if sourcePaths:
            for sourcePath in sourcePaths:
                element = FsElement.createFromPath(sourcePath)
                elements.append(element)

        # source through stdin
        elif not sys.stdin.isatty():
            for line in fileinput.input(files=[]):
                # in case the sdtin is reading a kombi
                # output, it is defined in columns:
                # taskName, elementType and fullPath.
                outputParts = tuple(filter(lambda x: x != '', line.strip().split('\t')))
                elementFullPath = outputParts[-1]

                # when stdin is reading kombi output
                element = None
                if len(outputParts) == 3:
                    globDirectoryElements = False
                    element = FsElement.createFromPath(
                        elementFullPath,
                        outputParts[1]
                    )

                # otherwise when stdin is reading a list of paths
                else:
                    element = FsElement.createFromPath(elementFullPath)

                elements.append(element)
        else:
            raise CliError("Cannot determine source!")

        # when a directory is detected as input. We glob
        # by default. The only exception is when
        # the element type is defined (reading a kombi output)
        if globDirectoryElements:
            for element in list(elements):
                if isinstance(element, DirectoryElement):
                    elements += element.glob()

        return elements
