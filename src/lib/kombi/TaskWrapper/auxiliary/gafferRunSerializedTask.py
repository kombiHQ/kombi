# gaffer needs to be imported at top-most
import Gaffer # noqa: w0611

# now we can import kombi
import kombi

# running serialized task
kombi.TaskWrapper.Subprocess.runSerializedTask()
