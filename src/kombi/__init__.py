import sys
from .ProcessExecution import ProcessExecution
from .EnvModifier import EnvModifier, EnvModifierError, EnvModifierInvalidVarError, EnvModifierInvalidVarValueError
from .Config import Config, ConfigKeyError
from .KombiError import KombiError
from . import Element
from . import Template
from . import Task
from . import TaskReporter
from . import TaskWrapper
from . import TaskHolder
from . import Dispatcher
from .Cli import Cli, CliError

# The ResourceLoader class needs to be imported as the last one, since it's going to
# initialize all the resources defined through the environment variable. These
# resources can be using the modules above (that's why it needs
# be imported as the last one).
from .ResourceLoader import ResourceLoader, ResourceLoaderError, ResourceLoaderInvalidError
# loading resources by triggering the singleton
ResourceLoader.get()

# initialize cli support
def init():
    """
    Initialize kombi cli.
    """
    Cli().run(
        sys.argv[1:]
    )
