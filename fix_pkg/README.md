# FIX_PKG

Analyzes a .pc file from pkgconfig and modifies the *prefix*
variable to contain the specific value passed, and also all the other
variables to point to *$prefix/...*.

# RATIONALE

Some builders create wrong *pkgconfig*, where the paths are fixed and
don't make use of *$prefix* variable. In some cases, even the *prefix*
variable is wrong, and doesn't match the right place.

FIX_PGK reads the *.pc* file and replaces the *prefix* variable with a
value passed in the command line. It also modifies any variable that is
set to */usr/...*, adding *$prefix* before and, thus, ensuring that they
point to the right place.

## How to use it

After installing the *snap-build-tools*, just add this in the right
place of your *snapcraft.yaml* file:

    $CRAFT_PROJECT_DIR/snapbuildtools/fix_pkg.py   PATH_TO_THE_PC_FILE   NEW_PREFIX

Usually, NEW_PREFIX should be $CRAFT_STAGE.

If NEW_PREFIX isn't passed, the *prefix* variable won't be modified.

Also, if NEW_PREFIX ends in /usr, that part will be removed.