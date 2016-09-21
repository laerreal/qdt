from var_widgets import \
    VarButton, \
    VarToplevel

from Tkinter import \
    Frame

from common import \
    ML as _

class SettingsWidget(Frame):
    def __init__(self, machine_history_tracker, *args, **kw):
        Frame.__init__(self, *args, **kw)

        self.mht = machine_history_tracker

        self.grid()

        self.refresh_after = self.after(0, self.__refresh_single__)

        self.mht.add_on_changed(self.on_changed)

        self.bind("<Destroy>", self.__on_destroy__)

    def apply(self):
        self.mht.remove_on_changed(self.on_changed)

        self.__apply_internal__()

        self.mht.commit()

        self.mht.add_on_changed(self.on_changed)

    def find_node_by_link_text(self, text):
        nid = text.split(":")[0]
        nid = int(nid)
        if nid < 0:
            return None
        else:
            return self.mht.mach.id2node[nid]

    def __refresh_single__(self):
        self.refresh()
        del self.refresh_after

    def __on_destroy__(self, *args):
        self.mht.remove_on_changed(self.on_changed)
        try:
            self.after_cancel(self.refresh_after)
        except AttributeError:
            pass

class SettingsWindow(VarToplevel):
    def __init__(self, machine_history_tracker, *args, **kw):
        VarToplevel.__init__(self, *args, **kw)

        self.mht = machine_history_tracker

        self.grid()

        self.columnconfigure(0, weight = 1)

        self.rowconfigure(0, weight = 1)
        # to be set by child class constructor
        self.sw = None

        self.rowconfigure(1, weight = 0)

        fr = Frame(self)
        fr.grid(
            row = 1,
            column = 0,
            sticky = "NES"
        )
        fr.rowconfigure(0, weight = 1)
        fr.columnconfigure(0, weight = 1)
        fr.columnconfigure(1, weight = 1)
        fr.columnconfigure(2, weight = 1)

        VarButton(fr,
            text = _("Refresh"),
            command = self.refresh
        ).grid(
            row = 0,
            column = 0,
            sticky = "S"
        )

        VarButton(fr,
            text = _("Apply"),
            command = self.apply
        ).grid(
            row = 0,
            column = 1,
            sticky = "S"
        )

        VarButton(fr, 
            text = _("OK"),
            command = self.apply_and_quit
        ).grid(
            row = 0,
            column = 2,
            sticky = "S"
        )

        # Makes settings window always on top.
        # Is there more pythonic interface?
        # http://effbot.org/tkinterbook/wm.htm#Tkinter.Wm.attributes-method
        self.attributes("-topmost", 1)

    def refresh(self):
        self.sw.refresh()

    def apply(self):
        self.sw.apply()
        self.sw.refresh()

    def apply_and_quit(self):
        self.sw.apply()
        self.destroy()