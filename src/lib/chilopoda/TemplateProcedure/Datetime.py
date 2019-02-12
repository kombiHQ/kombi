import datetime
from ..Template import Template

class _Datetime(object):
    """
    Basic datetime functions.
    """

    @staticmethod
    def yyyy():
        """
        Return the year formatted by 4 digits.
        """
        return datetime.datetime.now().strftime("%Y")

    @staticmethod
    def yy():
        """
        Return the year formatted by 2 digits.
        """
        return datetime.datetime.now().strftime("%y")

    @staticmethod
    def mm():
        """
        Return the month formatted by 2 digits.
        """
        return datetime.datetime.now().strftime("%m")

    @staticmethod
    def dd():
        """
        Return the day formatted by 2 digits.
        """
        return datetime.datetime.now().strftime("%d")

    @staticmethod
    def hour():
        """
        Return the hour formatted by 2 digits (24 hours format).
        """
        return datetime.datetime.now().strftime("%H")

    @staticmethod
    def minute():
        """
        Return the minutes formatted by 2 digits.
        """
        return datetime.datetime.now().strftime("%d")

    @staticmethod
    def second():
        """
        Return the seconds formatted by 2 digits.
        """
        return datetime.datetime.now().strftime("%S")


# registering template procedures
Template.registerProcedure(
    'yyyy',
    _Datetime.yyyy
)

Template.registerProcedure(
    'yy',
    _Datetime.yy
)

Template.registerProcedure(
    'mm',
    _Datetime.mm
)

Template.registerProcedure(
    'dd',
    _Datetime.dd
)

Template.registerProcedure(
    'hour',
    _Datetime.hour
)

Template.registerProcedure(
    'minute',
    _Datetime.minute
)

Template.registerProcedure(
    'second',
    _Datetime.second
)
