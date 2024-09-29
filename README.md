# Pull Requests Merger Action

A GitHub Action to automate the merging of pull requests based on specific
conditions. This action is designed to streamline the development workflow by
automatically merging pull requests once they meet defined criteria, such as
passing status checks or specific approvals.

## Features

- Automatically merge pull requests created by Dependabot, as long as they are
  listed in the allow.json file.

## Usage

Create a `.github/workflows/pull-requests-merger.yml` file:

```yaml
---
name: pull-requests-merger
"on":
  schedule:
    - cron: "42 10 * * 5"
permissions:
  actions: write
  contents: write
  pull-requests: write
jobs:
  pull-requests-merger:
    runs-on: ubuntu-22.04
    steps:
      - uses: 030/pull-requests-merger-action@v0.1.0
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

## Testing

### Multiple

```bash
find test/testdata/diff -type f | while read -r f; do
  python3 main.py \
    --gh-pr-diff "$(cat "${f}")" \
    --path-to-allow-json-file allow.json
done
```

### Single

```bash
python3 main.py \
    --gh-pr-diff "$(cat test/testdata/diff/upload-release-action.txt)" \
    --path-to-allow-json-file allow.json \
    --log-level DEBUG
```

```bash
python3 main.py \
    --gh-pr-diff "$(cat test/testdata/diff/golang-modules-2.txt)" \
    --path-to-allow-json-file allow.json \
    --log-level DEBUG
```
