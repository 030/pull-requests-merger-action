import json
import pytest
import unittest
import logging
from unittest.mock import patch, mock_open
from main import (
    key_exists_in_category,
    diffs,
    get_actual_commit_sha,
    get_name_and_version,
    new_unique_names_and_tags,
    old_unique_names_and_tags,
    package_name_and_tag_are_unique,
    valid,
    valid_commit_sha,
    valid_names,
    valid_tags,
    unique_names_and_tags,
)

HELPER_TEST_DATA_DIR = "test/testdata/diff/"


def helper_read_test_file(path: str):
    file_path = HELPER_TEST_DATA_DIR + path
    with open(file_path, "r") as file:
        file_content = file.read()
        return file_content


def test_get_name_and_version_valid_input_action():
    input_str = "uses: some-action@v1.2.3"
    expected = ("some-action", "v1.2.3", "github-actions")
    assert get_name_and_version(input_str) == expected


def test_get_name_and_version_valid_input_dockerfile():
    input_str = "FROM alpine:3.20.1"
    expected = ("alpine", "3.20.1", "docker")
    assert get_name_and_version(input_str) == expected


def test_get_name_and_version_valid_input_dockerfile_slashes():
    input_str = "FROM some/docker/file:1.2.3"
    expected = ("some/docker/file", "1.2.3", "docker")
    assert get_name_and_version(input_str) == expected


def test_get_name_and_version_valid_input_golang():
    input_str = "go 1.2.3"
    expected = ("go", "1.2.3", "golang")
    assert get_name_and_version(input_str) == expected


def test_get_name_and_version_valid_input_golang_modules():
    input_str = "github.com/frankban/quicktest v1.14.3"
    expected = ("github.com/frankban/quicktest", "v1.14.3", "golang")
    assert get_name_and_version(input_str) == expected


def test_get_name_and_version_invalid_input():
    input_str = "invalid input"
    with pytest.raises(ValueError, match="name and/or tag not found"):
        get_name_and_version(input_str)


def test_get_name_and_version_partial_input():
    input_str = "uses: some-action@"
    with pytest.raises(ValueError, match="name and/or tag not found"):
        get_name_and_version(input_str)


class TestPackageNameAndTag(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    @patch(
        "__main__.valid_names", return_value=True
    )  # Adjust the import path based on your structure
    @patch(
        "__main__.valid_tags", return_value=True
    )  # Adjust the import path based on your structure
    def test_valid_names_and_tags(self, mock_valid_tags, mock_valid_names):
        unique_names = ["packageA"]
        unique_tags = ["v1.0"]
        greater_than_or_equal = True
        package_type = "docker"

        name, tag = package_name_and_tag_are_unique(
            unique_names, unique_tags, greater_than_or_equal, package_type
        )

        self.assertEqual(name, "packageA")
        self.assertEqual(tag, "v1.0")

    @patch("__main__.valid_names", return_value=False)
    @patch("__main__.valid_tags", return_value=True)
    def test_invalid_names(self, mock_valid_tags, mock_valid_names):
        unique_names = ["packageA", "packageA"]  # Duplicate name
        unique_tags = ["v1.0"]
        greater_than_or_equal = True
        package_type = "docker"

        with self.assertRaises(ValueError) as context:
            package_name_and_tag_are_unique(
                unique_names, unique_tags, greater_than_or_equal, package_type
            )

        self.assertEqual(
            str(context.exception), "nor the names, neither the tags are unique"
        )

    @patch("__main__.valid_names", return_value=True)
    @patch("__main__.valid_tags", return_value=False)
    def test_invalid_tags(self, mock_valid_tags, mock_valid_names):
        unique_names = ["packageA"]
        unique_tags = ["v1.0", "v1.0"]  # Duplicate tag
        greater_than_or_equal = True
        package_type = "docker"

        with self.assertRaises(ValueError) as context:
            package_name_and_tag_are_unique(
                unique_names, unique_tags, greater_than_or_equal, package_type
            )

        self.assertEqual(
            str(context.exception), "nor the names, neither the tags are unique"
        )


class TestPullRequestsMergerAction(unittest.TestCase):
    def test_diffs(self):
        test_cases = [
            {
                "path": "actions-checkout-combined-build-push-action-should-return-error.txt",
                "expected_old_lines": [
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-        uses: docker/build-push-action@v5.1.0",
                ],
                "expected_new_lines": [
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+        uses: docker/build-push-action@v5.3.0",
                ],
            },
            {
                "path": "actions-checkout.txt",
                "expected_old_lines": [
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.1",
                    "-      - uses: actions/checkout@v4.1.0",
                ],
                "expected_new_lines": [
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                    "+      - uses: actions/checkout@v4.1.2",
                ],
            },
            {
                "path": "build-push-actions.txt",
                "expected_old_lines": [
                    "-        uses: docker/build-push-action@v5.1.0"
                ],
                "expected_new_lines": [
                    "+        uses: docker/build-push-action@v5.3.0"
                ],
            },
            {
                "path": "dockerfile-alpine.txt",
                "expected_old_lines": ["-FROM alpine:3.17.1"],
                "expected_new_lines": ["+FROM alpine:3.20.1"],
            },
            {
                "path": "login-action.txt",
                "expected_old_lines": [
                    "-        uses: docker/login-action@v3.0.0"
                ],
                "expected_new_lines": [
                    "+        uses: docker/login-action@v3.1.0"
                ],
            },
            {
                "path": "setup-buildx-action.txt",
                "expected_old_lines": [
                    "-        uses: docker/setup-buildx-action@v3.1.0"
                ],
                "expected_new_lines": [
                    "+        uses: docker/setup-buildx-action@v3.2.0"
                ],
            },
            {
                "path": "upload-release-action.txt",
                "expected_old_lines": [
                    "-        uses: svenstaro/upload-release-action@2.7.0",
                    "-        uses: svenstaro/upload-release-action@2.7.0",
                ],
                "expected_new_lines": [
                    "+        uses: svenstaro/upload-release-action@2.9.0",
                    "+        uses: svenstaro/upload-release-action@2.9.0",
                ],
            },
        ]

        for test_case in test_cases:
            actual_old_lines, actual_new_lines = diffs(
                helper_read_test_file(test_case["path"])
            )

            self.assertEqual(actual_old_lines, test_case["expected_old_lines"])
            self.assertEqual(actual_new_lines, test_case["expected_new_lines"])

    def test_unique_names_and_tags(self):
        test_cases = [
            {
                "removed_and_replaced_lines": [
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-      - uses: actions/checkout@v4.1.1",
                    "+      - uses: actions/checkout@v4.1.2",
                    "-        uses: docker/build-push-action@v5.1.0",
                    "+        uses: docker/build-push-action@v5.3.0",
                ],
                "expected_names": [
                    "actions/checkout",
                    "docker/build-push-action",
                ],
                "expected_tags": ["v4.1.1", "v4.1.2", "v5.1.0", "v5.3.0"],
                "expected_package_type": "github-actions",
            }
        ]

        for test_case in test_cases:
            unique_names, unique_tags, package_type = unique_names_and_tags(
                test_case["removed_and_replaced_lines"]
            )
            self.assertCountEqual(unique_names, test_case["expected_names"])
            self.assertCountEqual(unique_tags, test_case["expected_tags"])
            self.assertEqual(package_type, test_case["expected_package_type"])

    def test_valid_names(self):
        test_cases = [
            {
                "unique_names": [
                    "docker/build-push-action",
                    "actions/checkout",
                ],
                "expected": False,
            },
            {"unique_names": ["docker/build-push-action"], "expected": True},
        ]

        for test_case in test_cases:
            self.assertEqual(
                valid_names(test_case["unique_names"]), test_case["expected"]
            )

    def test_valid_tags(self):
        test_cases = [
            {
                "unique_tags": ["v4.1.2", "v5.1.0", "v4.1.1", "v5.3.0"],
                "expected": False,
            },
            {"unique_tags": ["v4.1.2", "v5.3.0"], "expected": False},
            {"unique_tags": ["v4.1.2", "v5.3.0", "v1.2.3"], "expected": False},
        ]

        for test_case in test_cases:
            self.assertEqual(
                valid_tags(test_case["unique_tags"], False),
                test_case["expected"],
            )

    def test_get_gh_action_name_and_tag_error(self):
        with pytest.raises(ValueError, match="name and/or tag not found"):
            get_name_and_version("hola")

    def test_diffs_error(self):
        with pytest.raises(
            ValueError, match="neither old_lines nor new_lines should be empty"
        ):
            diffs("mundo")

    def test_old_unique_names_and_tags(self):
        with pytest.raises(
            ValueError, match="old_lines should start with a: '-'"
        ):
            old_unique_names_and_tags(["mundo", "welt"])

    def test_new_unique_names_and_tags(self):
        with pytest.raises(
            ValueError, match=r"new_lines should start with a: '\+'"
        ):
            new_unique_names_and_tags(["hello", "world"])


class TestValidFunction(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    def test_valid_length_equal(self):
        result = valid(["a", "b", "c"], 3, True)
        self.assertTrue(result)

    def test_valid_length_greater(self):
        result = valid(["a", "b", "c", "d"], 3, True)
        self.assertTrue(result)

    def test_invalid_length_less(self):
        result = valid(["a", "b"], 3, True)
        self.assertFalse(result)

    def test_valid_length_exact(self):
        result = valid(["a", "b", "c"], 3, False)
        self.assertTrue(result)

    def test_invalid_length_not_equal(self):
        result = valid(["a", "b", "c"], 4, False)
        self.assertFalse(result)

    def test_empty_list_valid_length_zero(self):
        result = valid([], 0, True)
        self.assertTrue(result)

    def test_empty_list_valid_length_one(self):
        result = valid([], 1, True)
        self.assertFalse(result)


class TestValidCommitSHA(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"packages": {"package_name": {"v1.0": "abc123"}}}',
    )
    def test_valid_sha(self, mock_file):
        actual_sha = "abc123"
        name = "package_name"
        tag = "v1.0"
        path = "fake_path.json"

        result = valid_commit_sha(actual_sha, name, path, tag)
        self.assertTrue(result)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"packages": {"package_name": {"v1.0": "abc123"}}}',
    )
    def test_invalid_sha(self, mock_file):
        actual_sha = "xyz456"
        name = "package_name"
        tag = "v1.0"
        path = "fake_path.json"

        result = valid_commit_sha(actual_sha, name, path, tag)
        self.assertFalse(result)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"packages": {"package_name": {"v1.0": ""}}}',
    )
    def test_empty_expected_sha(self, mock_file):
        actual_sha = "abc123"
        name = "package_name"
        tag = "v1.0"
        path = "fake_path.json"

        with self.assertRaises(ValueError) as context:
            valid_commit_sha(actual_sha, name, path, tag)

        self.assertEqual(
            str(context.exception),
            "no expected checksum found in file: fake_path.json",
        )

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_file):
        actual_sha = "abc123"
        name = "package_name"
        tag = "v1.0"
        path = "fake_path.json"

        with self.assertRaises(FileNotFoundError):
            valid_commit_sha(actual_sha, name, path, tag)


class TestPackageNameAndTag(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    @patch(
        "main.valid_names", return_value=True
    )  # Adjust this path accordingly
    @patch("main.valid_tags", return_value=True)  # Adjust this path accordingly
    def test_valid_names_and_tags(self, mock_valid_tags, mock_valid_names):
        unique_names = ["packageA"]
        unique_tags = ["v1.0"]
        greater_than_or_equal = True
        package_type = "docker"

        name, tag = package_name_and_tag_are_unique(
            unique_names, unique_tags, greater_than_or_equal, package_type
        )

        self.assertEqual(name, "packageA")
        self.assertEqual(tag, "v1.0")

    @patch(
        "main.valid_names", return_value=False
    )  # Adjust this path accordingly
    @patch("main.valid_tags", return_value=True)  # Adjust this path accordingly
    def test_invalid_names(self, mock_valid_tags, mock_valid_names):
        unique_names = ["packageA", "packageA"]  # Duplicate name
        unique_tags = ["v1.0"]
        greater_than_or_equal = True
        package_type = "docker"

        with self.assertRaises(ValueError) as context:
            package_name_and_tag_are_unique(
                unique_names, unique_tags, greater_than_or_equal, package_type
            )

        self.assertEqual(
            str(context.exception), "nor the names, neither the tags are unique"
        )

    @patch(
        "main.valid_names", return_value=True
    )  # Adjust this path accordingly
    @patch(
        "main.valid_tags", return_value=False
    )  # Adjust this path accordingly
    def test_invalid_tags(self, mock_valid_tags, mock_valid_names):
        unique_names = ["packageA"]
        unique_tags = ["v1.0", "v1.0"]  # Duplicate tag
        greater_than_or_equal = True
        package_type = "docker"

        with self.assertRaises(ValueError) as context:
            package_name_and_tag_are_unique(
                unique_names, unique_tags, greater_than_or_equal, package_type
            )

        self.assertEqual(
            str(context.exception), "nor the names, neither the tags are unique"
        )


class TestGetActualCommitSHA(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    @patch("requests.get")
    def test_valid_commit_sha(self, mock_get):
        # Mock the response data for a successful request
        mock_response = {
            "tags": [
                {"name": "v1.0", "commit": {"sha": "abc123"}},
                {"name": "v1.1", "commit": {"sha": "def456"}},
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response["tags"]

        name = "owner/repo"
        tag_to_be_found = "v1.1"

        commit_sha = get_actual_commit_sha(name, tag_to_be_found)

        self.assertEqual(commit_sha, "def456")

    @patch("requests.get")
    def test_tag_not_found(self, mock_get):
        # Mock the response data for a successful request with no matching tag
        mock_response = {
            "tags": [
                {"name": "v1.0", "commit": {"sha": "abc123"}},
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response["tags"]

        name = "owner/repo"
        tag_to_be_found = "v1.1"  # This tag does not exist

        commit_sha = get_actual_commit_sha(name, tag_to_be_found)

        self.assertEqual(commit_sha, "")

    @patch("requests.get")
    def test_error_response(self, mock_get):
        # Mock a failed response
        mock_get.return_value.status_code = 404  # Not Found

        name = "owner/repo"
        tag_to_be_found = "v1.0"

        commit_sha = get_actual_commit_sha(name, tag_to_be_found)

        self.assertEqual(commit_sha, "")


class TestCheckStringInJson(unittest.TestCase):

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=json.dumps(
            {
                "docker": ["alpine"],
                "github-actions": [
                    "030/gomod-go-version-updater-action",
                    "030/settings-action",
                    "actions/checkout",
                    "actions/setup-go",
                    "codecov/codecov-action",
                    "docker/build-push-action",
                    "docker/login-action",
                    "docker/setup-buildx-action",
                    "docker/setup-qemu-action",
                    "hadolint/hadolint-action",
                    "svenstaro/upload-release-action",
                ],
                "golang": [],
            }
        ),
    )
    def test_string_found(self, mock_file):
        file_path = "fake_path.json"

        with open(file_path) as f:
            data = json.load(f)

        target_string = "actions/checkout"
        category = "github-actions"
        result = key_exists_in_category(data, category, target_string)

        self.assertTrue(result)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=json.dumps(
            {
                "docker": ["alpine"],
                "github-actions": [
                    "030/gomod-go-version-updater-action",
                    "030/settings-action",
                    "actions/setup-go",
                    "codecov/codecov-action",
                    "docker/build-push-action",
                    "docker/login-action",
                    "docker/setup-buildx-action",
                    "docker/setup-qemu-action",
                    "hadolint/hadolint-action",
                    "svenstaro/upload-release-action",
                ],
                "golang": [],
            }
        ),
    )
    def test_string_not_found(self, mock_file):
        file_path = "fake_path.json"

        with open(file_path) as f:
            data = json.load(f)

        target_string = "non-existent-action"
        category = "github-actions"
        result = key_exists_in_category(data, category, target_string)

        self.assertFalse(result)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({}))
    def test_empty_json(self, mock_file):
        file_path = "fake_path.json"

        with open(file_path) as f:
            data = json.load(f)

        target_string = "any-action"
        category = "github-actions"
        result = key_exists_in_category(data, category, target_string)

        self.assertFalse(result)


def mock_unique_names_and_tags(new_lines):
    # This is a simple mock implementation. Adjust it as needed for your tests.
    unique_names = [
        line[1:] for line in new_lines
    ]  # Remove the '+' from the start
    unique_tags = ["tag_" + line[1:] for line in new_lines]  # Just a mock tag
    return unique_names, unique_tags


class TestNewUniqueNamesAndTags:

    def test_valid_input(self):
        new_lines = [
            "+google.golang.org/protobuf v1.33.0",
            "+google.golang.org/protobuf v1.33.0",
        ]
        expected_names = ["golang.org/protobuf"]
        expected_tags = ["v1.33.0"]  # From mock
        expected_package_type = "golang"  # From mock

        result = new_unique_names_and_tags(new_lines)
        assert result == (expected_names, expected_tags, expected_package_type)

    def test_invalid_input_missing_plus(self):
        new_lines = [
            "+package1",
            "package2",  # This line does not start with "+"
            "+package3",
        ]
        with pytest.raises(
            ValueError, match="new_lines should start with a: '\\+'"
        ):
            new_unique_names_and_tags(new_lines)

    # def test_empty_input(self):
    #     new_lines = []
    #     expected_names = []
    #     expected_tags = ["tag1", "tag2"]  # From mock
    #     expected_package_type = "python"  # From mock

    #     result = new_unique_names_and_tags(new_lines)
    #     assert result == (expected_names, expected_tags, expected_package_type)


def mock_unique_names_and_tags(old_lines):
    # This is a simple mock implementation. Adjust it as needed for your tests.
    unique_names = [
        line[1:] for line in old_lines
    ]  # Remove the '-' from the start
    unique_tags = ["tag_" + line[1:] for line in old_lines]  # Just a mock tag
    return unique_names, unique_tags


class TestOldUniqueNamesAndTags(unittest.TestCase):

    @patch("main.unique_names_and_tags", side_effect=mock_unique_names_and_tags)
    def test_valid_input(self, mock_unique_names_and_tags):
        old_lines = ["-name1", "-name2", "-name3"]

        unique_names, unique_tags = old_unique_names_and_tags(old_lines)

        self.assertEqual(unique_names, ["name1", "name2", "name3"])
        self.assertEqual(unique_tags, ["tag_name1", "tag_name2", "tag_name3"])

    def test_invalid_input(self):
        old_lines = ["-name1", "name2", "-name3"]  # The second item is invalid

        with self.assertRaises(ValueError) as context:
            old_unique_names_and_tags(old_lines)

        self.assertEqual(
            str(context.exception), "old_lines should start with a: '-'"
        )


class TestPackageNameAndTag:

    def test_valid_names_and_tags(self):
        result = package_name_and_tag_are_unique(
            unique_names=["package1"],
            unique_tags=["tag1"],
            greater_than_or_equal=True,
            package_type="python",
        )
        assert result == ("package1", "tag1")

    def test_invalid_names_raises_value_error(self):
        with pytest.raises(
            ValueError, match="nor the names, neither the tags are unique"
        ):
            package_name_and_tag_are_unique(
                unique_names=["package1", "package1"],  # Duplicate name
                unique_tags=["tag1"],
                greater_than_or_equal=True,
                package_type="python",
            )

    def test_invalid_tags_raises_value_error(self):
        with pytest.raises(
            ValueError, match="nor the names, neither the tags are unique"
        ):
            package_name_and_tag_are_unique(
                unique_names=["package1"],
                unique_tags=[],  # No tags
                greater_than_or_equal=True,
                package_type="python",
            )

    def test_golang_package_type_does_not_raise(self):
        # This should not raise even with invalid names and tags
        result = package_name_and_tag_are_unique(
            unique_names=["package1", "package1"],  # Duplicate name
            unique_tags=["tag1"],
            greater_than_or_equal=True,
            package_type="golang",
        )
        assert result == ("package1", "tag1")


if __name__ == "__main__":
    unittest.main()
