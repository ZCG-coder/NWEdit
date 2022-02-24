from src.Dialog.commondialog import get_theme
from src.modules import tk, ttk, ttkthemes, os, threading
from src.Dialog.search import finditer_withlineno, find_all
import re


def list_all(directory):
    itemslist = os.listdir(directory)
    files = []
    for file in itemslist:
        path = os.path.abspath(os.path.join(directory, file))
        if os.path.isdir(path):
            files += list_all(path)
        else:
            files.append(path)
    files.sort()
    return files


class SearchInDir(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, path: str, opencommand: callable):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        parent.add(self, text='Search in Directory')

        self.parent = parent
        self.path = path
        self.opencommand = opencommand
        self._style = ttkthemes.ThemedStyle()
        self._style.set_theme(get_theme())
        bg = self._style.lookup("TLabel", "background")
        fg = self._style.lookup("TLabel", "foreground")

        # Tkinter Variables
        self.case = tk.BooleanVar()
        self.regex = tk.BooleanVar()
        self.fullword = tk.BooleanVar()

        self.found = {}
        ttk.Label(self, text="Search: ").pack(side="top",
                                              anchor="nw",
                                              fill="y")
        self.content = tk.Entry(
            self,
            background=bg,
            foreground=fg,
            insertbackground=fg,
            highlightthickness=0,
        )
        self.content.pack(side="top", fill="both")
        ttk.Button(
            self,
            text='Search',
            command=lambda: threading.Thread(target=self.find).start()).pack(
                side='top', fill='x')

        progressbar_frame = ttk.Frame(self)
        self.search_stat = ttk.Label(progressbar_frame,
                                     text="Press 'Search' to start searching.")
        self.search_stat.pack(fill='x')
        self.progressbar = ttk.Progressbar(progressbar_frame)
        self.progressbar.pack(side='top', fill='x')
        progressbar_frame.pack(side='top', fill='both')
        # Checkboxes
        checkbox_frame = ttk.Frame(self)
        self.case_yn = ttk.Checkbutton(checkbox_frame,
                                       text="Case Sensitive",
                                       variable=self.case)
        self.case_yn.pack(side="left")

        self.reg_yn = ttk.Checkbutton(checkbox_frame,
                                      text="RegExp",
                                      variable=self.regex)
        self.reg_yn.pack(side="left")

        self.fullw_yn = ttk.Checkbutton(checkbox_frame,
                                        text="Full Word",
                                        variable=self.fullword)
        self.fullw_yn.pack(side="left")

        checkbox_frame.pack(side='top', fill='both')

        treeframe = ttk.Frame(self)
        self.tree = ttk.Treeview(treeframe, show='tree')
        self.tree.pack(side='left', fill='both', expand=True)

        yscroll = ttk.Scrollbar(treeframe, command=self.tree.yview)
        yscroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=yscroll.set)
        self.tree.bind('<Double-1>', self.on_double_click)
        treeframe.pack(fill='both', expand=True)

        for x in (self.case, self.regex, self.fullword):
            x.trace_add('write', self.find)

        self.content.insert('end', 'e')

    def re_search(self, pat, text, nocase=False, full_word=False, regex=False):
        if nocase and full_word:
            res = [(x[0], x[1])
                   for x in finditer_withlineno(r"\b" + re.escape(pat) +
                                                r"\b", text, (re.IGNORECASE,
                                                              re.MULTILINE))]
        elif full_word:
            res = [(x[0], x[1])
                   for x in finditer_withlineno(r"\b" + re.escape(pat) +
                                                r"\b", text, re.MULTILINE)]
        elif nocase and regex:
            res = [(x[0], x[1])
                   for x in finditer_withlineno(pat, text, (re.IGNORECASE,
                                                            re.MULTILINE))]
        elif regex:
            res = [(x[0], x[1])
                   for x in finditer_withlineno(pat, text, re.MULTILINE)]
        if nocase:
            res = [(x[0], x[1]) for x in find_all(pat, text, case=False)]
        else:
            res = [(x[0], x[1]) for x in find_all(pat, text)]
        return res

    def find(self, *_):
        path = self.path
        files = list_all(path)
        self.found.clear()
        s = self.content.get()

        self.progressbar['value'] = 0
        self.progressbar['maximum'] = len(files)

        if s:
            for file in files:
                new_status = self.progressbar['value'] + 1
                self.progressbar['value'] = new_status
                self.search_stat.config(
                    text=f'Searching in file {new_status}/{len(files)}')
                try:
                    with open(file, 'rb') as f:
                        matches = self.re_search(s,
                                                 f.read().decode('utf-8'),
                                                 nocase=not (self.case.get()),
                                                 regex=self.regex.get())
                except (UnicodeDecodeError, PermissionError):
                    continue
                if not matches:
                    continue
                self.found[file] = [((f'{x[0][0]}.{x[0][1]}',
                                      f'{x[1][0]}.{x[1][1]}'))
                                    for x in matches]
            self.search_stat.config(text='Search Completed!')
            self.update_treeview()

    def update_treeview(self):
        self.search_stat.config(text='Updating results...')
        self.tree.delete(*self.tree.get_children())
        found_list = self.found.keys()
        for k in found_list:
            parent = self.tree.insert('', 'end', text=k)
            for pos in self.found[k]:
                self.tree.insert(parent, 'end', text=' - '.join(pos))
        self.search_stat.config(text='Finished! Press Search to search again.')

    def on_double_click(self, _=None):
        try:
            item = self.tree.focus()
            text = self.tree.item(item, 'text')

            if os.path.isfile(text):
                self.opencommand(text)
            else:
                parent = self.tree.parent(item)
                parenttext = self.tree.item(parent, 'text')
                textbox = self.opencommand(parenttext)
                ls = text.split()
                start = ls[0]
                end = ls[-1]
                textbox.tag_remove('sel', '1.0', 'end')
                textbox.tag_add('sel', start, end)
                textbox.mark_set('insert', start)
                textbox.see('insert')
        except Exception:
            pass
