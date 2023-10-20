# SNAP BUILD TOOLS

This is a set of tools useful to be used inside snapcraft.yaml to
simplify the process of snapping applications. The idea is to group
several common tools used during the snap process into a single,
easily accesible, repository.

## Available tools

* remove_common: it replaces the old, bash-based, code to remove
duplicated files in the snap from the CoreXX and Gnome-YY base snaps.
It is safer and faster.

* set_python_runtime: very useful for python3 programs that make use
of the Gnome extension snap. It ensures that the *shebang* in all the
python scripts point to */usr/bin/env python3* instead of pointing to
the python executable located in the Gnome SDK snap.

* parse_env: stores the environment variables in a file during a
part build, allowing to restore them inside the container to do
tests in case there is a problem during the build operation.

* fix_pkg: analyzes a .pc file from pkgconfig and modifies the *prefix*
variable to contain the specific value passed, and also all the other
variables to point to *$prefix/...*.

## How to use it

Just add this in your *parts*:

      snapbuildtools:
        source: https://github.com/sergio-costas/snap-build-tools.git
        source-depth: 1
        plugin: nil
        override-pull: |
          craftctl default
          $CRAFT_PART_SRC/install

and ensure that all the other parts in your system have an

    after: [snapbuildtools]

into them to ensure that this is installed before any other part. This
piece of YAML installs all the tools inside the projects folder when
snapcraft is launched.

Once you have it, you can use any tool from any other part. For example,
to call *set_python_runtime.py* to ensure that all python scripts in the
final stage begin with the *#!/usr/bin/env python3* shebang, just do:

    $CRAFT_PROJECT_DIR/snapbuildtools/set_python_runtime.py $CRAFT_STAGE

Each tool has its own README.md explaining how to use it.

If, for some reason, there is already a folder called *snapbuildtools* in the
project dir, you can install the tools in a different folder just by
adding a folder name after *$CRAFT_PART_SRC/install*.
