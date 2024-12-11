from textual.widgets import Input, Button, DataTable, RichLog, Header, Footer
from textual.app import App, ComposeResult
from textual.containers import Horizontal
import subprocess
import re

OK = "  :green_circle:"
NOT_OK = "  :red_circle:"
CAUTION = "  :yellow_circle:"
UNKNOWN = "  :question_mark:"


def new_release_tag() -> str:
    # Get from argparse
    return UNKNOWN


def latest_release_tag() -> str:
    # This seems best:
    # git for-each-ref refs/tags --sort=-taggerdate --format='%(objecttype) %(refname:short)'
    # Then in Python grab the first one prefixed by "tag" and whose tag matches the
    # version string format:
    # tag 0.0.0
    # Non annotated tags will be prefixed with "commit":
    # commit sometag
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
    ("current project version", UNKNOWN, NOT_OK),
    ("pip install", UNKNOWN, NOT_OK),
]

REL_STR_ROWS = [
    ("item", "value", "status"),
    ("format", UNKNOWN, NOT_OK),
    ("conflict", UNKNOWN, NOT_OK),
]

GIT_ROWS = [
    ("item", "value", "status"),
    ("latest release tag", UNKNOWN, NOT_OK),
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
        branch_check(self)
        if self.query_one("#newversion", Input).value:
            self.run_checks()

    def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id == "newversion":
            format_check(self)

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == "newversion":
            self.run_checks()

    def run_checks(self) -> None:
        format_check(self)
        branch_check(self)


def git_status(app: MyApp) -> None:
    cmd = ["git", "status"]
    cmd_log = app.query_one("#cmdlog", RichLog)
    cmd_log.write(f"[bold {app.current_theme.secondary}]$ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    status_log = app.query_one("#gitstatus", RichLog)
    status_log.clear()
    if result.returncode:
        for line in result.stderr.splitlines():
            cmd_log.write(f"[{app.current_theme.error}]{line}")
            status_log.write(f"[{app.current_theme.error}]{line}")
    else:
        for line in result.stdout.splitlines():
            cmd_log.write(line)
            status_log.write(line)


def format_check(app: MyApp) -> None:
    new_ver_input = app.query_one("#newversion", Input)
    ver_str_table = app.query_one("#verstring", DataTable)
    if re.match(r"^\d+\.\d+\.\d+$", new_ver_input.value):
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


def branch_check(app: MyApp) -> None:
    # git rev-parse --abbrev-ref HEAD
    # This will return branch name, we want "main"
    cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    cmd_log = app.query_one("#cmdlog", RichLog)
    cmd_log.write(f"[bold {app.current_theme.secondary}]$ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    branch = [UNKNOWN]
    status = NOT_OK
    if result.returncode:
        for line in result.stderr.splitlines():
            cmd_log.write(
                content=f"[{app.current_theme.error}]{line}",
                scroll_end=True,
                animate=True,
            )
    else:
        branch = []
        for line in result.stdout.splitlines():
            branch.append(line)
            cmd_log.write(line)
    if branch[0] == "main":
        status = OK
    git_table = app.query_one("#git", DataTable)
    git_table.update_cell(column_key="value", row_key="current branch", value=branch[0])
    git_table.update_cell(column_key="status", row_key="current branch", value=status)


def main():
    app = MyApp()
    app.run()


if __name__ == "__main__":
    main()
