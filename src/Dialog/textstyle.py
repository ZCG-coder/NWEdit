from src.modules import tk, ttk, art
from src.settings import Settings
import sys
import io


def listfonts():
    # A lot of string operations and some stdout magic
    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()

    art.font_list('Test', 'ascii')
    sys.stdout = old_stdout  # Put the old stream back in place
    fonts = buffer.getvalue().split('\n\n')
    
    for index, item in enumerate(fonts):
        fonts[index] = item.split('\n')[0][:-3]
        # Each font is name(spc):(spc), so minus three chars
    return fonts[:-1]
    # Last one is '', which is useless.


class StyleWindow(tk.Toplevel):
    def __init__(self, text, handler):
        super().__init__()
        self.transient('.')
        self.resizable(0, 0)
        self.title('Insert Ascii Art')

        self.text = text

        self.entry = ttk.Entry(self)
        self.entry.pack(fill='x')
        self.entry.insert('end', 'Hello, World')
        
        self.font_var = tk.StringVar()

        self.font = ttk.Combobox(self, state='readonly', values=listfonts(), textvariable=self.font_var)
        self.font.set(listfonts()[0])
        self.font.pack(fill='x')

        self.preview = tk.Text(self, state='disabled', wrap='none')
        self.preview.pack(fill='both')
        
        ttk.Button(self, text='Insert >>', command=self.insert).pack(fill='x')
        
        self.entry.bind('<KeyRelease>', self.update_text)
        self.font_var.trace_add('write', self.update_text)
        self.update_text()
    
    def update_text(self, *_):
        self.preview.config(state='normal')
        self.preview.delete('1.0', 'end')
        try:
            ascii_text = art.text2art(self.entry.get(), font=self.font.get(), chr_ignore=False)
        except art.ArtError:
            ascii_text = art.text2art(self.entry.get(), font=self.font.get(), chr_ignore=True)
        finally:
            self.preview.insert('end', ascii_text)
            self.preview.config(state='disabled')

    def insert(self):
        self.text.insert('insert', self.preview.get('1.0', 'end'))
        self.destroy()
