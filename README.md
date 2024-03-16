# pull-requests-merger-action

Pull Requests Merger Action.

Create a `.github/workflows/pull-requests-merger.yml` file:

```bash
---
name: pull-requests-merger
'on':
  schedule:
    - cron: '42 10 * * 5'
jobs:
  pull-requests-merger:
    permissions:
      contents: write
      pull-requests: write
    runs-on: ubuntu-22.04
    steps:
      - uses: 030/pull-requests-merger-action@v0.1.0
```
