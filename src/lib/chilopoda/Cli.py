import os
import sys
import argparse
import fileinput
from .Crawler.Fs.FsPath import FsPath
from .Crawler.Fs.Directory import Directory
from .Crawler import Crawler
from .TaskHolderLoader import TaskHolderLoader
from .Dispatcher import Dispatcher

class CliError(Exception):
    """Cli Error."""

class Cli(object):
    """
    Runs a chilopoda configuration through command-line.
    """

    def __init__(self):
        """
        Create a cli object.
        """
        self.__parser = argparse.ArgumentParser(
            description='Executes a configuration in chilopoda'
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

    def run(self, args, outStream=sys.stdout):
        """
        Execute the configuration.
        """
        parseArgs = self.__parser.parse_args(args)

        loader = TaskHolderLoader()

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

        # collecting crawlers
        crawlers = self.__loadCrawlers(parseArgs.source)

        # creating dispatcher
        dispatcher = Dispatcher.create('local')
        dispatcher.setOption('defaultReporter', 'columns')
        dispatcher.setOption('awaitExecution', True)

        # dispatching task holders
        for taskHolder in loader.taskHolders():
            for crawlersGroup in Crawler.group(crawlers):
                dispatcher.dispatch(taskHolder, crawlersGroup)

    def __loadCrawlers(self, sourcePaths):
        """
        Return the source crawlers.
        """
        crawlers = []
        globDirectoryCrawlers = True

        # source through argument
        if sourcePaths:
            for sourcePath in sourcePaths:
                crawler = FsPath.createFromPath(sourcePath)
                crawlers.append(crawler)

        # source through stdin
        elif not sys.stdin.isatty():
            for line in fileinput.input(files=[]):
                # in case the sdtin is reading a chilopoda
                # output the result. It will be defined
                # in columns (taskName, crawlerType, fullPath).
                outputParts = tuple(filter(lambda x: x != '', line.strip().split('\t')))
                crawlerFullPath = outputParts[-1]

                # when stdin is reading chilopoda output
                crawler = None
                if len(outputParts) == 3:
                    globDirectoryCrawlers = False
                    crawler = FsPath.createFromPath(
                        crawlerFullPath,
                        outputParts[1]
                    )

                # otherwise when stdin is reading a list of paths
                else:
                    crawler = FsPath.createFromPath(crawlerFullPath)

                crawlers.append(crawler)
        else:
            raise CliError("Cannot determine source!")

        # when a directory is detect as input. We glob
        # by default. The only exception is when
        # the crawler type is defined (reading a chilopoda output)
        if globDirectoryCrawlers:
            for crawler in list(crawlers):
                if isinstance(crawler, Directory):
                    crawlers += crawler.glob()

        return crawlers
