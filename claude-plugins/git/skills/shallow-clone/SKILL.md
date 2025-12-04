---
name: shallow-clone
description: Perform a shallow clone of a Git repository to a temporary location.
allowed-tools: [ Bash ]
---

# Shallow Clone

Provides a script for creating a shallow clone of a Git repository to a temporary location. This skill should be used
to analyze repository contents locally instead of using web APIs.

## Usage

Use the `scripts/shallow-clone.sh` script in this directory, for example:

```bash
./scripts/shallow-clone.sh <repository_url> [<tag_or_branch>]
```

The script will print the path to the cloned repository when done, for example:

```shell
$ ./scripts/shallow-clone.sh https://github.com/psf/requests.git
Cloning https://github.com/psf/requests.git (shallow, ref: HEAD) to /tmp/shallow-clone-DDqkuv...
/tmp/shallow-clone-DDqkuv/repo
```

After analyzing the local repository, clean up the temporary directory with:

```shell
$ rm -rf <path_to_temporary_directory>
```
