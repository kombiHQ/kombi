import argparse
from chilopoda.TaskHolder import TaskHolder

def __run(data):
    """
    Execute the taskHolder.
    """
    # loading task holder and running it
    with open(data) as f:
        taskHolder = TaskHolder.createFromJson(f.read())

        # executing run
        taskHolder.run()


# command-line interface
parser = argparse.ArgumentParser()

parser.add_argument(
    'data',
    metavar='data',
    type=str,
    help='json file containing the serialized task holder that should be executed'
)

# executing it
if __name__ == "__main__":
    args = parser.parse_args()
    __run(args.data)
