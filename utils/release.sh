#!/bin/bash

_new_version="${1}"
if [ -z "${_new_version}" ]; then
    echo "ERROR: Script argument is missing. A release version string is a required argument."
    exit 1
fi

_verok=$(echo "${_new_version}" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$')
if [ -z "${_verok}" ]; then
    echo "ERROR: \"${_new_version}\" is not a valid version format."
    exit 1
fi

_gtag=$(git tag -l "${_new_version}")
if [ -n "${_gtag}" ]; then
    echo "ERROR: ${_new_version} already exists as a git tag."
    exit 1
fi

_projver=$(grep -E 'version[ ]+=[ ]+' pyproject.toml | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')
if [ -z "${_projver}" ]; then
    echo "ERROR: Unable to read project version from \"pyproject.toml\"."
    exit 1
fi

echo "INFO: Project version found in \"pyproject.toml\" is \"${_projver}\""

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
    echo "ERROR: The source area appears to be out-of-date:"
    git status --porcelain
    exit 1
fi

answered_yes() {
    yn_prompt="${1}"
    if [ -z "${yn_prompt}" ]; then
        yn_prompt="Continue?"
    fi
    while true; do
        read -r -p "${yn_prompt} (y/n) " yn
        case $yn in
        [Yy]*) return 0 ;;
        [Nn]*) return 1 ;;
        *) echo "Please answer y or n " ;;
        esac
    done
}

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
