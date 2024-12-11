import sys
from .ProcessExecution import ProcessExecution
from .EnvModifier import EnvModifier, EnvModifierError, EnvModifierInvalidVarError, EnvModifierInvalidVarValueError
from .Config import Config
from . import Element
from . import Template
from . import Task
from . import TaskReporter
from . import TaskWrapper
from . import TaskHolder
from .Cli import Cli, CliError

# The Resource class needs to be imported as the last one, since it's going to
# initialize all the resources defined through the environment variable. These
# resources can be using the modules above (that's why it needs
# be imported as the last one).
from .Resource import Resource, ResourceError, ResourceInvalidError
# loading resources by triggering the singleton
Resource.get()

# initialize cli support
def init():
    """
    Initialize kombi cli.
    """
    Cli().run(
        sys.argv[1:]
    )
