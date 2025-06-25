import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GObject, Adw, Gtk, Nautilus

# shows an alert dialog with a heading and body text to the user
def message_alert(heading: str, body: str, dismiss_label: str = 'Dismiss', parent: Adw.Dialog = None):
    dialog = Adw.AlertDialog(
            heading=heading,
            body=body,
        )
    dialog.add_response(
            id=dismiss_label,
            label=dismiss_label,
        )
    dialog.present(parent)

# creates a new directory and clones the git repository into it
def git_clone(git_url: str, dir_name: str, working_dir: str, parentDialog: Adw.Dialog):
    import re, os, subprocess

    if not git_url or not dir_name:
        message_alert(
            heading="Git Clone Error",
            body="Please provide both a repository URL and a target directory name.",
            parent=parentDialog,
        )
        return

    # regex to check if the directory name is valid, it can only contain letters, numbers, underscores, hyphens, dots, and spaces
    if not re.match(r'^[\w\-. ]+$', dir_name):
        message_alert(
            heading="Git Clone Error",
            body="Invalid directory name. Only letters, numbers, underscores, hyphens, dots, and spaces are allowed.",
            parent=parentDialog,
        )
        return

    # regex to check if the URL is valid (doesnt cover all cases, but a good start)
    if not re.match(r'^(https?|git)://[^\s/$.?#].[^\s]*$', git_url):
        message_alert(
            heading="Git Clone Error",
            body="Invalid repository URL. Please provide a valid URL starting with http://, https://, or git://.",
            parent=parentDialog,
        )
        return

    # if the direcory exists, create a new directory name by appending a number to the directory name
    target_path = os.path.join(working_dir, dir_name)
    counter = 1
    while os.path.exists(target_path):
        target_path = os.path.join(working_dir, f"{dir_name}_{counter}")
        counter += 1

    # set working directory to self.working_dir then run git clone command with the provided URL and directory name
    try:
        subprocess.run(['git', 'clone', git_url, target_path], check=True, cwd=working_dir)
        parentDialog.close()
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Clone Error",
            body=f"Failed to clone repository: {e}",
            parent=parentDialog,
        )

# shows the status to the user in a dialog
def git_status(working_dir: str):
    import subprocess
    try:
        result = subprocess.run(['git', 'status'], check=True, capture_output=True, text=True, cwd=working_dir)
        if result.stdout.strip() == "":
            message_alert(
                heading="Git Status",
                body="No changes to show.",
            )
        else:
            message_alert(
                heading="Git Status",
                body=result.stdout,
            )
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Status Error",
            body=f"Failed to get git status: {e}",
        )

# returns two lists of branches, one for local branches and one for remote branches
def git_list_branches(working_dir: str, parentDialog: Adw.Dialog):
    import subprocess
    try:
        result = subprocess.run(['git', 'branch', '-a'], check=True, capture_output=True, text=True, cwd=working_dir)
        branches = result.stdout.strip().split('\n')
        branches = [branch.strip() for branch in branches if branch.strip()]
        return branches
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Branches Error",
            body=f"Failed to list branches: {e}",
            parent=parentDialog,
        )
    parentDialog.close()
    return []

# switches to the specified branch in the git repository
def git_switch_branch(branch_name: str, working_dir: str, parentDialog: Adw.Dialog):
    import subprocess
    try:
        # current branch
        if branch_name.startswith('*'):
            return
        # origin/head
        if '->' in branch_name:
            branch_name = branch_name.split('->')[0].strip()
        # remote branch
        if branch_name.startswith('remotes/') or branch_name.startswith('origin/'):
            subprocess.run(['git', 'checkout', '-t', branch_name], check=True, cwd=working_dir)
        # local branch
        else:
            subprocess.run(['git', 'checkout', branch_name], check=True, cwd=working_dir)

        parentDialog.close()
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Switch Branch Error",
            body=f"Failed to switch branch: {e}",
            parent=parentDialog,
        )

# pulls the latest changes from the remote repository
def git_pull(working_dir: str):
    import subprocess
    try:
        subprocess.run(['git', 'pull'], check=True, cwd=working_dir)
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Pull Error",
            body=f"Failed to pull changes: {e}",
        )

# stages all changes and commits them
def git_stage_commit(working_dir: str, commit_message: str, parentDialog: Adw.Dialog):
    import subprocess
    try:
        subprocess.run(['git', 'add', '-A'], check=True, cwd=working_dir)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, cwd=working_dir)
        parentDialog.close()
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Stage/Commit Error",
            body=f"Failed to stage or commit changes: {e}",
            parent=parentDialog,
        )

# pushes the changes to the remote repository
def git_push(working_dir: str):
    import subprocess
    try:
        subprocess.run(['git', 'push'], check=True, capture_output=True, cwd=working_dir)
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Push Error",
            body=f"Failed to push changes: {e}\n{e.stderr.strip()}",
        )

# saves the git credentials for the user and the current host
def git_save_credentials(email: str, username: str, password: str, working_dir: str, parentDialog: Adw.Dialog):
    import subprocess, urllib.parse
    if not email or not username or not password:
        message_alert(
            heading="Git Credentials Error",
            body="Please provide email, username, and password.",
            parent=parentDialog,
        )
        return
    try:
        subprocess.run(["git", "config", "--global", "user.email", email], check=True)
        subprocess.run(["git", "config", "--global", "user.name", username], check=True)
        subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)

        # Get the 'origin' URL and extract its protocol + host
        origin = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
        ).stdout.strip()
        parsed = urllib.parse.urlparse(origin)

        # Prepare the credential input for git credential approve
        cred_input = (
            f"protocol={parsed.scheme}\n"
            f"host={parsed.hostname}\n"
            f"username={username}\n"
            f"password={password}\n\n"
        )
        proc = subprocess.Popen(["git", "credential", "approve"], stdin=subprocess.PIPE)
        proc.communicate(cred_input.encode())

        parentDialog.close()
    except subprocess.CalledProcessError as e:
        message_alert(
            heading="Git Credentials Error",
            body=f"Failed to save credentials: {e}",
            parent=parentDialog,
        )


class GitCloneDialog(Adw.Dialog):
    def __init__(self, folder: Nautilus.FileInfo):
        super().__init__()

        self.working_dir = folder.get_location().get_path()

        # Set up the dialog properties
        self.set_title('Clone Git Repository')
        self.set_content_width(450)
        root = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        header_bar.set_decoration_layout(':close')
        root.add_top_bar (header_bar)
        body = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            spacing=8,
            margin_top=16,
            margin_bottom=16,
            margin_start=16,
            margin_end=16,
        )
        root.set_content(body)
        list_box = Gtk.ListBox(css_classes=['boxed-list-separate'])
        body.append(list_box)

        # Create the entry for the repository URL and target directory name
        self.url_entry = Adw.EntryRow(title='Repository URL')
        list_box.append(self.url_entry)
        self.dir_entry = Adw.EntryRow(title='Target Directory Name')
        list_box.append(self.dir_entry)

        # Create the submit button to call the git_clone method
        self.submit_button = Gtk.Button(
            label='Clone',
            css_classes=['pill', 'suggested-action'],
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        body.append(self.submit_button)
        self.submit_button.connect(
            'clicked',
            lambda *_: self.git_clone(),
            None,
        )

        self.set_child(root)

    def git_clone(self):
        git_clone(
            self.url_entry.get_text(),
            self.dir_entry.get_text(),
            self.working_dir,
            self,
        )


class GitBranchesDialog(Adw.Dialog):
    def __init__(self, folder: Nautilus.FileInfo):
        super().__init__()

        self.working_dir = folder.get_location().get_path()

        # fetch the branches from the git repository
        self.branches = self.git_list_branches()
        if not self.branches: return

        # Set up the dialog properties
        self.set_title('Switch Git Branch')
        self.set_content_width(450)
        root = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        header_bar.set_decoration_layout(':close')
        root.add_top_bar(header_bar)
        body = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            spacing=8,
            margin_top=16,
            margin_bottom=16,
            margin_start=16,
            margin_end=16,
        )
        root.set_content(body)
        list_box = Gtk.ListBox(css_classes=['boxed-list-separate'])
        body.append(list_box)

        # Create the list box for the branches
        branch_list = Gtk.ListBox(css_classes=["boxed-list"])
        branch_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        branch_list.set_activate_on_single_click(True)
        # when a row is activated (single-click), call our handler
        branch_list.connect(
            "row-activated",
            lambda listbox, row: self.git_switch_branch(row.get_index()),
        )
        body.append(branch_list)

        for branch in self.branches:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(
                label=branch,
                css_classes=["list-item"],
                margin_top=4,
                margin_bottom=4,
            )
            row.set_child(label)
            branch_list.append(row)

        self.set_child(root)

    def git_list_branches(self):
        return git_list_branches(self.working_dir, self)

    def git_switch_branch(self, branch_index: int):
        git_switch_branch(
            self.branches[branch_index],
            self.working_dir,
            self,
        )


class GitStageCommitDialog(Adw.Dialog):
    def __init__(self, folder: Nautilus.FileInfo):
        super().__init__()

        self.working_dir = folder.get_location().get_path()

        # Set up the dialog properties
        self.set_title('Stage All & Commit')
        self.set_content_width(450)
        root = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        header_bar.set_decoration_layout(':close')
        root.add_top_bar(header_bar)
        body = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            spacing=8,
            margin_top=16,
            margin_bottom=16,
            margin_start=16,
            margin_end=16,
        )
        root.set_content(body)
        list_box = Gtk.ListBox(css_classes=['boxed-list-separate'])
        body.append(list_box)

        # Create the entry for the commit message
        self.commit_message_entry = Adw.EntryRow(title='Commit Message')
        list_box.append(self.commit_message_entry)

        # Create the submit button to call the git_stage_commit method
        self.submit_button = Gtk.Button(
            label='Stage & Commit',
            css_classes=['pill', 'suggested-action'],
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        body.append(self.submit_button)
        self.submit_button.connect(
            'clicked',
            lambda *_: self.git_stage_commit(),
            None,
        )

        self.set_child(root)

    def git_stage_commit(self):
        commit_message = self.commit_message_entry.get_text().strip()
        if not commit_message:
            commit_message = 'Auto-commit by nautilus-git-operations'
        git_stage_commit(
            self.working_dir,
            commit_message,
            self,
        )


class GitCredeentialsDialog(Adw.Dialog):
    def __init__(self, folder: Nautilus.FileInfo):
        super().__init__()

        self.working_dir = folder.get_location().get_path()

        # Set up the dialog properties
        self.set_title("Git Credentials")
        self.set_content_width(450)
        root = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        header_bar.set_decoration_layout(":close")
        root.add_top_bar(header_bar)
        body = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            spacing=8,
            margin_top=16,
            margin_bottom=16,
            margin_start=16,
            margin_end=16,
        )
        root.set_content(body)
        list_box = Gtk.ListBox(css_classes=["boxed-list-separate"])
        body.append(list_box)

        # Create the entries for email, username, and password
        self.email_entry = Adw.EntryRow(title="Email")
        list_box.append(self.email_entry)
        self.username_entry = Adw.EntryRow(title="Username")
        list_box.append(self.username_entry)
        self.password_entry = Adw.EntryRow(title="Password/Token")
        list_box.append(self.password_entry)

        # Save button
        self.save_button = Gtk.Button(
            label="Save",
            css_classes=["pill", "suggested-action"],
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        body.append(self.save_button)
        self.save_button.connect("clicked", lambda *_: self._on_save_clicked(self.save_button))

        self.set_child(root)

    def _on_save_clicked(self, button):
        git_save_credentials(
            self.email_entry.get_text().strip(),
            self.username_entry.get_text().strip(),
            self.password_entry.get_text(),
            self.working_dir,
            self,
        )


class GitMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    def get_background_items(self, folder: Nautilus.FileInfo):
        if not folder or not folder.get_location() or not folder.get_location().get_path():
            return []

        git_clone_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitClone",
            label="Clone Repo…",
        )
        git_clone_item.connect(
            'activate',
            lambda *_: GitCloneDialog(folder).present(None),
        )

        # if no repository is found in the directory, disable the other items
        git_path = folder.get_location().get_path()
        from os import path as os_path
        if not git_path or not os_path.exists(os_path.join(git_path, '.git')):
            return [git_clone_item]

        git_status_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitStatus",
            label="Status…",
        )
        git_status_item.connect(
            'activate',
            lambda *_: git_status(folder.get_location().get_path()),
        )

        git_branches_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitBranches",
            label="Branch…",
        )
        git_branches_item.connect(
            'activate',
            lambda *_: GitBranchesDialog(folder).present(None),
        )

        git_pull_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitPull",
            label="Pull",
        )
        git_pull_item.connect(
            'activate',
            lambda *_: git_pull(folder.get_location().get_path()),
        )

        git_stage_commit_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitStageCommit",
            label="Stage All & Commit…",
        )
        git_stage_commit_item.connect(
            "activate",
            lambda *_: GitStageCommitDialog(folder).present(None),
        )

        git_push_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitPush",
            label="Push",
        )
        git_push_item.connect(
            'activate',
            lambda *_: git_push(folder.get_location().get_path()),
        )

        git_credentials_item = Nautilus.MenuItem(
            name="GitMenuProvider::GitCredentials",
            label="Set Credentials…",
        )
        git_credentials_item.connect(
            'activate',
            lambda *_: GitCredeentialsDialog(folder).present(None),
        )

        git_menu = Nautilus.Menu()
        git_menu.append_item(git_clone_item)
        git_menu.append_item(git_status_item)
        git_menu.append_item(git_branches_item)
        git_menu.append_item(git_pull_item)
        git_menu.append_item(git_stage_commit_item)
        git_menu.append_item(git_push_item)
        git_menu.append_item(git_credentials_item)
        menu_item = Nautilus.MenuItem(
            name='GitMenuProvider::GitMenu',
            label='Git',
        )
        menu_item.set_submenu(git_menu)
        return [menu_item]
