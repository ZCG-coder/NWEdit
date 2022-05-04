from re import L
from typing import *

from src.constants import OSX
from src.modules import json, tk, ttk, ttkthemes, font
from src.Utils.images import get_image
from PIL import Image, ImageTk


# Need these because importing settings is a circular import
def get_theme():
    with open("Config/general-settings.json") as f:
        settings = json.load(f)
    return settings["theme"]


def get_bg():
    style = ttkthemes.ThemedStyle()
    style.set_theme(get_theme())
    return style.lookup("TLabel", "background")


class WinFrame(tk.Toplevel):
    def __init__(
        self,
        master: Union[tk.Tk, tk.Toplevel, Literal["."]],
        title: Text,
        disable: bool = True,
        closable: bool = True,
        icon: tk.PhotoImage = None
    ):
        super().__init__(master)
        FONT_HEIGHT = font.Font().metrics("linespace")

        if OSX:
            self.tk.call(
                "::tk::unsupported::MacWindowStyle", "style", self._w, "simple"
            )
        else:
            self.overrideredirect(True)
        if icon:
            icon_path = icon.cget("file")
            image = Image.open(icon_path)
            image = image.convert("RGBA")
            image = image.resize((FONT_HEIGHT + 3, FONT_HEIGHT + 3))

            icon = ImageTk.PhotoImage(image=image)
        else:
            icon = None
        self.icon = icon
        self.title_text = title
        self.title(title)  # Need a decent message to show on the taskbar
        self.master = master
        self.bg = get_bg()
        self.create_titlebar()
        if closable:
            self.close_button()
            self.bind("<Escape>", lambda _: self.destroy())
        self.window_bindings()

        if disable:
            self.wait_visibility(self)
            self.grab_set()  # Linux WMs might fail to grab the window

        self.focus_force()
        self.attributes("-topmost", True)
        self.bind("<Destroy>", self.on_exit)

        size = ttk.Sizegrip(self)
        size.bind("<B1-Motion>", self.resize)
        size.pack(side="bottom", anchor="se")

    def on_exit(self, _):
        # Release Grab to prevent issues
        self.grab_release()

    def create_titlebar(self):
        self.titleframe = ttk.Frame(self)
        self.titlebar = ttk.Label(self.titleframe, text=self.title_text, compound="left")
        self.titlebar.image = self.icon
        self.titlebar["image"] = self.icon
        self.titlebar.pack(side="left", fill="both", expand=1)

        self.titleframe.pack(fill="x", side="top")

    def add_widget(self, child_frame):
        self.child_frame = child_frame
        self.child_frame.pack(fill="both", expand=True)

    def window_bindings(self):
        self.titlebar.bind("<ButtonPress-1>", self.start_move)
        self.titlebar.bind("<ButtonRelease-1>", self.stop_move)
        self.titlebar.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, _):
        self.x = None
        self.y = None

    def do_move(self, event):
        x = event.x - self.x + self.winfo_x()
        y = event.y - self.y + self.winfo_y()
        self.geometry(f"+{x}+{y}")

    def resize(self, event: tk.Event):
        cursor_x = event.x_root
        cursor_y = event.y_root
        window_x = self.winfo_rootx()
        window_y = self.winfo_rooty()
        self.geometry(f"{cursor_x - window_x}x{cursor_y - window_y}")
        return

    def close_button(self):
        close_button = ttk.Label(self.titleframe)
        close_button.config(image=get_image("close"))
        close_button.pack(side="left")

        close_button.bind("<ButtonRelease>", lambda _: self.destroy())
