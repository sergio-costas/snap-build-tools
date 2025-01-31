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
import fnmatch
try:
    import yaml
except:
    print("YAML module not found. Please, add 'python3-yaml' to the 'build-packages' list.")
    pass

parser = argparse.ArgumentParser(prog="remove_common", description="An utility to remove from snaps files that are already available in extensions")
parser.add_argument('extension', nargs='*', default=[])
parser.add_argument('-e', '--exclude', nargs='+', help="A list of files and directories to exclude from checking")
parser.add_argument('-m', '--map', nargs='+', default=[], help="A list of snap_name:path pairs")
parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Show extra info")
parser.add_argument('-q', '--quiet', action='store_true', default=False, help="Don't show any message")
args = parser.parse_args()

# specific case for themed icons
global_excludes = ['usr/share/icons/*/index.theme']
global_maps = ['gtk-common-themes:usr']

def get_snapcraft_yaml():
    """Returns a string with the full path of the snapcraft file.

    Returns
    -------
    string
        The full path of the snapcraft.yaml file, or None if no file is found.
    """

    if 'CRAFT_PROJECT_DIR' not in os.environ:
        return None

    project_folder = os.environ['CRAFT_PROJECT_DIR']
    snapcraft_file_path = os.path.join(project_folder, "snapcraft.yaml")
    if not os.path.exists(snapcraft_file_path):
        snapcraft_file_path = os.path.join(project_folder, "snap", "snapcraft.yaml")
        if not os.path.exists(snapcraft_file_path):
            return None
    return snapcraft_file_path


def get_extension_list(cmdline_extensions):
    """Returns an array with the extensions for this project.

    Parameters
    ----------
    cmdline_extensions : array of strings
        an array with the list of extensions passed by the command line.
        If no extensions were passed, it must be a zero-length array.

    Returns
    -------
    array of strings
        an array with the list of extensions desired. If no extensions are
        defined, it will return a zero-length array.

    Raises
    ------
    FileNotFoundError
        If the snapcraft.yaml file can't be found.
    """

    if len(cmdline_extensions) != 0:
        return cmdline_extensions

    snapcraft_file = get_snapcraft_yaml()
    if snapcraft_file is None:
        raise FileNotFoundError("There is no snapcraft.yaml file in the project folder")

    with open(snapcraft_file, "r") as snapcraft_stream:
        snapcraft_data = yaml.load(snapcraft_stream, Loader=yaml.Loader)
    parts_data = snapcraft_data["parts"]
    extensions = []
    for part_name in parts_data:
        part_data = parts_data[part_name]
        if "build-snaps" not in part_data:
            continue
        for extension in part_data["build-snaps"]:
            if extension not in extensions:
                extensions.append(extension)
    return extensions


def generate_mappings(predefined_mappings, cmdline_mappings):
    """Parses the specific mappings for each snap

    It receives both the predefined mappings and the mappings passed by
    command line, and returns a dictionary with each snap and its corresponding
    mapping path.

    Parameters
    ----------
    predefined_mappings : array of strings
        An array of strings, each one in the format snap_name:mapping. Used
        for the "known mappings", like the one for gtk-common-themes.
    cmdline_mappings : array of strings
        An array of strings as received from argparse with the snap_name:mapping
        pairs.

    Returns
    -------
    dictionary
        A dictionary where each key is a string with a snap name and the
        value is another string with the mapping path for that snap, ended
        in '/'.

    Raises
    ------
    SyntaxError
        If the format of any of the mapping strings is not valid
    """

    mappings = {}

    for map in predefined_mappings + cmdline_mappings:
        elements = map.split(":")
        if len(elements) != 2:
            raise SyntaxError("Error in mapping. It must be in the format snap_name:path", {'filename': 'remove_common.py', 'text': map, 'lineno': 0, 'offset': 0})
        if elements[1] == '/':
            raise SyntaxError("The mapping can't be '/'", {'filename': 'remove_common.py', 'text': map, 'lineno': 0, 'offset': 0})
        while elements[1][0] == '/':
            elements[1] = elements[1][1:]
        if elements[1][-1] != '/':
            elements[1] += '/'
        mappings[elements[0]] = elements[1]

    return mappings


def generate_extensions_paths(extensions, mappings):
    """Generates the list of extensions paths from the list of extensions

    This list has the paths of each extension used, to know where to search
    for duplicates. Also, it contains the corresponding map for each path.

    Parameters
    ----------
    extensions : array of strings
        An array of strings with the names of the extensions used in this snap.
    mappings : dictionary
        A dictionary where each key is a string with a snap name and the
        value is another string with the mapping path for that snap, ended
        in '/'.

    Returns
    -------
    array of tuples
        An array of tuples, where the first element of each tuple is a string
        to the contents of each extension, and the second element is the mapping
        for that path, or None if no mapping is needed.
    """

    folders = []
    for snap in extensions:
        path = f"/snap/{snap}/current"
        map_path = mappings[snap] if snap in mappings else None
        folders.append((path, map_path))
    return folders


def check_if_exists(extensions_paths, relative_file_path, verbose):
    """Checks if an specific file does exist in any of the base paths.

    Checks if the specified file at `relative_file_path` does exist in
    any of the paths included in the `extensions_paths` array, taking into
    account the mapping specified.

    Mapping is paramount for some extension snaps like gtk-common-themes.
    In this specific case, the snap contains the `share` folder directly
    at its root folder, while any other snap would have it inside the
    `usr` folder. Thus, for that extension snap, the map must be `usr`
    to instruct this function to remove `usr` from the beginning of the
    relative path when checking for a file inside gtk-common-themes.

    Parameters
    ----------
    extensions_paths : array of tuples with two elements
        An array with tuples containing each one a string with the root
        path for one of the extensions snap, and, if required, another
        string with the mapping for that snap (or None if no mapping is
        required for that snap).
    relative_file_path : string
        The file path to search in the folder list, relative to the
        snap root.

    Returns
    -------
    boolean
        It returns True if the file does exist in, at least, one of the
        specified snaps, and false if it doesn't exist in any of them.
    """
    # Checks if an specific file does exist in any of the base paths
    for folder, map_path in extensions_paths:
        if (map_path is not None) and relative_file_path.startswith(map_path):
            relative_file_path2 = relative_file_path[len(map_path):]
            if relative_file_path2[0] == '/':
                relative_file_path2 = relative_file_path2[1:]
        else:
            relative_file_path2 = relative_file_path
        check_path = os.path.join(folder, relative_file_path2)
        if os.path.exists(check_path):
            if verbose:
                print(f"The path {relative_file_path} has been found inside {folder} with map {map_path}: {relative_file_path2}")
            return True
    return False


def main(snap_folder, extensions_paths, exclude_list=[], verbose=False, quiet=True):
    """Main function

    Searches each file in 'snap_folder' inside each path in 'extensions_paths'
    to check if it is already available there, deleting it in that case, unless
    it matches any of the rules in 'exclude_list'.

    The check is done based only on the relative path and file name relative to
    'snap_folder', searching that inside each path in 'extensions_paths', although
    taking into account the mapping.

    Parameters
    ----------
    snap_folder : string
        The path of the folder where the staged .deb have been uncompressed (usually
        CRAFT_PART_INSTALL)
    extensions_paths : array of tuples with two elements
        An array with tuples containing each one a string with the root
        path for one of the extensions snap, and, if required, another
        string with the mapping for that snap (or None if no mapping is
        required for that snap).
    exclude_list : array of strings
        A list of fnmatch rules for excluding files and/or paths
    verbose : bool, optional
        Show extra verbose information, by default False
    quiet : bool, optional
        Don't show messages, by default False
    """

    duplicated_bytes = 0
    for full_file_path in glob.glob(os.path.join(snap_folder, "**/*"), recursive=True):
        if not os.path.isfile(full_file_path) and not os.path.islink(full_file_path):
            continue
        relative_file_path = full_file_path[len(snap_folder):]
        if relative_file_path[0] == '/':
            relative_file_path = relative_file_path[1:]
        do_exclude = False
        for exclude in exclude_list:
            if fnmatch.fnmatch(relative_file_path, exclude):
                if verbose:
                    print(f"Excluding {relative_file_path} with rule {exclude}")
                do_exclude = True
                break
        if do_exclude:
            continue
        if check_if_exists(extensions_paths, relative_file_path, verbose):
            if os.path.isfile(full_file_path):
                duplicated_bytes += os.stat(full_file_path).st_size
            os.remove(full_file_path)
            if verbose:
                print(f"Removing duplicated file {relative_file_path} {full_file_path}")
    if not quiet:
        print(f"Removed {duplicated_bytes} bytes in duplicated files")


if __name__ == "__main__":
    verbose = args.verbose
    exclude = args.exclude
    extensions = args.extension
    quiet = args.quiet
    mapping = {}

    if exclude is not None:
        global_excludes += exclude

    extensions = get_extension_list(args.extension)
    if len(extensions) == 0:
        print("Called remove_common.py without a list of snaps, and no 'build-snaps' entry in the snapcraft.yaml file. Aborting.")
        sys.exit(1)

    mappings = generate_mappings(global_maps, args.map)

    if verbose:
        print(f"Removing duplicates already in {extensions}")

    extensions_paths = generate_extensions_paths(extensions, mappings)
    extensions_paths.append((os.environ["CRAFT_STAGE"], None))

    # This is the folder where to check for duplicates that are already
    # in other snaps, or in the stage because they were built in other
    # parts.
    snap_folder = os.environ["CRAFT_PART_INSTALL"]

    main(snap_folder, extensions_paths, global_excludes, verbose, quiet)
