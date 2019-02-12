from ..Template import Template

class _Text(object):
    """
    Basic image sequence functions.
    """

    @staticmethod
    def upper(string):
        """
        Return string converted to upper case.
        """
        return str(string).upper()

    @staticmethod
    def lower(string):
        """
        Return string converted to lower case.
        """
        return str(string).lower()

    @staticmethod
    def replace(text, searchValue, replaceValue):
        """
        Return a string where all search value are replaced by the replace value.
        """
        return text.replace(searchValue, replaceValue)

    @staticmethod
    def remove(text, removeValue):
        """
        Return a string where all remove value are removed from the text.
        """
        return text.replace(removeValue, '')


# upper case
Template.registerProcedure(
    'upper',
    _Text.upper
)

# lower case
Template.registerProcedure(
    'lower',
    _Text.lower
)

# replace
Template.registerProcedure(
    'replace',
    _Text.replace
)

# remove
Template.registerProcedure(
    'remove',
    _Text.remove
)
