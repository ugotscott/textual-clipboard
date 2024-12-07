#!/bin/bash

_new_version="${1}"
if [ -z "${_new_version}" ]; then
    echo "ERROR: Script argument is missing. A release version string is a required argument."
    exit 1
fi

answered_yes() {
    yn_prompt="${1}"
    if [ -z "${yn_prompt}" ]; then
        yn_prompt="Continue?"
    fi
    while true; do
        read -p "${yn_prompt} (y/n) " yn
        case $yn in
        [Yy]*) return 0 ;;
        [Nn]*) return 1 ;;
        *) echo "Please answer y or n " ;;
        esac
    done
}

_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "${_branch}" != "main" ]; then
    echo "ERROR: Apparently you are on branch \"${_branch}\". To release you need to be on branch \"main\"."
    exit 1
fi

if ! git fetch; then
    echo "ERROR: git fetch command failed."
    exit 1
fi

if ! git diff --quiet; then
    echo "ERROR: The source area appears to be out-of-date."
    exit 1
fi

_untracked=$(git status --porcelain --untracked-files)
if [ -n "${_untracked}" ]; then
    echo "WARNING: There appear to be untracked files:"
    git status --porcelain --untracked-files
    if ! answered_yes "Continue with release?"; then
        echo "INFO: Release process aborted."
        exit 1
    fi
fi

_uncomitted=$(git status --porcelain)
if [ -n "${_uncomitted}" ]; then
    echo "WARNING: There appear to be uncomitted files:"
    git status --porcelain
    if ! answered_yes "Continue with release?"; then
        echo "INFO: Release process aborted."
        exit 1
    fi
fi
