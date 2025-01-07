#!/usr/bin/env python3

""" Unitary tests for snapmodule """

import unittest
import os
from pathlib import Path
import shutil
import remove_common


class TestRemoveCommon(unittest.TestCase):
    """ Test class """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._base_test_folder = "/tmp/tests"

    def _touch_file(self, relative_path):
        if relative_path[0] == os.sep:
            relative_path = relative_path[1:]

        full_path = os.path.join(self._base_test_folder, relative_path)
        file_path, _ = os.path.split(full_path)

        Path(file_path).mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding='utf-8') as fobject:
            fobject.write("a")
        return full_path

    def _create_files(self):
        self._touch_file("core22/usr/bin/file1.txt")
        self._touch_file("core22/usr/bin/file2.txt")
        self._touch_file("core22/usr/lib/file1.txt")
        self._touch_file("gnome-42-2204/bin/file1.txt")
        self._touch_file("gnome-42-2204/share/file1.txt")
        self._touch_file("gnome-42-2204/share/file2.txt")

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

    def _delete_files(self):
        shutil.rmtree(self._base_test_folder)

    def test_basic_test(self):
        """ This test creates several files in two emulated snaps, and
            some repeated and non-repeated files in an emulated stage,
            and checks that only the duplicated files are removed. """

        final_files = self._create_files()
        remove_common.main("/tmp/tests/stage", [("/tmp/tests/core22", None), ("/tmp/tests/gnome-42-2204", "usr/")])
        assert not os.path.exists(final_files[0])
        assert not os.path.exists(final_files[1])
        assert os.path.exists(final_files[2])
        assert not os.path.exists(final_files[3])
        assert os.path.exists(final_files[4])
        assert not os.path.exists(final_files[5])
        assert not os.path.exists(final_files[6])
        assert os.path.exists(final_files[7])
        assert os.path.exists(final_files[8])
        self._delete_files()

    def test_basic_test0(self):
        """ This test creates several files in two emulated snaps, and
            some repeated and non-repeated files in an emulated stage,
            and checks that only the duplicated files are removed. """

        final_files = self._create_files()
        remove_common.main("/tmp/tests/stage", [("/tmp/tests/core22", None), ("/tmp/tests/gnome-42-2204", "usr/")])
        assert not os.path.exists(final_files[0])
        assert not os.path.exists(final_files[1])
        assert os.path.exists(final_files[2])
        assert not os.path.exists(final_files[3])
        assert os.path.exists(final_files[4])
        assert not os.path.exists(final_files[5])
        assert not os.path.exists(final_files[6])
        assert os.path.exists(final_files[7])
        assert os.path.exists(final_files[8])
        self._delete_files()

unittest.main()
