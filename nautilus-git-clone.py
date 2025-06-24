import gi
gi.require_version('Nautilus', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')
from gi.repository import GObject, Adw, Gtk, Nautilus

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
        git_url = self.url_entry.get_text()
        dir_name = self.dir_entry.get_text()
        if not git_url or not dir_name:
            error_dialog = Adw.AlertDialog(
                heading="Git Clone Error",
                body="Please provide both a repository URL and a target directory name.",
            )
            error_dialog.add_response(
                id='Dismiss',
                label='Dismiss',
            )
            error_dialog.present(self)
            return

        # regex to check if the directory name is valid, it can only contain letters, numbers, underscores, hyphens, dots, and spaces
        import re
        if not re.match(r'^[\w\-. ]+$', dir_name):
            error_dialog = Adw.AlertDialog(
                heading="Git Clone Error",
                body="Invalid directory name. Only letters, numbers, underscores, hyphens, dots, and spaces are allowed.",
            )
            error_dialog.add_response(
                id='Dismiss',
                label='Dismiss',
            )
            error_dialog.present(self)
            return

        # regex to check if the URL is valid (doesnt cover all cases, but a good start)
        if not re.match(r'^(https?|git)://[^\s/$.?#].[^\s]*$', git_url):
            error_dialog = Adw.AlertDialog(
                heading="Git Clone Error",
                body="Invalid repository URL. Please provide a valid URL starting with http://, https://, or git://.",
            )
            error_dialog.add_response(
                id='Dismiss',
                label='Dismiss',
            )
            error_dialog.present(self)
            return

        # if the direcory exists, create a new directory name by appending a number to the directory name
        import os
        target_path = os.path.join(self.working_dir, dir_name)
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(self.working_dir, f"{dir_name}_{counter}")
            counter += 1

        # set working directory to self.working_dir then run git clone command with the provided URL and directory name
        import subprocess
        try:
            subprocess.run(['git', 'clone', git_url, target_path], check=True, cwd=self.working_dir)
        except subprocess.CalledProcessError as e:
            error_dialog = Adw.AlertDialog(
                heading="Git Clone Error",
                body=f"Failed to clone repository: {e}",
            )
            error_dialog.add_response(
                id='Dismiss',
                label='Dismiss',
            )
            error_dialog.present(self)
            return

        self.close()


class GitCloneMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    def get_background_items(self, folder: Nautilus.FileInfo):
        git_clone_item = Nautilus.MenuItem(
            name='GitCloneMenuProvider::CloneGitRepo',
            label='Clone Git Repo…',
        )
        git_clone_item.connect(
            'activate',
            lambda *_: GitCloneDialog(folder).present(None),
            None,
        )
        return [git_clone_item]
