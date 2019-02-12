# gaffer needs to be imported at top-most
import Gaffer # noqa: w0611

# now we can import chilopoda
import chilopoda

# running serialized task
chilopoda.TaskWrapper.Subprocess.runSerializedTask()
