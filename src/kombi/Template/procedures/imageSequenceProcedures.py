"""
Basic image sequence functions.
"""

from ..Template import Template

def padding(frame, size):
    """
    Return the frame with the padding size specified.
    """
    return str(int(frame)).zfill(int(size))

def retimePadding(frame, retime, size):
    """
    Return the frame with the padding size specified.
    """
    return str(int(frame) + int(retime)).zfill(int(size))


# frame padding
Template.registerProcedure(
    'pad',
    padding
)

# re-time frame padding
Template.registerProcedure(
    'retimepad',
    retimePadding
)
