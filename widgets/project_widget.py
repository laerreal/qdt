from var_widgets import \
    VarTreeview

from ttk import \
    Notebook

from machine_widget import \
    MachineWidget

from qemu import \
    MachineNode

from Tkinter import \
    PanedWindow

from common import \
    ML as _

class DescriptionsTreeview(VarTreeview):
    def __init__(self, descriptions, *args, **kw):
        VarTreeview.__init__(self, *args, **kw)

        self.descs = descriptions

        self.heading("#0", text = _("Name"))

        self.after(0, self.update)

    def update(self):
        self.delete(*self.get_children())

        for i, d in enumerate(self.descs):
            self.insert('', i, text = d.name)

class ProjectWidget(PanedWindow):
    def __init__(self, project, *args, **kw):
        PanedWindow.__init__(self, *args, **kw)

        self.p = project

        self.tv_descs = DescriptionsTreeview(self.p.descriptions)
        self.add(self.tv_descs)

        self.nb_descriptions = Notebook(self)
        self.add(self.nb_descriptions)

        self.desc2w = {}
        for desc in self.p.descriptions:
            if not isinstance(desc, MachineNode):
                continue

            self.desc2w[desc] = []

            for l in self.p.get_layouts(desc.name):
                w = MachineWidget(desc, self)
                try:
                    w.mdw.SetLayout(l)
                except:
                    if self.desc2w[desc]:
                        continue

                self.desc2w[desc].append(w)
                self.nb_descriptions.add(w, text = desc.name)

    def refresh_layouts(self):
        for desc, widgets in self.desc2w.iteritems():

            layouts = []
            for w in widgets:
                if not isinstance(w, MachineWidget):
                    continue

                layouts.append(w.mdw.GetLayout())

            self.p.layouts.remove(
                *[ e for e in self.p.layouts if e[0] == desc.name ]
            )
            for l in layouts:
                self.p.layouts.append((desc.name, l))

    def undo(self):
        self.p.pht.undo()

    def redo(self):
        self.p.pht.do()

    def can_do(self):
        return self.p.pht.can_do()

    def can_redo(self):
        return self.p.pht.can_do()