import click
import json
import logging
import re
import requests
import sys


def get_name_and_version(input_str) -> tuple[str, str, str]:
    pattern_uses = r"uses: (\S+)@(\S+)"
    pattern_from = r"FROM (\S+):(\S+)"
    pattern_golang = r"(go)\s(\S+)"
    pattern_golang_modules = r"((github\.com|golang\.org|gopkg\.in|k8s\.io|go\.uber\.org|sigs\.k8s\.io)/\S+)\s+(v\S+)"

    logging.debug(
        f"input_str: '%s'",
        input_str,
    )

    try:
        match = re.search(pattern_uses, input_str)
        if match:
            name = match.group(1)
            tag = match.group(2)
            return name, tag, "github-actions"
        match = re.search(pattern_from, input_str)
        if match:
            name = match.group(1)
            tag = match.group(2)
            return name, tag, "docker"
        match = re.search(pattern_golang, input_str)
        if match:
            name = match.group(1)
            tag = match.group(2)
            return name, tag, "golang"
        match = re.search(pattern_golang_modules, input_str)
        if match:
            name = match.group(1)
            tag = match.group(3)
            return name, tag, "golang"

        raise ValueError("name and/or tag not found")

    except Exception as e:
        raise ValueError("name and/or tag not found")


# diffs returns a str that contains the lines that will be removed and replaced
def diffs(gh_pr_diff: str) -> tuple[list[str], list[str]]:
    logging.info("checking diffs")
    old_lines = []
    new_lines = []

    try:
        lines = gh_pr_diff.split("\n")
        logging.debug(
            f"lines: '%s'",
            lines,
        )

        for i in range(1, len(lines)):
            if lines[i].startswith("+") and lines[i].count("+") == 1:
                old_line = lines[i - 1]
                new_line = lines[i]

                old_lines.append(old_line)
                new_lines.append(new_line)

        if old_lines == [] or new_lines == []:
            raise ValueError("neither old_lines nor new_lines should be empty")

    except Exception as e:
        logging.error(f"error: {e}")
        raise

    return old_lines, new_lines


def configure_logging(log_level=logging.INFO):
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def unique_elements(elements: list[str]) -> list[str]:
    return list(set(elements))


def valid(
    unique_elements: list[str], valid_length: int, greater_than_or_equal: bool
) -> bool:
    logging.info("checking whether it is valid...")
    valid = False
    length = len(unique_elements)
    logging.info(f"length: %i", length)

    if greater_than_or_equal:
        if length >= valid_length:
            valid = True
    else:
        if length == valid_length:
            valid = True

    return valid


def valid_commit_sha(actual: str, name: str, path: str, tag: str) -> bool:
    logging.info(
        f"checking whether found checksum: '%s' for package: '%s' with tag: '%s' by looking it up in file: '%s' is valid",
        actual,
        name,
        tag,
        path,
    )
    valid = False

    try:
        with open(path, "r") as file:
            json_data = json.load(file)
        expected = json_data["packages"][name][tag]
        logging.info(f"expected: '%s'", expected)
        if expected == "":
            raise ValueError("no expected checksum found in file: " + path)
    except Exception as e:
        logging.error(f"key or value not found in file. Error: {e}")
        raise

    logging.info(f"actual: '%s', expected: '%s'", actual, expected)
    if actual == expected:
        valid = True

    return valid


# a name is valid if the change is restricted to one package name
def valid_names(unique_names) -> bool:
    return valid(unique_names, 1, False)


# a maximum of two unique tags is allowed in a pr that has to be updated
def valid_tags(unique_tags: list[str], greater_than_or_equal: bool) -> bool:
    return valid(unique_tags, 1, greater_than_or_equal)


def unique_names_and_tags(
    removed_and_replaced_lines: list[str],
) -> tuple[list[str], list[str], str]:
    logging.info("checking unique_names_and_tags")
    names = []
    tags = []

    package_type = ""
    for removed_and_replaced_line in removed_and_replaced_lines:
        name, tag, package_type = get_name_and_version(
            removed_and_replaced_line
        )
        names.append(name)
        tags.append(tag)

    unique_names = unique_elements(names)
    unique_tags = unique_elements(tags)

    return unique_names, unique_tags, package_type


def package_name_and_tag_are_unique(
    unique_names: list[str],
    unique_tags: list[str],
    greater_than_or_equal: bool,
    package_type: str,
) -> tuple[str, str]:
    logging.info(
        f"determining name and tag for unique_names: '%s' and unique_tags: '%s'",
        unique_names,
        unique_tags,
    )
    try:
        if not (
            valid_names(unique_names)
            and valid_tags(unique_tags, greater_than_or_equal)
        ):
            if package_type != "golang":
                raise ValueError("nor the names, neither the tags are unique")
    except Exception as e:
        logging.error(f"error: {e}")
        raise

    name = unique_names[0]
    tag = unique_tags[0]

    return name, tag


def get_actual_commit_sha(name: str, tag_to_be_found: str) -> str:
    commit_sha = ""

    response = requests.get("https://api.github.com/repos/" + name + "/tags")

    if response.status_code == 200:
        tags = response.json()

        for tag in tags:
            if tag["name"] == tag_to_be_found:
                commit_sha = tag["commit"]["sha"]
                break
    else:
        print("Error:", response.status_code)

    logging.info(f"commit_sha: %s", commit_sha)

    return commit_sha


def old_unique_names_and_tags(
    old_lines: list[str],
) -> tuple[list[str], list[str]]:
    logging.info("checking old_unique_names_and_tags")
    try:
        for old_line in old_lines:
            if not old_line.startswith("-"):
                raise ValueError("old_lines should start with a: '-'")
    except Exception as e:
        logging.error(f"error: {e}")
        raise

    unique_names, unique_tags = unique_names_and_tags(old_lines)

    return unique_names, unique_tags


def new_unique_names_and_tags(
    new_lines: list[str],
) -> tuple[list[str], list[str], str]:
    logging.info("checking new_unique_names_and_tags")
    try:
        for new_line in new_lines:
            if not new_line.startswith("+"):
                raise ValueError("new_lines should start with a: '+'")
    except Exception as e:
        logging.error(f"error: {e}")
        raise

    unique_names, unique_tags, package_type = unique_names_and_tags(new_lines)
    logging.debug(
        f"unique_names: '%s', unique_tags: '%s', package_type: '%s'",
        unique_names,
        unique_tags,
        package_type,
    )

    return unique_names, unique_tags, package_type


def key_exists_in_category(
    file_path: str, category: str, search_key: str
) -> bool:
    try:
        with open(file_path, "r") as file:
            data = json.load(file)  # Read and parse JSON content
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' does not contain valid JSON.")
        return False

    # Check if the category exists and if the search_key exists within that category
    if category in data:
        return search_key in data[category]
    return False


@click.command()
@click.option("--gh-pr-diff", required=True)
@click.option("--log-level", default="INFO")
@click.option("--path-to-allow-json-file", required=True)
def cli(gh_pr_diff, log_level, path_to_allow_json_file):
    configure_logging(log_level)

    _, new_lines = diffs(gh_pr_diff)
    new_unique_names, new_unique_tags, package_type = new_unique_names_and_tags(
        new_lines
    )
    new_name, _ = package_name_and_tag_are_unique(
        new_unique_names, new_unique_tags, False, package_type
    )

    if not key_exists_in_category(
        path_to_allow_json_file, package_type, new_name
    ):
        logging.error(
            f"'%s' is NOT part of the package_type: '%s' in the JSON file: '%s'.",
            new_name,
            package_type,
            path_to_allow_json_file,
        )
        sys.exit(1)

    logging.info(
        f"'%s' is in the JSON array.",
        new_name,
    )


def main():
    cli()


if __name__ == "__main__":
    main()
