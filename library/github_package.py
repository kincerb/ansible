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
            - Mutually exclusive with O(password).
        type: str
    user:
        description:
            - The GitHub account that owns the repository
        type: str
        required: true
    password:
        description:
            - The GitHub account password for the user.
            - Mutually exclusive with O(token).
        type: str
    repo:
        description:
            - Repository name
        type: str
        required: true
    release:
        description:
            - Tagged release to install
        type: str
        required: true
        choices: [ 'latest', 'create_release' ]

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

EXAMPLES = """
- name: Get latest release of a public repository
  github_package:
    user: ansible
    repo: ansible
    action: latest_release

- name: Get latest release of testuseer/testrepo
  github_package:
    token: tokenabc1234567890
    user: testuser
    repo: testrepo
    action: latest_release

- name: Get latest release of test repo using username and password
  github_package:
    user: testuser
    password: secret123
    repo: testrepo
    action: latest_release

"""

RETURN = """
tag:
    description: Version of the created/latest release.
    type: str
    returned: success
    sample: 1.1.0
"""

import traceback

GITHUB_IMP_ERR = None
try:
    import github3

    HAS_GITHUB_API = True
except ImportError:
    GITHUB_IMP_ERR = traceback.format_exc()
    HAS_GITHUB_API = False

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

    def __init__(self, *, user, repo, asset_suffix, **kwargs):
        """Initialize object with arguments given."""
        self._gh = github3.GitHub()
        self.user = user
        self.repo = repo
        self.asset_suffix = asset_suffix
        self.logged_in = False

        self._post_init(**kwargs)

    def __repr__(self):  # noqa: D105
        return f"{type(self).__name__}({self.repo!r})"

    def _post_init(self, **kwargs) -> None:
        if kwargs.get("token") is not None:
            try:
                self._gh.login(token=kwargs.pop("token"))
            except github3.exceptions.AuthenticationFailed as e:
                if kwargs.get("login_required", False):
                    module.fail_json(
                        msg="Failed to connect to GitHub: %s" % to_native(e),
                        details="Please check username and password or token "
                        "for repository %s" % repo,
                    )
                else:
                    pass
            self.logged_in = True


def main():
    """Entry point for github_package module."""
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(required=True),
            user=dict(required=True),
            password=dict(no_log=True),
            token=dict(no_log=True),
            release=dict(type="str", default="latest"),
            asset_suffix=dict(type="str", required=True),
            tmp_dir=dict(type="str", default="/tmp"),
        ),
        supports_check_mode=True,
        mutually_exclusive=(("password", "token"),),
    )

    if not HAS_GITHUB_API:
        module.fail_json(
            msg=missing_required_lib("github3.py"), exception=GITHUB_IMP_ERR
        )

    repo = module.params["repo"]
    user = module.params["user"]
    release = module.params["release"]

    repository = gh_obj.repository(user, repo)

    if not repository:
        module.fail_json(msg="Repository %s/%s doesn't exist" % (user, repo))

    if release == "latest":
        release = repository.latest_release()
        if release:
            module.exit_json(tag=release.tag_name)
        else:
            module.exit_json(tag=None)


if __name__ == "__main__":
    main()
