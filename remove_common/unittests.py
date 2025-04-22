#!/usr/bin/env python3

""" Unitary tests for snapmodule """

import unittest
import os
from pathlib import Path
import shutil
import tempfile
import remove_common


class BaseTest(unittest.TestCase):

    def setUp(self):
        self._base_test_folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._base_test_folder)

    def _touch_file(self, relative_path, contents="a", symlink=None):
        """ Creates a file with the specified path/name, ensuring
            that it is inside the test folder.

            Parameters
            ----------
            relative_path : string
                The path where the file will be created. If it isn't a relative
                path, it will be made relative, and create the file inside the
                temporary folder.
            contents : string
                The data to be stored inside the created file.
            symlink : string
                A symlink name. If it's not None, along with the file, a symlink
                will be created in the same folder, pointing to the created file.

            Returns
            -------
            string or [string, string]

            If no symlink is specified, it will return the full path of the created
            file; if symlink is specified, it will return an array with the full
            paths for both the created file and the symlink.
        """
        if relative_path[0] == os.sep:
            relative_path = relative_path[1:]

        full_path = os.path.join(self._base_test_folder, relative_path)
        file_path, file_name = os.path.split(full_path)

        Path(file_path).mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding='utf-8') as fobject:
            fobject.write(contents) # just ensure that the file contains something
        if symlink is None:
            return full_path
        symlink_path = os.path.join(file_path, symlink)
        os.symlink(file_name, symlink_path)
        return [full_path, symlink_path]


class TestRemoveCommon(BaseTest):
    """ Tests that duplicated files are correctly removed """

    def _create_files(self):
        self._touch_file("core22/current/usr/bin/file1.txt")
        self._touch_file("core22/current/usr/bin/file2.txt")
        self._touch_file("core22/current/usr/lib/file1.txt")
        self._touch_file("gnome-42-2204/current/bin/file1.txt")
        self._touch_file("gnome-42-2204/current/share/file1.txt")
        self._touch_file("gnome-42-2204/current/share/file2.txt")

        final_files = []
        final_files.append(self._touch_file("stage/usr/bin/file1.txt"))
        final_files.append(self._touch_file("stage/usr/bin/file2.txt"))
        final_files.append(self._touch_file("stage/usr/bin/file3.txt"))
        final_files.append(self._touch_file("stage/usr/lib/file1.txt"))
        final_files.append(self._touch_file("stage/usr/lib/file2.txt"))
        final_files.append(self._touch_file("stage/usr/share/file1.txt"))
        final_files.append(self._touch_file("stage/usr/share/file2.txt"))
        final_files.append(self._touch_file("stage/usr/share/file3.txt"))
        final_files.append(self._touch_file("stage/etc/file1.txt"))
        return final_files

    def test_basic_test(self):
        """ Basic test

        Creates several files in two emulated snaps, and some repeated
        and non-repeated files in an emulated stage, and checks that
        only the duplicated files are removed. """

        final_files = self._create_files()
        config = remove_common.Configuration(extensions = ["core22", "gnome-42-2204"],
                                             mappings = ["gnome-42-2204:usr"],
                                             snap_prefix = self._base_test_folder,
                                             quiet = True)
        remove_common.main(snap_folder = os.path.join(self._base_test_folder, "stage"),
                           config = config)
        assert not os.path.exists(final_files[0])
        assert not os.path.exists(final_files[1])
        assert os.path.exists(final_files[2])
        assert not os.path.exists(final_files[3])
        assert os.path.exists(final_files[4])
        assert not os.path.exists(final_files[5])
        assert not os.path.exists(final_files[6])
        assert os.path.exists(final_files[7])
        assert os.path.exists(final_files[8])

    def test_execute(self):
        """ Execution test

        Same than Basic test, but running it from command line instead. """

        final_files = self._create_files()
        os.environ["CRAFT_PART_INSTALL"] = os.path.join(self._base_test_folder, "stage")
        os.system(f"./remove_common.py --quiet core22 gnome-42-2204 --map gnome-42-2204:usr --snap-prefix={self._base_test_folder}")
        assert not os.path.exists(final_files[0])
        assert not os.path.exists(final_files[1])
        assert os.path.exists(final_files[2])
        assert not os.path.exists(final_files[3])
        assert os.path.exists(final_files[4])
        assert not os.path.exists(final_files[5])
        assert not os.path.exists(final_files[6])
        assert os.path.exists(final_files[7])
        assert os.path.exists(final_files[8])


    def test_symlinks(self):
        """ Test symlinks """
        self._touch_file("core22/current/usr/bin/file1.txt")
        self._touch_file("core22/current/usr/bin/file2.txt")
        self._touch_file("gnome-42-2204/current/bin/file1.txt")
        self._touch_file("gnome-42-2204/current/bin/file2.txt")
        self._touch_file("gnome-42-2204/current/bin/dangling_dup.txt")

        file_with_symlink1 = self._touch_file("stage/usr/bin/file1.txt", "this is symlinked1", "file1_symlink.txt")
        file_with_symlink2 = self._touch_file("stage/usr/bin/file2.txt", "this is symlinked2", "file2_symlink.txt")
        # symlink to symlink
        double_symlink = os.path.join(self._base_test_folder,"stage/usr/bin/file1_double_symlink.txt")
        os.symlink("file1_symlink.txt", double_symlink)
        # and extra symlink
        extra_symlink = os.path.join(self._base_test_folder,"stage/usr/bin/file1_symlink2.txt")
        os.symlink("file1.txt", extra_symlink)
        dangling_symlink = os.path.join(self._base_test_folder,"stage/usr/bin/dangling.txt")
        os.symlink("../nofolder/file_dangling.txt", dangling_symlink)

        duplicated_dangling_symlink = os.path.join(self._base_test_folder,"stage/usr/bin/dangling_dup.txt")
        os.symlink("../nofolder/file_dangling_dup.txt", duplicated_dangling_symlink)

        config = remove_common.Configuration(extensions = ["core22", "gnome-42-2204"],
                                             mappings = ["gnome-42-2204:usr"],
                                             snap_prefix = self._base_test_folder,
                                             quiet = True)
        remove_common.main(snap_folder = os.path.join(self._base_test_folder, "stage"),
                           config = config)
        assert not os.path.exists(file_with_symlink1[0])
        assert not os.path.exists(file_with_symlink2[0])
        assert os.path.lexists(file_with_symlink1[1])
        assert os.path.lexists(file_with_symlink2[1])
        assert os.path.exists(file_with_symlink1[1])
        assert os.path.exists(file_with_symlink2[1])
        with open(file_with_symlink1[1], "r") as link1:
            data = link1.read()
            assert data == "this is symlinked1"
        with open(double_symlink, "r") as link1:
            data = link1.read()
            assert data == "this is symlinked1"
        with open(file_with_symlink2[1], "r") as link2:
            data = link2.read()
            assert data == "this is symlinked2"

unittest.main()
