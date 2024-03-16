import click
import json
import logging
import re
import requests
import sys


def get_gh_action_name_and_tag(input_str) -> (str, str):
    name = ""
    pattern = r"uses: (\S+)@(\S+)"
    tag = ""

    try:
        match = re.search(pattern, input_str)

        name = match.group(1)
        tag = match.group(2)
    except Exception as e:
        raise ValueError("name and/or not found")

    return name, tag


# diffs returns a str that contains the lines that will be removed and replaced
def diffs(gh_pr_diff: str) -> []:
    logging.info("checking diffs")
    old_and_new_lines = []

    try:
        lines = gh_pr_diff.split('\n')

        for i in range(1, len(lines)):
            if lines[i].startswith('+') and lines[i].count('+') == 1:
                old_line = lines[i-1]
                new_line = lines[i]

                old_and_new_lines.append(old_line)
                old_and_new_lines.append(new_line)

        if old_and_new_lines == []:
            raise ValueError("old_and_new_lines should not be empty")

    except Exception as e:
        logging.error(f"error: {e}")
        raise

    return old_and_new_lines


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def unique_elements(elements: []) -> []:
    return list(set(elements))


def valid(unique_elements: [], valid_length: int) -> bool:
    logging.info("checking whether it is valid...")
    valid = False
    length = len(unique_elements)
    logging.info(f"length: %i", length)
    if length == valid_length:
        valid = True

    return valid


def valid_commit_sha(actual: str, name: str, path: str, tag: str) -> bool:
    logging.info(f"checking whether found checksum: '%s' for package: '%s' with tag: '%s' by looking it up in file: '%s' is valid", actual, name, tag, path)
    valid = False

    try:
        with open(path, 'r') as file:
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
    return valid(unique_names, 1)


# a maximum of two unique tags is allowed in a pr that has to be updated
def valid_tags(unique_tags) -> bool:
    return valid(unique_tags, 2)


def unique_names_and_tags(removed_and_replaced_lines: []) -> ([], []):
    logging.info("checking unique_names_and_tags")
    names = []
    tags = []

    for removed_and_replaced_line in removed_and_replaced_lines:
        name, tag = get_gh_action_name_and_tag(removed_and_replaced_line)
        names.append(name)
        tags.append(tag)

    unique_names = unique_elements(names)
    unique_tags = unique_elements(tags)

    return unique_names, unique_tags


def new_package_name_and_tag(unique_names: [], unique_tags: []) -> (str, str):
    logging.info(f"determining name and tag for unique_names: '%s' and unique_tags: '%s'", unique_names, unique_tags)
    try:
        if not (valid_names(unique_names) and valid_tags(unique_tags)):
            raise ValueError("nor the names, neither the tags are unique")
    except Exception as e:
        logging.error(f"error: {e}")
        raise

    name = unique_names[0]

    # ensure that the tags are sorted from old to new so that latest tag can
    # be determined
    sorted_unique_tags = sorted(unique_tags, key=lambda x: tuple(map(int, x.lstrip('v').split('.'))))
    tag = sorted_unique_tags[1]

    return name, tag


def get_actual_commit_sha(name: str, tag_to_be_found: str) -> str:
    commit_sha = ""

    response = requests.get("https://api.github.com/repos/"+name+"/tags")

    if response.status_code == 200:
        tags = response.json()

        for tag in tags:
            if tag["name"] == tag_to_be_found:
                commit_sha = tag["commit"]["sha"]
                break
    else:
        print("Error:", response.status_code)

    return commit_sha


@click.command()
@click.option('--gh-pr-diff', required=True)
@click.option('--path-to-allow-json-file', required=True)
def cli(gh_pr_diff, path_to_allow_json_file):
    removed_and_replaced_lines = diffs(gh_pr_diff)

    unique_names, unique_tags = unique_names_and_tags(removed_and_replaced_lines)

    name, tag = new_package_name_and_tag(unique_names, unique_tags)

    actual_commit_sha = get_actual_commit_sha(name, tag)

    if valid_commit_sha(actual_commit_sha, name, path_to_allow_json_file, tag):
        logging.info(f"commit sha of updated package: '%s' with tag: '%s' is valid", name, tag)
    else:
        logging.error(f"checksum of package: '%s' with tag: '%s' deviates", name, tag)
        sys.exit(1)


def main():
    configure_logging()
    cli()


if __name__ == '__main__':
    main()
