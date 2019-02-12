import json
import os
from chilopoda.Template import Template

def queryVendorVersion(dataFilePath):
    """
    Return the vendor version stored under the vendor data.
    """
    data = ""
    with open(os.path.join(os.path.dirname(os.path.dirname(dataFilePath)), "vendor.json")) as f:
        data = json.load(f)

    return str(data['vendorVersion']).zfill(3)


def queryVendorPlateName(dataFilePath):
    """
    Return the vendor plate name stored under the vendor data.
    """
    data = ""
    with open(os.path.join(os.path.dirname(os.path.dirname(dataFilePath)), "vendor.json")) as f:
        data = json.load(f)

    return data['plateName']


# internal plate to client plate
Template.registerProcedure(
    'queryvendorver',
    queryVendorVersion
)

Template.registerProcedure(
    'queryplatename',
    queryVendorPlateName
)
