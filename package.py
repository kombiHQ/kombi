#! /usr/bin/env python3

import os
import zipfile
import argparse

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

def __zipContent(rootDirectory, directory, ignoreDirectories, file):
    """
    Recursively adds files and directories to the zip file.
    """
    for item in os.listdir(directory):
        fullItemPath = os.path.join(directory, item)

        if os.path.isfile(fullItemPath):
            arcname = os.path.relpath(fullItemPath, start=os.path.dirname(rootDirectory))
            file.write(fullItemPath, arcname)

        elif os.path.isdir(fullItemPath) and item not in ignoreDirectories:
            arcname = os.path.relpath(fullItemPath, start=os.path.dirname(rootDirectory)) + '/'
            file.write(fullItemPath, arcname)
            __zipContent(rootDirectory, fullItemPath, ignoreDirectories, file)

def main():
    """
    Handle the argument parsing and creating the package.
    """
    parser = argparse.ArgumentParser(description="Create an archive for all kombi data necessary for deployment")
    parser.add_argument('--fullData', action='store_true', help="Include full data (default is False).")
    parser.add_argument('output', nargs='?', type=str, default='kombi.zip', help="Output zip file (default is 'kombi.zip').")
    args = parser.parse_args()

    excludeDataDirectories = [
        '__pycache__'
    ]
    if not args.fullData:
        excludeDataDirectories += [
            'doc',
            'examples',
            'tests'
        ]

    directoriesToZip = {
        os.path.join(CURRENT_DIRECTORY, 'data'): excludeDataDirectories,
        os.path.join(CURRENT_DIRECTORY, 'src', 'bin'): ['__pycache__'],
        os.path.join(CURRENT_DIRECTORY, 'src', 'lib'): ['__pycache__']
    }

    rootFiles = ['LICENSE', 'info.json']
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as file:
        for rootFile in rootFiles:
            file.write(os.path.join(CURRENT_DIRECTORY, rootFile), rootFile)
        for rootDirectory, ignoreDirectories in directoriesToZip.items():
            __zipContent(rootDirectory, rootDirectory, ignoreDirectories, file)


if __name__ == '__main__':
    main()
