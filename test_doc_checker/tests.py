#!/usr/bin/env python3

import os
import test_doc_checker

import unittest
import tempfile

class TestDocTestOptions(unittest.TestCase):

    def test_yaml_file(self):
        os.environ['CRAFT_PROJECT_DIR'] = os.path.join(os.getcwd(), 'test_data')
        parts = test_doc_checker.get_all_parts()
        self.assertEqual(len(parts), 64)
        self.assertIn('buildenv', parts)
        self.assertIn('ninja', parts) # just two of them are enough
        self.assertEqual(len(parts['ninja']), 6)

    def test_yaml_file_fails(self):
        os.environ['CRAFT_PROJECT_DIR'] = os.path.join(os.getcwd())
        self.assertRaises(FileNotFoundError, test_doc_checker.get_all_parts)

    def test_parts_folder(self):
        true_parts_path = os.path.join(os.getcwd(),'test_data', 'parts')
        os.environ['CRAFT_PART_SRC'] = os.path.join(true_parts_path, 'main_test', 'src')
        parts_path = test_doc_checker.get_parts_folder()
        self.assertEqual(parts_path, true_parts_path)

    def test_get_meson_options_file(self):
        true_parts_path = os.path.join(os.getcwd(),'test_data', 'parts')
        os.environ['CRAFT_PART_SRC'] = os.path.join(true_parts_path, 'main_test', 'src')

        meson_options_file = test_doc_checker.get_meson_options_file_for_part('harfbuzz')
        self.assertIsNotNone(meson_options_file)

    def test_get_non_existent_meson_options_file(self):
        true_parts_path = os.path.join(os.getcwd(),'test_data', 'parts')
        os.environ['CRAFT_PART_SRC'] = os.path.join(true_parts_path, 'main_test', 'src')

        meson_options_file = test_doc_checker.get_meson_options_file_for_part('part3')
        self.assertIsNone(meson_options_file)

    def test_get_non_existent_part_meson_options_file(self):
        true_parts_path = os.path.join(os.getcwd(),'test_data', 'parts')
        os.environ['CRAFT_PART_SRC'] = os.path.join(true_parts_path, 'main_test', 'src')

        meson_options_file = test_doc_checker.get_meson_options_file_for_part('part4')
        self.assertIsNone(meson_options_file)

    def test_get_options_harfbuzz(self):
        options = test_doc_checker.find_test_doc_options('harfbuzz')
        self.assertEqual(len(options), 4)
        for option in options:
            self.assertIn(option["name"], ['tests', 'introspection', 'docs', 'doc_tests'])

    def test_get_options_part2(self):
        options = test_doc_checker.find_test_doc_options('part2')
        self.assertEqual(len(options), 0)

    def test_get_options_part3(self):
        options = test_doc_checker.find_test_doc_options('part3')
        self.assertEqual(len(options), 0)

    def test_get_part_data(self):
        parameters = test_doc_checker.find_meson_parameters_for_part('harfbuzz')
        self.assertEqual(len(parameters), 5)
        self.assertIn('graphite2', parameters)
        self.assertIn('introspection', parameters)
        self.assertIn('gobject', parameters)
        self.assertIn('optimization', parameters)
        self.assertIn('debug', parameters)

    def test_find_missing_meson_options(self):
        os.environ['CRAFT_PROJECT_DIR'] = os.path.join(os.getcwd(), 'test_data')
        os.environ['CRAFT_PART_SRC'] = os.path.join(os.getcwd(),'test_data', 'parts', 'main_test', 'src')
        missing_options = test_doc_checker.find_missing_meson_options('harfbuzz')
        self.assertEqual(len(missing_options), 2)
        self.assertIn('tests', missing_options)
        self.assertIn('docs', missing_options)

    def test_extract_option_value(self):
        data = "option('graphite', type: 'feature', value: false, description: 'Deprecated use graphite2 option instead')"
        option_name = test_doc_checker.extract_option_value(data)
        self.assertEqual(option_name, 'graphite')
        option_type = test_doc_checker.extract_option_value(data, 'type:')
        self.assertEqual(option_type, 'feature')
        option_value = test_doc_checker.extract_option_value(data, 'value:')
        self.assertEqual(option_value, 'false')
        option_description = test_doc_checker.extract_option_value(data, 'description:')
        self.assertEqual(option_description, 'Deprecated use graphite2 option instead')
        option_invalid = test_doc_checker.extract_option_value(data, 'non-existent-option:')
        self.assertIsNone(option_invalid)

    def test_extract_option_value2(self):
        option_name = test_doc_checker.extract_option_value('')
        self.assertIsNone(option_name)

    def test_extract_option_value3(self):
        data = "option('graphite', type : 'feature', value : false, description : 'Deprecated use graphite2 option instead')"
        option_name = test_doc_checker.extract_option_value(data)
        self.assertEqual(option_name, 'graphite')
        option_type = test_doc_checker.extract_option_value(data, 'type:')
        self.assertEqual(option_type, 'feature')
        option_value = test_doc_checker.extract_option_value(data, 'value:')
        self.assertEqual(option_value, 'false')
        option_description = test_doc_checker.extract_option_value(data, 'description:')
        self.assertEqual(option_description, 'Deprecated use graphite2 option instead')
        option_invalid = test_doc_checker.extract_option_value(data, 'non-existent-option:')
        self.assertIsNone(option_invalid)



if __name__ == '__main__':
    unittest.main()
