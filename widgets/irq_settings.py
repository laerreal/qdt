from .settings_window import \
    SettingsWidget, \
    SettingsWindow

from common import \
    mlget as _

from .var_widgets import \
    VarLabelFrame, \
    VarLabel

from qemu import \
    MOp_SetIRQAttr, \
    MOp_SetIRQEndPoint, \
    MachineNodeOperation, \
    IRQHub, \
    DeviceNode

from six.moves import \
    range as xrange

from six.moves.tkinter import \
    BOTH, \
    StringVar

from six.moves.tkinter_ttk import \
    Combobox

from .device_settings import \
    DeviceSettingsWidget

from .hotkey import \
    HKEntry

class IRQSettingsWidget(SettingsWidget):
    def __init__(self, irq, *args, **kw):
        SettingsWidget.__init__(self, irq, *args, **kw)

        self.irq = irq

        for pfx, txt in [
            ("src_", _("Source")),
            ("dst_", _("Destination"))
        ]:
            lf = VarLabelFrame(self, text = txt)
            lf.pack(fill = BOTH, expand = False)

            lf.columnconfigure(0, weight = 0)
            lf.columnconfigure(1, weight = 1)

            for row in xrange(0, 3):
                lf.rowconfigure(row, weight = 1)

            l = VarLabel(lf, text = _("Node"))
            l.grid(row = 0, column = 0, sticky = "NE")

            node_var = StringVar()
            node_var.trace_variable("w", self.on_node_text_changed)
            node_cb = Combobox(lf,
                textvariable = node_var,
                values = [],
                state = "readonly"
            )
            node_cb.grid(row = 0, column = 1, sticky = "NEW")

            index_l = VarLabel(lf, text = _("GPIO index"))
            index_l.grid(row = 1, column = 0, sticky = "NE")

            index_var = StringVar()
            index_e = HKEntry(lf, textvariable = index_var)
            index_e.grid(row = 1, column = 1, sticky = "NEW")

            name_l = VarLabel(lf, text = _("GPIO name"))
            name_l.grid(row = 2, column = 0, sticky = "NE")

            name_var = StringVar()
            name_e = HKEntry(lf, textvariable = name_var)
            name_e.grid(row = 2, column = 1, sticky = "NEW")

            for v in ["lf", "node_var", "node_cb",
                      "index_l", "index_e", "index_var", 
                      "name_l", "name_e", "name_var"]:
                setattr(self, pfx + v, locals()[v])

    def on_node_text_changed(self, *args):
        for pfx in [ "src", "dst" ]:
            node_var = getattr(self, pfx + "_node_var")
            node_text = node_var.get()

            if not node_text:
                continue

            node = self.find_node_by_link_text(node_text)
            node_is_device = isinstance(node, DeviceNode)

            index_l = getattr(self, pfx + "_index_l")
            index_e = getattr(self, pfx + "_index_e")
            name_l = getattr(self, pfx + "_name_l")
            name_e = getattr(self, pfx + "_name_e")

            dev_widgets = [index_l, index_e, name_l, name_e]

            if node_is_device:
                for w in dev_widgets:
                    w.config(state = "normal")
            else:
                for w in dev_widgets:
                    w.config(state = "disabled")

    def __apply_internal__(self):
        irq = self.irq

        for pfx in [ "src", "dst" ]:
            var = getattr(self, pfx + "_node_var")
            new_val = self.find_node_by_link_text(var.get()) 

            cur_val = getattr(irq, pfx + "_node")

            if not new_val == cur_val:
                # if end node type is changed then reset index and name
                if isinstance(new_val, DeviceNode) \
                   and not isinstance(cur_val, DeviceNode):
                    getattr(self, pfx + "_index_var").set("0")
                    getattr(self, pfx + "_name_var").set("")
                elif isinstance(new_val, IRQHub) \
                     and not isinstance(cur_val, IRQHub):
                    getattr(self, pfx + "_index_var").set("")
                    getattr(self, pfx + "_name_var").set("")

                self.mht.stage(
                    MOp_SetIRQEndPoint,
                    pfx + "_node",
                    new_val,
                    irq.id
                )

            for attr in [ "index", "name" ]:
                var = getattr(self, pfx + "_" + attr + "_var")
                new_val = var.get()
                if not new_val:
                    if attr is "index":
                        new_val = 0
                    else:
                        new_val = None

                cur_val = getattr(irq, pfx + "_" +attr)

                if not new_val == cur_val:
                    self.mht.stage(
                        MOp_SetIRQAttr,
                        pfx + "_" + attr,
                        new_val,
                        irq.id
                    )

        self.mht.set_sequence_description(_("IRQ line configuration."))

    def refresh(self):
        SettingsWidget.refresh(self)

        nodes = [ DeviceSettingsWidget.gen_node_link_text(node) \
            for node in self.mach.devices + self.mach.irq_hubs ]

        for pfx in [ "src", "dst" ]:
            cb = getattr(self, pfx + "_node_cb")
            cb.config(values = nodes)

            # IRQ line end (source or destination)
            end_node = getattr(self.irq, pfx)[0]
            node_text = DeviceSettingsWidget.gen_node_link_text(end_node)
            node_var = getattr(self, pfx + "_node_var")
            node_var.set(node_text)

            if isinstance(end_node, DeviceNode):
                index_var = getattr(self, pfx + "_index_var")
                name_var = getattr(self, pfx + "_name_var")

                # IRQ descriptor in machine description
                end_desc = getattr(self.irq, pfx)

                index_var.set(str(end_desc[1]))

                if end_desc[2] is not None:
                    name_var.set(str(end_desc[2]))
                else:
                    name_var.set("")

    def on_changed(self, op, *args, **kw):
        if not isinstance(op, MachineNodeOperation):
            return

        if op.writes_node():
            if not self.irq.id in self.mach.id2node:
                self.destroy()
            else:
                self.refresh()
        elif isinstance(op, MOp_SetIRQAttr):
            if op.node_id == self.irq.id:
                self.refresh()

class IRQSettingsWindow(SettingsWindow):
    def __init__(self, *args, **kw):
        irq = kw.pop("irq")

        SettingsWindow.__init__(self, irq, *args, **kw)

        self.title(_("IRQ line settings"))

        self.set_sw(IRQSettingsWidget(irq, self.mach, self))
        self.sw.grid(row = 0, column = 0, sticky = "NEWS")
