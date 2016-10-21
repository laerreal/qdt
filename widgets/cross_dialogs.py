from common import \
    mlget as _

from tkFileDialog import \
    asksaveasfilename

class CrossSaveAsDialog(object):
    def __init__(self, filetypes = None, title = None):
        self.title = _("Save as") if title is None else title

        self.filetypes = [(_("All files"), '.*')] if filetypes is None \
            else filetypes

    def ask(self):
        kw = {
            "title" : self.title.get(),
            "filetypes": [
                (filter_name.get(), filter) for (filter_name, filter) in \
                    self.filetypes
            ]
        }

        return asksaveasfilename(**kw)

def asksaveas(*args, **kw):
    return CrossSaveAsDialog(*args, **kw).ask()