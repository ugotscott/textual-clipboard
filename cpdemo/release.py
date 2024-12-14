from textual.widgets import Input, Button, DataTable, RichLog, Header, Footer
from textual.app import App, ComposeResult
from textual.containers import Horizontal
import subprocess
import re
from dataclasses import dataclass
from types import SimpleNamespace


@dataclass
class GitData:
    main = "main"
    branch = ""
    tags = SimpleNamespace(all=[str], main=[str], other=[str])


@dataclass
class State:
    git_data_cache = GitData()


OK = "  :green_circle:"
NOT_OK = "  :red_circle:"
CAUTION = "  :yellow_circle:"
UNKNOWN = "  :question_mark:"


def new_release_tag() -> str:
    # Get from argparse
    return UNKNOWN


def tag_exists(tag: str) -> bool:
    # git tag -l
    return False


def out_of_date() -> bool:
    # git fetch
    # follwed by:
    # git diff --quiet
    # If git diff returns non-zero exit code
    # then repo is out-of-date
    return True


def not_tracked() -> list:
    # git status --porcelain --untracked-files
    return [UNKNOWN]


def not_comitted() -> list:
    # git status --porcelain
    return [UNKNOWN]


PROJ_ROWS = [
    ("item", "value", "status"),
    ("pyproject.toml version", UNKNOWN, NOT_OK),
    ("pip install", UNKNOWN, NOT_OK),
]

REL_STR_ROWS = [
    ("item", "value", "status"),
    ("format", UNKNOWN, NOT_OK),
    ("conflict", UNKNOWN, NOT_OK),
    ("sequence", UNKNOWN, NOT_OK),
]

GIT_ROWS = [
    ("item", "value", "status"),
    ("latest release main", UNKNOWN, NOT_OK),
    ("latest release other", UNKNOWN, NOT_OK),
    ("current branch", UNKNOWN, NOT_OK),
    ("up-to-date", UNKNOWN, NOT_OK),
    ("not tracked items", UNKNOWN, NOT_OK),
    ("not comitted items", UNKNOWN, NOT_OK),
]


class MyApp(App):
    """Project Release App"""

    CSS_PATH = "release.tcss"

    def compose(self) -> ComposeResult:
        """Top level widgets"""
        yield Header()
        yield Footer()
        with Horizontal(id="input"):
            new_version = Input()
            new_version.placeholder = "X.X.X"
            new_version.id = "newversion"
            new_version.border_title = "Requested Release Version"
            new_version.restrict = r"^\d{1,}[\.]{0,1}\d*[\.]{0,1}\d*$"
            yield new_version
            rel_branch = Input()
            rel_branch.placeholder = "branch name"
            rel_branch.value = "main"
            rel_branch.id = "relbranch"
            rel_branch.border_title = "Project Release Branch"
            yield rel_branch
            yield Button("Additional Checks", id="additional")
            yield Button("Release", id="release")
            yield Button("Rerun Checks", id="rerun")
        with Horizontal(id="checks"):
            ver_str_table = DataTable()
            ver_str_table.id = "verstring"
            ver_str_table.border_title = "Version String Checks"
            yield ver_str_table

            proj_table = DataTable()
            proj_table.id = "project"
            proj_table.border_title = "Project Checks"
            yield proj_table

            git_table = DataTable()
            git_table.id = "git"
            git_table.border_title = "Git Checks"
            yield git_table

        with Horizontal(id="logs"):
            git_status = RichLog(highlight=True, markup=True)
            git_status.id = "gitstatus"
            git_status.border_title = "Git Status"
            yield git_status

            cmd_log = RichLog(highlight=True, markup=True)
            cmd_log.id = "cmdlog"
            cmd_log.border_title = "Command Log"
            yield cmd_log

        self.title = "Project New Version Release"

    def on_mount(self) -> None:
        table = self.query_one("#project", DataTable)
        for col in PROJ_ROWS[0]:
            table.add_column(label=col, key=col)
        for row in PROJ_ROWS[1:]:
            table.add_row(*row, key=row[0])

        table = self.query_one("#verstring", DataTable)
        for col in REL_STR_ROWS[0]:
            table.add_column(label=col, key=col)
        for row in REL_STR_ROWS[1:]:
            table.add_row(*row, key=row[0])

        table = self.query_one("#git", DataTable)
        for col in GIT_ROWS[0]:
            table.add_column(label=col, key=col)
        for row in GIT_ROWS[1:]:
            table.add_row(*row, key=row[0])

    def on_ready(self) -> None:
        git_status(self)
        get_git_data(self, State.git_data_cache)
        branch_check(self, State().git_data_cache)
        # git_checks(self, State().git_data_cache)
        if self.query_one("#newversion", Input).value:
            self.run_checks()

    def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id == "newversion":
            self.run_checks()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == "newversion":
            self.run_checks()
        elif message.input.id == "relbranch":
            State.git_data_cache.main = message.input.value
            branch_check(self, State().git_data_cache)
            rel_tag_check(self, State().git_data_cache)

    def run_checks(self) -> None:
        format_check(self)
        branch_check(self, State().git_data_cache)
        rel_tag_check(self, State().git_data_cache)


def error_str(app: MyApp, plain_str: str) -> str:
    return f"[{app.current_theme.error}]{plain_str}"


class CmdOut:
    def __init__(self, cmd: list) -> None:
        self.cp = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if self.cp.returncode != 0:
            self.error = True
            self.value = self.cp.stderr
        else:
            self.error = False
            self.value = self.cp.stdout


def show_cmd_output(app: MyApp, output: list | str, error=False):
    cmd_log = app.query_one("#cmdlog", RichLog)
    if isinstance(output, list):
        cmd_log.write(f"[bold {app.current_theme.secondary}]$ {' '.join(output)}")
    else:
        for line in output.splitlines():
            formatted_line = line
            if error:
                formatted_line = error_str(app, line)
            cmd_log.write(formatted_line, animate=True, scroll_end=True)


def show_git_status(app: MyApp, status_output: str, error=False):
    status_log = app.query_one("#gitstatus", RichLog)
    status_log.clear()
    for line in status_output.splitlines():
        formatted_line = line
        if error:
            formatted_line = error_str(app, line)
        status_log.write(formatted_line)


def git_status(app: MyApp) -> None:
    cmd = ["git", "status"]
    result = CmdOut(cmd)
    show_cmd_output(app, cmd)
    show_git_status(app, result.value, result.error)
    show_cmd_output(app, result.value, result.error)


def valid_ver_str(verstr: str) -> bool:
    if re.match(r"^\d+\.\d+\.\d+$", verstr):
        for num in verstr.split("."):
            if num.startswith("0") and num != "0":
                return False
            if not num.isnumeric():
                return False
    else:
        return False
    return True


def get_release_tags(app: MyApp, git_data: GitData) -> SimpleNamespace:
    cmd = [
        "git",
        "for-each-ref",
        "refs/tags",
        "--sort=-taggerdate",
        r"--format=%(refname:short) %(objecttype)",
    ]
    all_release_tags = []
    show_cmd_output(app, cmd)
    result = CmdOut(cmd)
    if result.error:
        show_cmd_output(app, result.value, result.error)
    else:
        show_cmd_output(app, result.value)
        for line in result.value.splitlines():
            tag, tag_type = line.split()
            if tag_type == "tag" and valid_ver_str(tag):
                all_release_tags.append(tag)
        if all_release_tags:
            all_release_tags.sort(key=version_key)
    main_release_tags = []
    other_release_tags = []
    for tag in all_release_tags:
        cmd = ["git", "branch", "--contains", f"tags/{tag}"]
        show_cmd_output(app, cmd)
        result = CmdOut(cmd)
        if not result.error:
            show_cmd_output(app, result.value)
            for branch in result.value.splitlines():
                if branch.strip() == git_data.main:
                    main_release_tags.append(tag)
                    break
            if tag not in main_release_tags:
                other_release_tags.append(tag)
        else:
            show_cmd_output(app, result.value, result.error)
    return SimpleNamespace(
        all=all_release_tags, main=main_release_tags, other=other_release_tags
    )


def get_current_branch(app: MyApp) -> str:
    branch = []
    cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    show_cmd_output(app, cmd)
    result = CmdOut(cmd)
    if result.error:
        show_cmd_output(app, result.value, result.error)
    else:
        show_cmd_output(app, result.value)
        for line in result.value.splitlines():
            branch.append(line)
    if branch:
        return branch[0]
    return ""


def get_git_data(app: MyApp, git_data: GitData) -> None:
    git_data.tags = get_release_tags(app, git_data)
    git_data.branch = get_current_branch(app)


def format_check(app: MyApp) -> None:
    new_ver_input = app.query_one("#newversion", Input)
    ver_str_table = app.query_one("#verstring", DataTable)
    if valid_ver_str(new_ver_input.value):
        new_val = OK
    else:
        new_val = NOT_OK
    ver_str_table.update_cell(
        value=new_ver_input.value,
        column_key="value",
        row_key="format",
        update_width=True,
    )
    ver_str_table.update_cell(
        value=new_val, column_key="status", row_key="format", update_width=True
    )


def branch_check(app: MyApp, git_data: GitData) -> None:
    branch = UNKNOWN
    status = NOT_OK
    if git_data.branch:
        branch = git_data.branch
        if git_data.branch == git_data.main:
            status = OK
        else:
            status = CAUTION
    git_table = app.query_one("#git", DataTable)
    git_table.update_cell(column_key="value", row_key="current branch", value=branch)
    git_table.update_cell(column_key="status", row_key="current branch", value=status)


def version_key(version):
    return [int(x) for x in version.split(".")]


def ver_is_gt(ver1: str, ver2: str) -> bool:
    """
    Check if version1 is greater than version2.
    """
    if not valid_ver_str(ver1) or not valid_ver_str(ver2):
        return False
    v1 = [int(x) for x in ver1.split(".")]
    v2 = [int(x) for x in ver2.split(".")]
    for i in range(max(len(v1), len(v2))):
        x = v1[i] if i < len(v1) else 0
        y = v2[i] if i < len(v2) else 0
        if x > y:
            return True
        elif x < y:
            return False
    return False  # Versions are equal


def ver_val(ver_str: str, idx: int) -> str:
    return ver_str.split(".")[idx]


def minor_is_gt(ver: str, all_tags_sorted: list[str]) -> bool:
    is_gt = True
    minor = ver.split(".")[1]
    for tag in all_tags_sorted:
        if minor == tag.split(".")[1]:
            if not ver_is_gt(ver, tag):
                is_gt = False
                break
    return is_gt


def rel_tag_check(app: MyApp, git_data: GitData) -> None:
    ver_str_table = app.query_one("#verstring", DataTable)
    tags = git_data.tags
    new_tag = app.query_one("#newversion", Input).value
    if not valid_ver_str(new_tag):
        new_tag = ""

    print(f"new_tag = {new_tag} tags.all = {tags.all} git_data = {git_data}")
    if not new_tag or not tags.all:
        ver_str_table.update_cell(column_key="value", row_key="sequence", value=UNKNOWN)
        ver_str_table.update_cell(column_key="status", row_key="sequence", value=NOT_OK)
        ver_str_table.update_cell(column_key="value", row_key="conflict", value=UNKNOWN)
        ver_str_table.update_cell(column_key="status", row_key="conflict", value=NOT_OK)
    elif minor_is_gt(new_tag, tags.all):
        if git_data.branch == git_data.main and ver_val(new_tag, 1) < ver_val(
            tags.main[0], 1
        ):
            ver_str_table.update_cell(column_key="value", row_key="sequence", value="!")
            ver_str_table.update_cell(
                column_key="status", row_key="sequence", value=CAUTION
            )
        else:
            ver_str_table.update_cell(
                column_key="value", row_key="sequence", value="ok"
            )
            ver_str_table.update_cell(column_key="status", row_key="sequence", value=OK)
    else:
        ver_str_table.update_cell(column_key="value", row_key="sequence", value="bad")
        ver_str_table.update_cell(column_key="status", row_key="sequence", value=NOT_OK)

    conflict = False
    for tag in tags.all:
        if new_tag == tag:
            conflict = True
            break
    if conflict:
        ver_str_table.update_cell(column_key="value", row_key="conflict", value="yes")
        ver_str_table.update_cell(column_key="status", row_key="conflict", value=NOT_OK)
    else:
        if new_tag:
            ver_str_table.update_cell(
                column_key="value", row_key="conflict", value="no"
            )
            ver_str_table.update_cell(column_key="status", row_key="conflict", value=OK)
        else:
            ver_str_table.update_cell(
                column_key="value", row_key="conflict", value=UNKNOWN
            )
            ver_str_table.update_cell(
                column_key="status", row_key="conflict", value=NOT_OK
            )

    if tags.main:
        pass

    if tags.other:
        pass


def main():
    app = MyApp()
    app.run()


if __name__ == "__main__":
    main()
