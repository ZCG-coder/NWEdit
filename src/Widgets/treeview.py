from src.constants import OSX, logger
from src.Dialog.commondialog import StringInputDialog
from src.Dialog.fileinfodialog import FileInfoDialog
from src.modules import font, json, os, send2trash, shutil, tk, ttk
from src.SettingsParser.extension_settings import FileTreeIconSettings
from src.SettingsParser.interval_settings import IntervalSettings
from src.Utils.color_utils import is_dark_color


class FileTree(ttk.Frame):
    """
    Treeview to select files
    """

    def __init__(self, master=None, opencommand=None):
        self.expanded = []
        self.temp_path = []
        self._style = ttk.Style()
        self.bg = self._style.lookup("TLabel", "background")
        super().__init__(master)
        self.tree = ttk.Treeview(self, show="tree")
        self.yscroll = ttk.Scrollbar(self, command=self.tree.yview)
        self.xscroll = ttk.Scrollbar(self, command=self.tree.xview, orient="horizontal")
        self.yscroll.pack(side="right", fill="y")
        self.xscroll.pack(side="bottom", fill="x")
        self.tree["yscrollcommand"] = self.yscroll.set
        self.tree["xscrollcommand"] = self.xscroll.set
        self.master = master
        self.opencommand = opencommand
        self.root_node = None

        self.icon_settings = FileTreeIconSettings()
        self.icon_settings.set_theme(is_dark_color(self.bg))
        self.icons = []
        self.temp_path = []  # IMPORTANT! Reset after use

        self.interval_settings = IntervalSettings()
        self.refresh_interval = self.interval_settings.get_settings("TreeviewRefresh")

        self.pack(side="left", fill="both", expand=1)
        self.tree.bind("<Double-1>", self.on_double_click_treeview)
        self.tree.tag_bind(
            "file",
            "<Button-2>" if OSX else "<Button-3>",
            lambda event: self.right_click(event, False),
        )
        self.tree.tag_bind(
            "subfolder",
            "<Button-2>" if OSX else "<Button-3>",
            lambda event: self.right_click(event, True),
        )
        self.tree.update()

        self.tree.tag_configure("subfolder", foreground="#448dc4")
        italic = font.Font(self)
        italic.config(slant="italic")
        self.tree.tag_configure("empty", font=italic, foreground="#C2FF74")

        self.tree.pack(fill="both", expand=1, anchor="nw")
        self.tree.bind("<<TreeviewOpen>>", lambda _: self.open_dir())
        self.tree.bind("<<TreeviewClose>>", lambda _: self.close_dir())

        with open("EditorStatus/treeview_stat.json") as f:
            self.load_status(f)

    def remove(self, item: str) -> None:
        path = self.get_path(item, True)
        try:
            send2trash.send2trash(path)  # Send to trash is a good idea if possible
        except (send2trash.TrashPermissionError, OSError):
            # Linux OSs might have problems with the trash bin
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        self.refresh_tree(True)  # Reset to root path to avoid any problems

    def rename(self, item: str) -> None:
        path = self.get_path(item, True)
        dialog = StringInputDialog(self.master, "Rename", "New name:")
        if not dialog.result:
            return
        try:
            newdir = os.path.join(self.path, dialog.result)
            shutil.move(path, newdir)
        except (IsADirectoryError, FileExistsError):
            pass
        finally:
            self.refresh_tree(True)

    def get_info(self, item: str) -> None:
        path = self.get_path(item, True)
        FileInfoDialog(self.master, path)

    def new_folder(self, item: str, isdir: bool) -> None:
        win = StringInputDialog(self.master, "New Folder", "Name:")
        if name := win.result:
            item_path = self.get_path(item, isdir)
            path = os.path.join(item_path, name)
            os.mkdir(path)
            self.path = path
        self.refresh_tree()

    def new_file(self, item: str, isdir: bool) -> None:
        win = StringInputDialog(self.master, "New File", "Name:")
        if name := win.result:
            item_path = self.get_path(item, isdir)
            path = os.path.join(item_path, name)
            with open(path, "w") as f:
                f.write("")
        self.refresh_tree()

    def close_dir(self):
        tree = self.tree
        item = self.tree.focus()

        self.expanded.remove(item)

    def open_dir(self, directory_item="") -> None:
        """Save time by loading directory only when needed, so we don't have to recursivly process the directories."""
        tree = self.tree
        if directory_item:
            item = directory_item
        else:
            item = tree.focus()
        self.expanded.append(item)

        item_text = tree.item(item, "text")

        self.temp_path = []
        self.get_parent(item)
        path = f'{"/".join(reversed(self.temp_path))[1:]}/{item_text}'
        if os.path.isfile(path):
            return
        self.path = path
        logger.debug(f"Opened tree item, path: {self.path}")
        tree.delete(*tree.get_children(item))
        self.process_directory(item, path=self.path)

    def process_directory(
            self, parent: str, showdironly: bool = False, path: str = ""
    ) -> None:
        if os.path.isfile(path):
            return
        items = sorted(os.listdir(path))
        if not items:
            self.tree.insert(parent, "end", text="Empty", tags=("empty",))
        last_dir_index = 0
        for p in items:
            abspath = os.path.join(path, p)
            isdir = os.path.isdir(abspath)
            if isdir:
                oid = self.tree.insert(
                    parent,
                    last_dir_index,
                    text=p,
                    tags=("subfolder",),
                    open=False,
                    image=self.icon_settings.folder_icon,
                )
                last_dir_index += 1
                if not showdironly:
                    self.tree.insert(
                        oid, 0, text="Loading...", tags=("empty",)
                    )  # Just a placeholder, will load if needed
            else:
                if showdironly:
                    return
                extension = p.split(".")
                self.icons.append(self.icon_settings.get_icon(extension[-1]))
                self.tree.insert(
                    parent,
                    "end",
                    text=p,
                    open=False,
                    image=self.icons[-1],
                    tags=("file",),
                )

    def on_double_click_treeview(self, event: tk.Event, destroy: bool = False) -> None:
        tree = self.tree
        item = tree.identify("item", event.x, event.y)
        name = self.get_path(item, True)
        self.opencommand(name)
        if destroy:
            self.master.destroy()

    def get_parent(self, item: str) -> None:
        """Find the path to item in treeview"""
        tree = self.tree
        parent_iid = tree.parent(item)
        parent_text = tree.item(parent_iid, "text")
        self.temp_path.append(parent_text)
        if parent_text:
            self.get_parent(parent_iid)

    def get_path(self, item: str, append_name: bool = False) -> str:
        self.temp_path = []
        self.get_parent(item)
        self.temp_path.reverse()
        self.temp_path.remove("")
        if append_name:
            self.temp_path.append(self.tree.item(item, "text"))
        return os.path.abspath("/".join(self.temp_path))

    def right_click(self, event: tk.Event, isdir: bool, item: str = "") -> None:
        menu = tk.Menu(self.master)
        if not item:
            item = self.tree.identify("item", event.x, event.y)
        self.tree.selection_set(item)

        new_cascade = tk.Menu(menu)
        new_cascade.add_command(
            label="New File", command=lambda: self.new_file(item, isdir)
        )
        new_cascade.add_command(
            label="New Directory", command=lambda: self.new_folder(item, isdir)
        )
        menu.add_cascade(menu=new_cascade, label="New...")
        menu.add_separator()
        menu.add_command(label="Get Info", command=lambda: self.get_info(item))
        menu.add_separator()
        menu.add_command(label="Rename file", command=lambda: self.rename(item))
        menu.add_command(label="Move to Trash", command=lambda: self.remove(item))
        menu.add_separator()
        menu.add_command(label="Refresh", command=self.advanced_refresh)

        menu.tk_popup(event.x_root, event.y_root)

    def refresh_tree(self, reset=False) -> None:
        self.tree.delete(*self.tree.get_children())
        if reset:
            abspath = os.path.abspath(self.orig_path)
        else:
            abspath = os.path.abspath(self.path)
        self.root_node = self.tree.insert(
            "", "end", text=abspath, open=True, tags=("root",)
        )
        self.process_directory(self.root_node, path=abspath)

    def set_path(self, new_path: os.PathLike):
        self.tree.delete(*self.tree.get_children())
        abspath = os.path.abspath(new_path)
        self.path = abspath

        self.orig_path = abspath
        self.root_node = self.tree.insert(
            "", "end", text=abspath, open=True, tags=("root",)
        )
        self.process_directory(self.root_node, path=abspath)

    def advanced_refresh(self):
        path = self.orig_path
        with open("EditorStatus/treeview_stat.json", "w") as f:
            self.write_status(f)
        with open("EditorStatus/treeview_stat.json") as f:
            self.load_status(f)

    def write_status(self, fp):
        state = {
            "path"              : self.orig_path,
            "expandedNodes"     : self.expanded,
            "yScrollbarLocation": self.yscroll.get(),
            "xScrollbarLocation": self.xscroll.get()
        }

        with fp as f:
            json.dump(state, f)

    def load_status(self, fp):
        with fp as f:
            status = json.load(f)
        self.path = self.orig_path = status["path"]
        self.refresh_tree(True)

        for item in status["expandedNodes"]:
            self.tree.item(item, open=True)
            self.open_dir(item)

        self.expanded = status["expandedNodes"]

        y_scroll_location = status["yScrollbarLocation"]
        x_scroll_location = status["xScrollbarLocation"]
        self.tree.yview_moveto(y_scroll_location[0])
        self.tree.xview_moveto(x_scroll_location[0])
