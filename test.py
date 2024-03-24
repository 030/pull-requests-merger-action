import pytest
import unittest

from main import diffs, get_gh_action_name_and_tag, new_unique_names_and_tags, old_unique_names_and_tags, valid, valid_names, valid_tags, unique_names_and_tags

HELPER_TEST_DATA_DIR = "test/testdata/diff/"


def helper_read_test_file(path: str):
    file_path = HELPER_TEST_DATA_DIR+path
    with open(file_path, 'r') as file:
        file_content = file.read()
        return file_content


class TestPullRequestsMergerAction(unittest.TestCase):
    def test_diffs(self):
        test_cases = [
            {'path': "actions-checkout-combined-build-push-action-should-return-error.txt",
             'expected_old_lines': ['-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-        uses: docker/build-push-action@v5.1.0'
                                    ],
             'expected_new_lines': [
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+      - uses: actions/checkout@v4.1.2',
                 '+        uses: docker/build-push-action@v5.3.0'
             ]},
            {'path': "actions-checkout.txt",
             'expected_old_lines': ['-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.1',
                                    '-      - uses: actions/checkout@v4.1.0'],
             'expected_new_lines': ['+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2',
                                    '+      - uses: actions/checkout@v4.1.2']
             },
            {'path': "build-push-actions.txt",
             'expected_old_lines': ['-        uses: docker/build-push-action@v5.1.0'],
             'expected_new_lines': ['+        uses: docker/build-push-action@v5.3.0']
             },
            {'path': "login-action.txt",
             'expected_old_lines': ['-        uses: docker/login-action@v3.0.0'],
             'expected_new_lines': ['+        uses: docker/login-action@v3.1.0'],
             },
            {'path': "setup-buildx-action.txt",
             'expected_old_lines': ['-        uses: docker/setup-buildx-action@v3.1.0'],
             'expected_new_lines': ['+        uses: docker/setup-buildx-action@v3.2.0']
             },
            {'path': "upload-release-action.txt",
             'expected_old_lines': ['-        uses: svenstaro/upload-release-action@2.7.0',
                                    '-        uses: svenstaro/upload-release-action@2.7.0'],
             'expected_new_lines': ['+        uses: svenstaro/upload-release-action@2.9.0',
                                    '+        uses: svenstaro/upload-release-action@2.9.0']
             },
        ]

        for test_case in test_cases:
            actual_old_lines, actual_new_lines = diffs(helper_read_test_file(test_case['path']))

            self.assertEqual(actual_old_lines, test_case['expected_old_lines'])
            self.assertEqual(actual_new_lines, test_case['expected_new_lines'])

    def test_unique_names_and_tags(self):
        test_cases = [
            {'removed_and_replaced_lines': ['-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-      - uses: actions/checkout@v4.1.1',
                                            '+      - uses: actions/checkout@v4.1.2',
                                            '-        uses: docker/build-push-action@v5.1.0',
                                            '+        uses: docker/build-push-action@v5.3.0'],
             'expected_names': ['actions/checkout',
                                'docker/build-push-action'],
             'expected_tags': ['v4.1.1',
                               'v4.1.2',
                               'v5.1.0',
                               'v5.3.0']}
        ]

        for test_case in test_cases:
            unique_names, unique_tags = unique_names_and_tags(test_case['removed_and_replaced_lines'])
            self.assertCountEqual(unique_names, test_case['expected_names'])
            self.assertCountEqual(unique_tags, test_case['expected_tags'])

    def test_valid_names(self):
        test_cases = [
            {'unique_names': ['docker/build-push-action',
                              'actions/checkout'],
             'expected': False},
            {'unique_names': ['docker/build-push-action'],
             'expected': True},
        ]

        for test_case in test_cases:
            self.assertEqual(valid_names(test_case['unique_names']), test_case['expected'])

    def test_valid_tags(self):
        test_cases = [
            {'unique_tags': ['v4.1.2',
                             'v5.1.0',
                             'v4.1.1',
                             'v5.3.0'],
             'expected': False},
            {'unique_tags': ['v4.1.2',
                             'v5.3.0'],
             'expected': False},
            {'unique_tags': ['v4.1.2',
                             'v5.3.0',
                             'v1.2.3'],
             'expected': False},
        ]

        for test_case in test_cases:
            self.assertEqual(valid_tags(test_case['unique_tags'], False), test_case['expected'])

    def test_get_gh_action_name_and_tag_error(self):
        with pytest.raises(ValueError, match="name and/or not found"):
            get_gh_action_name_and_tag("hola")

    def test_diffs_error(self):
        with pytest.raises(ValueError, match="neither old_lines nor new_lines should be empty"):
            diffs("mundo")

    def test_old_unique_names_and_tags(self):
        with pytest.raises(ValueError, match="old_lines should start with a: '-'"):
            old_unique_names_and_tags(["mundo", "welt"])

    def test_new_unique_names_and_tags(self):
        with pytest.raises(ValueError, match=r"new_lines should start with a: '\+'"):
            new_unique_names_and_tags(["hello", "world"])


if __name__ == '__main__':
    unittest.main()
