# Test meson options

This tool examines the *meson_options.txt* files in each part, searching for
options related with building documentation, tests, VAPI and Gobject-Introspection.
Then it compares them with the actual options set in the *snapcraft.yaml* file
and the desired values (*enabled* for VAPI and introspection, *disabled* for
documentation and tests), and print which options have an incorrect value in
each part, and the desired value.

It is useful for XXX-SDK snaps, which have too many parts to do this manually.

## Using it:

Just add this entry in your *snapcraft.yaml* file, and ensure that the script is
ran in *build*, *stage* or *prime*, never in *pull*. This is paramount to ensure
that all the source code for other parts have been downloaded and the *meson_options*
file is available in the each part folder.

  check-meson-options:
    plugin: nil
    source: https://github.com/sergio-costas/snap-build-tools.git
    source-depth: 1
    build-packages:
      - python3-yaml
    override-pull: |
      craftctl default
      $CRAFT_PART_SRC/install
    override-build: |
      $CRAFT_PROJECT_DIR/snapbuildtools/test_doc_checker.py
      craftctl default

If you already have downloaded the tools in a different part, just run the
*test_doc_checker.py* script in the *override-build* zone.
