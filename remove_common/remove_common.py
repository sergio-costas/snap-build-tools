#!/usr/bin/env python3

""" Removes files that are already in base snaps or have been generated
    in a previous part. Useful to remove files added by stage-packages
    due to dependencies, but that aren't required because they are
    already available in core22, gnome-42-2204 or gtk-common-themes,
    or have already been built by a previous part. """

import sys
import os
import glob
import argparse

parser = argparse.ArgumentParser(prog="remove_common", description="An utility to remove from snaps files that are already available in extensions")
parser.add_argument('extensions', nargs='+')
parser.add_argument('-e', '--exclude', nargs='+', help="A list of file and folders to exclude from checking")
parser.add_argument('-v', '--verbose', action='store_true', help="Show extra info")
args = parser.parse_args()

def check_if_exists(folder_list, relative_file_path):
    """ Checks if an specific file does exist in any of the base paths"""
    for folder in folder_list:
        check_path = os.path.join(folder, relative_file_path)
        if os.path.exists(check_path):
            return True
    return False


def main(base_folder, folder_list, exclude_list, verbose=False):
    """ Main function """
    duplicated_bytes = 0
    for full_file_path in glob.glob(os.path.join(base_folder, "**/*"), recursive=True):
        if not os.path.isfile(full_file_path) and not os.path.islink(full_file_path):
            continue
        relative_file_path = full_file_path[len(base_folder):]
        if relative_file_path[0] == '/':
            relative_file_path = relative_file_path[1:]
        if relative_file_path in exclude_list:
            if verbose:
                print(f"Excluding {relative_file_path}")
            continue
        if os.path.split(relative_file_path)[0] in exclude_list:
            if verbose:
                print(f"Excluding {relative_file_path}")
            continue
        if check_if_exists(folder_list, relative_file_path):
            if os.path.isfile(full_file_path):
                duplicated_bytes += os.stat(full_file_path).st_size
            os.remove(full_file_path)
            if verbose:
                print(f"Removing duplicated file {relative_file_path}")
    print(f"Removed {duplicated_bytes} bytes in duplicated files")


if __name__ == "__main__":
    folders = []

    VERBOSE = args.verbose
    exclude = args.exclude
    if exclude is None:
        exclude = []

    folders.append(os.environ["CRAFT_STAGE"])
    for snap in args.extensions:
        folders.append(f"/snap/{snap}/current")

    install_folder = os.environ["CRAFT_PART_INSTALL"]

    main(install_folder, folders, exclude, VERBOSE)
