#!/usr/bin/env python3

import os
import remove_common
import shutil
import unittest
import tempfile

ONLY_IN_INSTALL = 0
IN_BOTH = 1
ONLY_IN_BASE = 2

class base_system:
    def __init__(self):
        self._base_folder = tempfile.mkdtemp()
        self._snap_path = os.path.join(self._base_folder, "snaps")
        # this is the path for icons
        self._gtk_common_themes_path = os.path.join(self._snap_path, "gtk-common-themes")
        # this is the path for other files
        self._gnome_46_path = os.path.join(self._snap_path, "gnome-46")
        # this is the path where files already available at any of the previous folders must be deleted
        self._install_path = os.path.join(self._base_folder, "install")

        self._exclude = []
        for exclude in remove_common.global_excludes:
            self.add_exclude(exclude)

        os.makedirs(self._gtk_common_themes_path)
        os.makedirs(self._gnome_46_path)
        os.makedirs(self._install_path)

    def set_craft_project_dir(self, folder):
        os.environ['CRAFT_PROJECT_DIR'] = os.path.join(os.getcwd(), folder)

    def delete_folders(self):
        shutil.rmtree(self._base_folder)


    def create_icons_folder(self, name, mode):
        if (mode == ONLY_IN_INSTALL) or (mode == IN_BOTH):
            os.makedirs(os.path.join(self._gtk_common_themes_path, "share", "icons", name), exist_ok=True)
        if (mode == ONLY_IN_BASE) or (mode == IN_BOTH):
            os.makedirs(os.path.join(self._install_path, "usr", "share", "icons", name), exist_ok=True)

    def create_icon(self, theme, name, mode):
        self.create_icons_folder(theme, mode)
        if (mode == ONLY_IN_BASE) or (mode == IN_BOTH):
            self._create_empty_file(os.path.join(self._gtk_common_themes_path, "share", "icons", theme, name))
        if (mode == ONLY_IN_INSTALL) or (mode == IN_BOTH):
            self._create_empty_file(os.path.join(self._install_path, "usr", "share", "icons", theme, name))

    def create_folder(self, path, mode):
        if (mode == ONLY_IN_BASE) or (mode == IN_BOTH):
            os.makedirs(os.path.join(self._gnome_46_path, path), exist_ok=True)
        if (mode == ONLY_IN_INSTALL) or (mode == IN_BOTH):
            os.makedirs(os.path.join(self._install_path, path), exist_ok=True)

    def _create_empty_file(self, path):
        open(path, "w").close()

    def create_file(self, fullpath, mode):
        path, name = os.path.split(fullpath)
        self.create_folder(path, mode)
        if (mode == ONLY_IN_BASE) or (mode == IN_BOTH):
            self._create_empty_file(os.path.join(self._gnome_46_path, path, name))
        if (mode == ONLY_IN_INSTALL) or (mode == IN_BOTH):
            self._create_empty_file(os.path.join(self._install_path, path, name))

    def add_exclude(self, exclude):
        self._exclude.append(exclude)

    def remove_common(self):
        # maps must end in "/", like "usr/"
        maps = ((self._gnome_46_path, None), (self._gtk_common_themes_path, "usr/"))
        remove_common.main(self._install_path, [self._install_path], maps, self._exclude)

    def file_exists(self, path):
        full_path = os.path.join(self._install_path, path)
        return os.path.exists(full_path)

class TestRemoveCommon(unittest.TestCase):

    def test_dups_are_removed(self):
        b = base_system()
        b.create_file("usr/bin/a1", ONLY_IN_BASE)
        b.create_file("usr/bin/a2", ONLY_IN_INSTALL)
        b.create_file("usr/bin/a3", IN_BOTH)
        b.remove_common()
        self.assertFalse(b.file_exists("usr/bin/a1"))
        self.assertTrue(b.file_exists("usr/bin/a2"))
        self.assertFalse(b.file_exists("usr/bin/a3"))

    def test_theme_index_arent_removed(self):
        b = base_system()
        b.create_icon("hicolor", "icon1", IN_BOTH)
        b.create_icon("hicolor", "index.theme", IN_BOTH)
        b.remove_common()
        self.assertTrue(b.file_exists("usr/share/icons/hicolor/index.theme"))
        self.assertFalse(b.file_exists("usr/share/icons/hicolor/icon1"))

    def test_keep_file(self):
        b = base_system()
        b.create_file("usr/bin/a1", IN_BOTH)
        b.create_file("usr/bin/a2", IN_BOTH)
        b.create_file("usr/bin/a3", IN_BOTH)
        b.add_exclude("usr/bin/a2")
        b.remove_common()
        self.assertFalse(b.file_exists("usr/bin/a1"))
        self.assertTrue(b.file_exists("usr/bin/a2"))
        self.assertFalse(b.file_exists("usr/bin/a3"))

    def test_keep_folder(self):
        b = base_system()
        b.create_file("usr/bin/a1", IN_BOTH)
        b.create_file("usr/bin/a2", IN_BOTH)
        b.create_file("usr/bin/more/a3", IN_BOTH)
        b.create_file("usr/bin/more/another/a4", IN_BOTH)
        b.add_exclude("usr/bin/*")
        b.remove_common()
        self.assertTrue(b.file_exists("usr/bin/a1"))
        self.assertTrue(b.file_exists("usr/bin/a2"))
        self.assertTrue(b.file_exists("usr/bin/more/a3"))
        self.assertTrue(b.file_exists("usr/bin/more/another/a4"))

    # Configure function tests

    def test_get_extension_list_from_cmdline(self):
        extension_list = remove_common.get_extension_list(["extension1", "extension2"])
        self.assertEqual(len(extension_list), 2)
        self.assertTrue("extension1" in extension_list)
        self.assertTrue("extension2" in extension_list)

    def test_get_extension_list_from_file(self):
        b = base_system()
        b.set_craft_project_dir("test_files/project_1")
        extension_list = remove_common.get_extension_list([])
        self.assertEqual(len(extension_list), 4)
        self.assertIn("gnome-46-2404", extension_list)
        self.assertIn("mesa-2404", extension_list)
        self.assertIn("core24", extension_list)
        self.assertIn("gtk-common-themes", extension_list)

    def test_generated_mappings(self):
        mappings = remove_common.generate_mappings(["gtk-common-themes:usr"], ["snap1:/test1", "snap2:test2/"])
        self.assertIn("gtk-common-themes", mappings)
        self.assertEqual(mappings["gtk-common-themes"], "usr/")
        self.assertIn("snap1", mappings)
        self.assertEqual(mappings["snap1"], "test1/")
        self.assertIn("snap2", mappings)
        self.assertEqual(mappings["snap2"], "test2/")
        self.assertRaises(SyntaxError, remove_common.generate_mappings, ["snap1:/"], [])
        self.assertRaises(SyntaxError, remove_common.generate_mappings, ["snap1:usr:a"], [])

    def test_generate_folders(self):
        folders = remove_common.generate_extensions_paths(["gtk-common-themes", "core24"], {"gtk-common-themes": "usr/"})
        self.assertEqual(len(folders), 2)
        for entry in folders:
            self.assertEqual(len(entry), 2)
            self.assertIn(entry[0], ["/snap/gtk-common-themes/current", "/snap/core24/current"])
            if (entry[0] == "/snap/gtk-common-themes/current"):
                self.assertEqual(entry[1], "usr/")
            elif (entry[0] == "/snap/core24/current"):
                self.assertIsNone(entry[1])


if __name__ == '__main__':
    unittest.main()
