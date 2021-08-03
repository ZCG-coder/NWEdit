from src.modules import tk, ttk, ttkthemes
from src.statusbar import bind_events
from src.Menu.yscrolledframe import ScrollableFrame
from src.Menu.menuitem import MenuItem
from src.constants import WINDOWS
from src.functions import is_dark_color
from src.Dialog.commondialog import get_theme

if WINDOWS:
    from ctypes import windll
    from win32api import GetMonitorInfo, MonitorFromPoint

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080


def set_appwindow(root):
    hwnd = windll.user32.GetParent(root.winfo_id())
    style = windll.user32.GetWindowLongPtrA(hwnd, GWL_EXSTYLE)
    style = style & ~WS_EX_TOOLWINDOW
    style = style | WS_EX_APPWINDOW
    windll.user32.SetWindowLongPtrA(hwnd, GWL_EXSTYLE, style)
    # re-assert the new window style
    root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())


class Menu(ScrollableFrame):
    def __init__(self):
        self.topwin = tk.Toplevel()
        self.topwin.transient('.')
        self.topwin.overrideredirect(0)
        
        self.topwin.overrideredirect(1)
        self.topwin.withdraw()
        super().__init__(self.topwin, relief='groove')
        self.win = self.topwin.master
        self.opened = False

        self.win.update()
        self.x = self.win.winfo_rootx()
        self.y = self.win.winfo_rooty()

    def add_command(self, label, command, image=None, unpost=True, passeventobj=False):
        if image:
            command_label = ttk.Label(self.frame,
                                      text=label,
                                      image=image,
                                      compound="left")
        else:
            command_label = ttk.Label(self.frame, text=label)

        def exec_command(event=None):
            if unpost:
                self.unpost()
            if passeventobj:
                command(event)
            else:
                command()

        command_label.bind('<1>', exec_command)
        bind_events(command_label)
        command_label.pack(side='top', anchor='nw', fill='x')

    def tk_popup(self, x, y):
        self.pack(fill='both', expand=1)
        self.win.update()
        self.update()
        self.topwin.geometry(f'+{x}+{y}')
        self.topwin.deiconify()
        self.opened = True

        self.win.event_add('<<CloseMenu>>', '<1>')
        self.win.event_add('<<Move>>', '<Configure>')
        self.win.bind('<<CloseMenu>>', self.close_menu)
        self.win.bind('<<Move>>', self.unpost)

    def close_menu(self, event=None):
        if not (event.x_root in range(self.topwin.winfo_x(),
                                      self.winfo_x() + self.topwin.winfo_width() + 1)
                and event.y_root in range(self.topwin.winfo_y(),
                                          self.topwin.winfo_y() + self.topwin.winfo_height() + 1)):
            self.unpost()

    def unpost(self, _=None):
        self.opened = False
        self.pack_forget()
        self.topwin.withdraw()
        self.win.event_delete('<<CloseMenu>>')
        self.win.event_delete('<<Move>>')
        self.on_unpost()
    
    def on_unpost(self):
        # Can override
        pass

# This isn't an typo
def add_cascade(self, master_menu, label, cascade):
    style = ttkthemes.ThemedStyle()
    style.set_theme(get_theme())
    bg = style.lookup("TLabel", "background")
    if is_dark_color(bg):
        self.dropdown_image = tk.PhotoImage(file='Images/next-tab-light.gif')
    else:
        self.dropdown_image = tk.PhotoImage(file='Images/next-tab.gif')

    expand = Menu()

    def expand_menu(event):
        label = event.widget
        x = label.winfo_rootx() + label.winfo_width()
        y = label.winfo_rooty()
        expand.tk_popup(x, y)

        expand.on_unpost = master_menu.unpost

        for itemindex, name in enumerate(cascade.items):
            if type(name).__name__ == 'list':
                break
            command = cascade.commands[itemindex]
            image = cascade.images[itemindex]
            expand.add_command(name, command=command, image=image)
    master_menu.add_command(label, command=expand_menu, image=self.dropdown_image, unpost=False, passeventobj=True)

Menu.add_cascade = add_cascade


class Menubar(ttk.Frame):
    def __init__(
            self,
            master: tk.Tk,
    ) -> None:
        super().__init__(master)
        self.pack(fill="x", side="top")
        self.master = master
        self.items_frame = ttk.Frame(self)
        self.items_frame.place(relx=1.0, x=0, y=1, anchor='ne')
        self.search_entry = ttk.Entry(self.items_frame, width=15)
        self.search_entry.pack(side='left', fill='both')
        self.search_button = ttk.Button(self.items_frame,
                                        text='>>',
                                        width=3,
                                        command=self._search_command)
        self.search_button.pack(side='left')
        self.commands = {}
        self.menus = []
        self.menu_opened = None
        self.style = ttkthemes.ThemedStyle()
        self.style.set_theme(get_theme())
        self.bg = self.style.lookup("TLabel", "background")
        if is_dark_color(self.bg):
            self.close_icon = tk.PhotoImage(file="Images/close.gif")
            self.maximise_icon = tk.PhotoImage(file="Images/maximise-light.gif")
            self.minimise_icon = tk.PhotoImage(file="Images/minimise-light.gif")
        else:
            self.close_icon = tk.PhotoImage(file="Images/close-dark.gif")
            self.maximise_icon = tk.PhotoImage(file="Images/maximise.gif")
            self.minimise_icon = tk.PhotoImage(file="Images/minimise.gif")
            self.dropdown_image = tk.PhotoImage(file='Images/next-tab.gif')
        if WINDOWS:
            self.x_pos = self.master.winfo_rootx()
            self.y_pos = self.master.winfo_rooty()
            self.geometry = self.master.winfo_geometry()
            self.maximise_count = 0
            self.maximised = False
            self.init_custom_title()

    def init_custom_title(self):
        self.bind('<1>', self.start_move)
        self.bind('<ButtonRelease-1>', self.stop_move)
        self.bind('<B1-Motion>', self.moving)

        self.master.bind('<Map>', self.frame_mapped)

        controls_frame = ttk.Frame(self.items_frame)
        controls_frame.pack(side='right')

        minimise = ttk.Label(controls_frame, image=self.minimise_icon)
        minimise.pack(side='left')
        bind_events(minimise)
        minimise.bind('<1>', self.minimise)

        maximise = ttk.Label(controls_frame, image=self.maximise_icon)
        maximise.pack(side='left')
        bind_events(maximise)
        maximise.bind('<1>', self.maximise)

        close = ttk.Label(controls_frame, image=self.close_icon)
        close.pack(side='left')
        bind_events(close)
        close.bind('<1>', lambda _: self.master.destroy())

        self.master.focus_set()
        self.master.after(10, lambda: set_appwindow(self.master))
        self.master.update_idletasks()

    def frame_mapped(self, _=None):
        self.master.update_idletasks()
        self.master.overrideredirect(1)
        self.master.state('normal')

    def start_move(self, event):
        self.x_pos = event.x
        self.y_pos = event.y

    def stop_move(self, _):
        self.x_pos = None
        self.y_pos = None

    def moving(self, event):
        if self.maximised:
            self.master.geometry(self.geometry)
            self.maximise_count -= 1
            self.maximised = False
        x = (event.x_root - self.x_pos)
        y = (event.y_root - self.y_pos)
        self.master.geometry(f"+{x}+{y}")

    def maximise(self, _=None):
        self.master.update_idletasks()
        geometry = self.master.winfo_geometry()
        if not self.maximise_count % 2:
            monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
            work_area = monitor_info.get("Work")
            self.master.geometry(f"{work_area[2]}x{work_area[3]}+0+0")
            self.maximised = True
        else:
            self.master.geometry(self.geometry)
            self.maximised = False
        self.geometry = geometry
        self.maximise_count += 1

    def minimise(self, _=None):
        self.master.withdraw()
        new = tk.Toplevel(self.master)
        new.iconify()

        def focusin(_):
            new.destroy()
            self.master.deiconify()

        new.bind('<FocusIn>', focusin)

    def _search_command(self):
        text = self.search_entry.get()
        menu = Menu()
        for item in sorted(self.commands.keys()):
            if text in item:
                p_list = self.commands[item]
                command = p_list[1]
                image = p_list[2]
                menu.add_command(item, command, image)
        menu.tk_popup(
            self.search_button.winfo_rootx() + self.search_button.winfo_width(),
            self.search_button.winfo_rooty() + self.search_button.winfo_height())

    def add_cascade(self, label: str, menu: MenuItem) -> None:
        dropdown = Menu()
        for index, item in enumerate(menu.items):
            command = menu.commands[index]
            image = menu.images[index]
            if not type(item).__name__ == 'list':
                dropdown.add_command(item, command, image)
                self.commands[item] = [item, command, image]
            
            else:
                expand = MenuItem()
                for itemindex, name in enumerate(item[1:]):
                    cmd = command[itemindex]
                    img = image[itemindex]
                    expand.add_command(name, cmd, img)
                dropdown.add_cascade(dropdown, item[0], expand)

        label_widget = ttk.Label(
            self,
            text=label,
            padding=[1, 3, 6, 1],
            font="Arial 12",
        )

        label_widget.pack(side='left', fill='both', anchor='nw')

        def click(_):
            self.menu_opened = dropdown
            dropdown.tk_popup(
                label_widget.winfo_rootx(),
                label_widget.winfo_rooty() + self.winfo_height(),
            )

        def enter(event):
            if self.menu_opened:
                if self.menu_opened.opened:
                    self.menu_opened.unpost()
                    click(event)
            label_widget.state(('active',))

        def leave(_):
            label_widget.state(('!active',))

        label_widget.bind('<Leave>', leave)
        label_widget.bind('<Enter>', enter)
        label_widget.bind("<1>", click, True)