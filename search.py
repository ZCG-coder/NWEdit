﻿from modules import tk, ttk


class Search:
    def __init__(self, master: tk.Tk, tabwidget: ttk.Notebook, tablist: dict):
        self.master = master
        self.case = tk.BooleanVar()
        self.regexp = tk.BooleanVar()
        self.start = tk.SEL_FIRST
        self.end = tk.SEL_LAST
        self.currtext = tablist[tabwidget.nametowidget(tabwidget.select())].textbox
        if not self.currtext.tag_ranges("sel"):
            self.start = tk.FIRST
            self.end = tk.END
        self.starts = []
        self.search_frame = ttk.Frame(self.currtext.frame)

        self.search_frame.pack(anchor="nw", side="bottom")
        ttk.Label(self.search_frame, text="Search: ").pack(
            side="left", anchor="nw", fill="y"
        )
        self.content = tk.Entry(
            self.search_frame,
            background="black",
            foreground="white",
            insertbackground="white",
            highlightthickness=0,
        )
        self.content.pack(side="left", fill="both")

        forward = ttk.Button(self.search_frame, text="<", width=1)
        forward.pack(side="left")

        backward = ttk.Button(self.search_frame, text=">", width=1)
        backward.pack(side="left")

        ttk.Label(self.search_frame, text="Replacement: ").pack(
            side="left", anchor="nw", fill="y"
        )
        self.repl = tk.Entry(
            self.search_frame,
            background="black",
            foreground="white",
            insertbackground="white",
            highlightthickness=0,
        )
        self.repl.pack(side="left", fill="both")

        self.repl_button = ttk.Button(self.search_frame, text="Replace all")
        self.repl_button.pack(side="left")
        self.clear_button = ttk.Button(self.search_frame, text="Clear All")
        self.clear_button.pack(side="left")

        self.case_yn = ttk.Checkbutton(self.search_frame, text="Case Sensitive", variable=self.case)
        self.case_yn.pack(side="left")

        self.reg_button = ttk.Checkbutton(self.search_frame, text="Regexp", variable=self.regexp)
        self.reg_button.pack(side="left")

        self.clear_button.config(command=self.clear)
        self.repl_button.config(command=self.replace)
        self.forward.config(command=self.nav_forward)
        self.backward.config(command=self.nav_backward)
        self.content.bind("<KeyRelease>", self.find)
        closeicon = tk.PhotoImage(file="Images/close.gif")
        ttk.Button(self.search_frame, image=closeicon, command=self._exit, width=1).pack(
            side="right", anchor="ne"
        )


    def find(self, _=None):
        found = tk.IntVar()
        text = self.currtext
        text.tag_remove("found", "1.0", "end")
        s = self.content.get()
        self.starts.clear()
        if s:
            idx = "1.0"
            while 1:
                idx = text.search(
                    s,
                    idx,
                    noscase=not (self.case.get()),
                    stopindex="end",
                    regexp=self.regexp.get(),
                    count=found,
                )
                if not idx:
                    break
                lastidx = "%s+%dc" % (idx, len(s))
                text.tag_add("found", idx, lastidx)
                self.starts.append(idx)
                text.mark_set("insert", idx)
                text.focus_set()
                idx = lastidx
            text.tag_config("found", foreground="red", background="yellow")
        text.see("insert")

    def replace(self):
        text = self.currtext
        text.tag_remove("found", "1.0", "end")
        s = self.content.get()
        r = self.repl.get()
        if s != "\\" and s:
            idx = "1.0"
            while 1:
                idx = text.search(
                    s,
                    idx,
                    nocase=not (self.case.get()),
                    stopindex="end",
                    regexp=self.regexp.get(),
                )
                if not idx:
                    break
                lastidx = "%s+%dc" % (idx, len(s))
                text.delete(idx, lastidx)
                text.insert(idx, r)
                idx = lastidx

    def clear(self):
        text = self.currtext
        text.tag_remove("found", "1.0", "end")

    def nav_forward(self):
        try:
            text = self.currtext
            curpos = text.index("insert")
            if curpos in self.starts:
                prev = self.starts.index(curpos) - 1
                text.mark_set("insert", self.starts[prev])
                text.see("insert")
                text.focus_set()
        except Exception:
            pass

    def nav_backward(self):
        try:
            text = self.currtext
            curpos = text.index("insert")
            if curpos in self.starts:
                prev = self.starts.index(curpos) + 1
                text.mark_set("insert", self.starts[prev])
                text.see("insert")
                text.focus_set()
        except Exception:
            pass

    def _exit(self):
        self.search_frame.pack_forget()
        self.clear()
        self.currtext.focus_set()