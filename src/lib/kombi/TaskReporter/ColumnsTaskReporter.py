import sys
from .TaskReporter import TaskReporter

class ColumnsTaskReporter(TaskReporter):
    """
    Implements columns task reporter.
    """

    __columnSize = 8
    __reserveColumns = 4

    def display(self):
        """
        Implement the column display.
        """
        # computing task name column size
        taskNameWidth = self.__columnSize * self.__reserveColumns
        if self.__textColumnSize(self.taskName()) + self.__columnSize >= taskNameWidth:
            taskNameWidth = self.__textColumnSize(self.taskName()) + self.__columnSize

        # computing crawler type column size
        crawlerTypeWidth = self.__columnSize * self.__reserveColumns
        for crawler in self.crawlers():
            if self.__textColumnSize(crawler.var('type')) + self.__columnSize >= crawlerTypeWidth:
                crawlerTypeWidth = self.__textColumnSize(crawler.var('type')) + self.__columnSize

        # printing columns
        for crawler in self.crawlers():
            sys.stdout.write(
                '{}{}{}{}{}\n'.format(
                    self.taskName(),
                    "\t" * int((taskNameWidth - self.__textColumnSize(self.taskName())) / self.__columnSize),
                    crawler.var('type'),
                    "\t" * int((crawlerTypeWidth - self.__textColumnSize(crawler.var('type'))) / self.__columnSize),
                    crawler.var('fullPath')
                )
            )

    @classmethod
    def __textColumnSize(cls, text):
        """
        Return the size of the text fitted in columns.
        """
        return len(text) + cls.__columnSize - (len(text) % cls.__columnSize)


# registering reporter
TaskReporter.register(
    'columns',
    ColumnsTaskReporter
)
