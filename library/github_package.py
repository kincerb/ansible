#!/usr/bin/python
# ruff: noqa: D100,E402

# Copyright: (c) 2024, Brent Kincer <dev.bkincer@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: github_package

short_description: Install software from GitHub repos

version_added: 1.0.0

description:
    - Install software from releases published in GitHub repos

options:
    token:
        description:
            - GitHub Personal Access Token for authenticating.
        type: str
    user:
        description:
            - The GitHub account that owns the repository
        type: str
        required: true
    repo:
        description:
            - Repository name
        type: str
        required: true
    release:
        description:
            - Tagged release to install
        type: str
        required: false
    asset_suffix:
        description:
            - Filename suffix matching asset to download
        type: str
        required: true
    tmp_dir:
        description:
            - Temporary storage for downloads
        type: path
        required: false
        default: /tmp
    dest:
        description:
            - Destination for extracted asset
        type: path
        required: false
        default: /usr/local/bin

attributes:
    check_mode:
        support: full
    diff_mode:
        support: none

author:
    - "Brent Kincer (@kincerb)"
requirements:
    - "github3.py"
"""

EXAMPLES = r"""
- name: Install the latest release of delta
  github_package:
    user: dandavison
    repo: delta
    release: latest
    asset_suffix: x86_64-unknown-linux-gnu.tar.gz
    dest: /usr/local/bin

- name: Install the 10.2.0 release of fd
  github_package:
    user: sharkdp
    repo: fd
    release: 10.2.0
    asset_suffix: x86_64-unknown-linux-gnu.tar.gz
"""

RETURN = r"""
tag:
    description: Version of the created/latest release.
    type: str
    returned: success
    sample: 1.1.0
"""

import traceback
from pathlib import Path

try:
    import github3
except ImportError:
    HAS_GITHUB = False
    GITHUB_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_GITHUB = True
    GITHUB_IMPORT_ERROR = None

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.text.converters import to_native


class GitHubPackage(object):
    """Class to download artifacts from GitHub projects."""

    repo: str
    user: str
    release: str
    asset_suffix: str
    tmp_dir: str
    logged_in: bool

    def __init__(self, module: AnsibleModule):
        """Initialize object with arguments given."""
        self.module = module
        self.user = module.params["user"]
        self.repo = module.params["repo"]
        self.asset_suffix = module.params["asset_suffix"]
        self.tmp_dir = module.params["tmp_dir"]
        self.release = module.params["release"]
        self.dest = module.params["dest"]
        self.token = module.params["token"]

        self._gh = github3.GitHub()
        self.logged_in = False
        self.result = {}

    def __repr__(self):  # noqa: D105
        return f"{type(self).__name__}({self.repo!r})"

    def login(self) -> None:
        try:
            self._gh.login(token=self.token)
        except github3.exceptions.AuthenticationFailed as e:
            self.module.fail_json(msg="Failed GitHub login with token", exception=e)
        else:
            self.logged_in = True


def run_module():
    """Entry point for github_package module."""
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(required=True),
            user=dict(required=True),
            token=dict(no_log=True),
            release=dict(type="str", default="latest"),
            asset_suffix=dict(type="str", required=True),
            tmp_dir=dict(type="path", default="/tmp"),
            dest=dict(type="path", default="/usr/local/bin"),
        ),
        supports_check_mode=True,
    )

    if not HAS_GITHUB:
        module.fail_json(
            msg=missing_required_lib("github3.py"), exception=GITHUB_IMPORT_ERROR
        )

    gh_package = GitHubPackage(module)


def main():
    """Entry point for github_package module."""
    run_module()


if __name__ == "__main__":
    main()
