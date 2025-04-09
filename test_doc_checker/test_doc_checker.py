#!/usr/bin/env python3

import os
import yaml
import fnmatch

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


def get_all_parts():
    """Get a list with the name of all the parts in the YAML file

    Returns
    -------
    array of strings
        A list of each of the parts of this project

    Raises
    ------
    FileNotFoundError
        Raised if the snapcraft.yaml file can't be found.
    """
    snapcraft_file = get_snapcraft_yaml()
    if snapcraft_file is None:
        raise FileNotFoundError("Can't find snapcraft.yaml file")
    with open(snapcraft_file, "r") as snapcraft_stream:
        snapcraft_data = yaml.load(snapcraft_stream, Loader=yaml.Loader)
    parts_data = {part_name:snapcraft_data["parts"][part_name] for part_name in snapcraft_data["parts"] }
    return parts_data


def get_parts_folder():
    """Returns the folder where the project parts are stored

    This allows to check the inner src folders for each part.

    Returns
    -------
    string
        A string with the path where all the parts are stored

    Raises
    ------
    Exception
        The function uses CRAFT_PART_SRC environment variable to extract
        the path for all the parts, so if it has an unexpected format, it
        won't be able to do it, and raises this exception.
    """
    src_folder = os.environ['CRAFT_PART_SRC']
    parts_string = '/parts/'
    pos = src_folder.find(parts_string)
    if pos == -1:
        raise Exception("CRAFT_PART_SRC has an unrecognized format")
    return src_folder[:pos + len(parts_string) - 1] # -1 to remove the trailing '/'


def get_meson_options_file_for_part(part_name):
    """Returns the contents of the meson_options.txt file for the specified part

    Parameters
    ----------
    part_name : string
        the part name

    Returns
    -------
    string or None
        The contents of the meson_options.txt for the specified part, or None if
        the file or the part doesn't exist.
    """
    parts_folder = get_parts_folder()

    meson_path = os.path.join(parts_folder, part_name, 'src', 'meson_options.txt')
    if not os.path.exists(meson_path):
        return None
    with open(meson_path, "r") as meson_file:
        data = meson_file.read()
    return data


def extract_option_value(data, option_name = None):
    """Extract the data for the specified option name, removing simple quotes if needed

    Parameters
    ----------
    data : string
        The sentence that contains all the options
    option_name : string or None
        The option name, with or without ':' at the end, or
        None if the data must be returned just from the beginning of the 'data' string.

    Returns
    -------
    string
        The value of the option, or None if there are
        no value.
    """
    if data.startswith('option('):
        data = data[len('option('):]
    if option_name is not None:
        if option_name[-1] != ':':
            option_name += ':'
        pos = data.find(option_name)
        if pos == -1:
            option_name = option_name[:-1] + ' :'
            pos = data.find(option_name)
            if pos == -1:
                return None
        data = data[pos + len(option_name):]
    data = data.strip()
    if len(data) == 0:
        return None
    if data[0] == "'":
        begin = 1
        end = data.find("'", 1)
        if end == -1:
            return None
    else:
        begin = 0
        end = data.find(",", begin+1)
        if end == -1:
            return None
    return data[begin: end]


def find_test_doc_options(part_name):
    """Finds the relevant options in the meson_options.txt file

    This function reads the meson_options.txt file and searches the options
    that could be relevant for building a snap. Specifically it searches for
    documentation, tests, vapi and gobject introspection options. The former
    two should be disabled, while the later two should be enabled.

    Parameters
    ----------
    part_name : string
        The part to search for options in the meson_options.txt file.

    Returns
    -------
    Array of dictionaries with these entries:
        * name: the meson option name
        * description: the description of the option
        * value: the default value of the option
        * type: the option type
        * desired: if that option should be enabled or disabled
    """
    options_list_disabled = ['doc*', 'test*', 'demo*']
    options_list_enabled = ['*vapi*', 'introspection']
    meson_data = get_meson_options_file_for_part(part_name)

    if meson_data is None:
        return []

    valid_options = []

    options = meson_data.split('option(')
    for option in options:
        option_name = extract_option_value(option)
        if option_name is None:
            continue
        option_description = extract_option_value(option, 'description:')
        option_value = extract_option_value(option, 'value:')
        option_type = extract_option_value(option, 'type:')

        for option_mask in options_list_disabled + options_list_enabled:
            if fnmatch.fnmatch(option_name, option_mask):
                valid_options.append({"desired": option_mask in options_list_enabled,
                                      "name": option_name,
                                      "description": option_description,
                                      "value": option_value,
                                      "type": option_type})
                break
    return valid_options


def find_meson_parameters_for_part(part_name):
    """Returns the list of meson parameters for a part

    Returns the configurable parameters (the ones with the form -Dxxxx) currently
    set in the snapcraft.yaml file for the specified part, and also its current value.

    Parameters
    ----------
    part_name : string
        The part to analyze

    Returns
    -------
    Dictionary
        Returns a dictionary where the key is the meson option, and the value is
        the value set for that option. It will return None if the part doesn't use
        the 'meson' plugin.
    """
    part_data = get_all_parts()[part_name]
    if part_data['plugin'] != 'meson':
        return None
    if 'meson-parameters' not in part_data:
        return {}
    parameters = {}
    for parameter in part_data['meson-parameters']:
        if not parameter.startswith('-D'):
            continue
        parameter = parameter[2:].split('=')
        parameters[parameter[0].strip()] = parameter[1].strip()
    return parameters


def find_missing_meson_options(part_name):
    parameters = find_meson_parameters_for_part(part_name)
    if parameters is None:
        return {}
    options = find_test_doc_options(part_name)
    if len(options) == 0:
        return {}

    missing_options = {}
    for option in options:
        if option["name"] in parameters:
            # if an option is already configured in snapcraft.yaml, jump over
            continue
        # if the default value is enabled and we want it that way, it doesn't need to be configured,
        # BUT is good to configure it anyway to allow the dependency checker to detect if a dependency
        # is missing.
        if (not option["desired"]) and option["value"] in ["false", "disabled"]:
            # if the default value is disabled and we want it that way, it doesn't need to be configured
            continue
        missing_options[option["name"]] = option
    return missing_options

def process_project():
    parts = get_all_parts()
    for part in parts:
        missing_options = find_missing_meson_options(part)
        if len(missing_options) == 0:
            continue
        print(f"Missing meson options for {part}:")
        for option_name in missing_options:
            option = missing_options[option_name]
            print(f"  {option_name}:")
            if option['description'] is not None:
                print(f"    description: {option['description']}")
            if option['value'] is not None:
                print(f"    value: {option['value']}")
            if option['type'] is not None:
                if option['type'] == 'boolean':
                    print(f"    should be '{'true' if option['desired'] else 'false'}'")
                elif option['type'] == 'feature':
                    print(f"    should be '{'enabled' if option['desired'] else 'disabled'}'")
                else:
                    print(f"    type: {option['type']}")

if __name__ == "__main__":
    process_project()
