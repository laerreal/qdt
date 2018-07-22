from common import (
    mlget as _
)
from widgets import (
    VarButton,
    HKEntry,
    VarToplevel,
    CanvasDnD,
    VarTk
)
from inspect import (
    getmro,
    isclass
)
from math import (
    pi,
    sin,
    cos,
    atan2
)
from bisect import (
    bisect_left
)
from six.moves.tkinter import (
    END,
    StringVar
)

class Const(object):
    ico = u"Const"

    def __init__(self):
        self.str_value = None

class Op(object):
    ico = None
    # no limitations for operands amount
    # either integer or tuple of 2 integers (min & max)
    op_amount = None
    # no information about return values amount
    ret_amount = None

    def __init__(self, *operands):
        self.operands = operands

    def __getitem__(self, idx):
        return self.operands[idx]

class Bin(Op):
    __py_op__ = None
    op_amount = 2 # exactly 2 operands
    ret_amount = 1 # returns 1 value

    def __py__(self, w):
        self[0].__py__(w)
        w(self.__py_op__)
        self[1].__py__(w)

class Add(Bin):
    ico = u"+"
    __py_op__ = "+"

    def __eval__(self, a, b):
        return a + b

class Sub(Bin):
    ico = u"\u2212"
    __py_op__ = "-"

    def __eval__(self, a, b):
        return a - b

class Mul(Bin):
    ico = u"\u00d7"
    __py_op__ = "*"

    def __eval__(self, a, b):
        return a * b

class Div(Bin):
    ico = u"/"
    __py_op__ = "/"

    def __eval__(self, a, b):
        return a / b

class IntDiv(Bin):
    ico = u"//"
    __py_op__ = "//"

    def __eval__(self, a, b):
        return a // b

class Mod(Bin):
    ico = u"mod"
    __py_op__ = "%"

    def __eval__(self, a, b):
        return a % b

class DnDGroup(object):
    def __init__(self, w, anchor_id, items):
        self.anchor_id = anchor_id
        self.items = items
        w.bind("<<DnDDown>>", self.on_dnd_down, "+")

    def on_dnd_down(self, event):
        w = event.widget
        a_id = self.anchor_id
        if w.dnd_dragged != a_id:
            return
        self.prev = w.canvas.coords(a_id)[:2]
        self.__moved = w.bind("<<DnDMoved>>", self.on_dnd_moved, "+")
        self.__up = w.bind("<<DnDUp>>", self.on_dnd_up, "+")

    def on_dnd_moved(self, event):
        w = event.widget
        a_id = self.anchor_id
        px, py = self.prev

        x, y = w.canvas.coords(a_id)[:2]
        dx, dy = x - px, y - py
        self.prev = x, y

        coords = w.canvas.coords
        for i in self.items:
            xy = coords(i)
            if len(xy) == 2:
                x0, y0 = xy
                coords(i, x0 + dx, y0 + dy)
            else:
                x0, y0, x1, y1 = xy                coords(i, x0 + dx, y0 + dy, x1 + dx, y1 + dy)

    def on_dnd_up(self, event):
        w = event.widget
        w.unbind("<<DnDMoved>>", self.__moved)
        w.unbind("<<DnDUp>>", self.__up)

def slot(x, y):
    return x - 10, y - 10, x + 10, y + 10

class OpWgt(object):

    def __init__(self, op_class):
        self.op = op_class()
        self.op_id = None
        self.in_slots = []
        self.out_slots = []

    def init(self, w, x, y):
        c = w.canvas
        op = self.op

        in_slots = self.in_slots
        I = op.op_amount
        step = pi / I
        a = -pi + step / 2

        rad = 30

        i = 0
        while i < I:
            sx, sy = x + rad * cos(a), y + rad * sin(a)
            in_slots.append(c.create_rectangle(slot(sx, sy)))
            a += step
            i += 1

        out_slots = self.out_slots
        I = op.ret_amount
        step = pi / I
        a = pi - step / 2

        i = 0
        while i < I:
            sx, sy = x + rad * cos(a), y + rad * sin(a)
            out_slots.append(c.create_rectangle(slot(sx, sy)))
            a -= step
            i += 1

        op_id = c.create_text(x, y, text = op.ico, tag = "DnD")
        self.op_id = op_id
        # bounds = c.bbox(op_id)
        # width = bounds[2] - bounds[0]
        # height = bounds[3] - bounds[1]
        # c.coords(op_id, x - width / 2, y - height / 2)
        DnDGroup(w, op_id, self.in_slots + self.out_slots)

    def ids(self):
        return [self.op_id] + self.in_slots + self.out_slots

CONST_PADDING = 5

class ConstWgt(object):
    def __init__(self):
        self.c = Const()

    def init(self, w, x, y):
        c = w.canvas

        self.frame_id = c.create_rectangle(
            x - CONST_PADDING, y - CONST_PADDING,
            x + CONST_PADDING, y + CONST_PADDING,
            fill = "white",
            tag = "DnD"
        )
        self.text_id = c.create_text(x, y, text = "")
        self.update(w)

        DnDGroup(w, self.frame_id, [self.text_id])

    def update(self, w):
        c = w.canvas
        text_id = self.text_id

        val = self.c.str_value

        color = "black"

        if val is None:
            text = ""
        elif val == "":
            text = '""'
            color = "gray"
        else:
            text = val

        c.itemconfig(text_id, text = text, fill = color)

        bounds = c.bbox(text_id)
        c.coords(self.frame_id,
            bounds[0] - CONST_PADDING, bounds[1] - CONST_PADDING,
            bounds[2] + CONST_PADDING, bounds[3] + CONST_PADDING
        )

    def ids(self):
        return [self.text_id, self.frame_id]

class VarDialog(VarToplevel):
    def __init__(self, *a, **kw):
        VarToplevel.__init__(self, *a, **kw)

        self.transient(self.master)
        self.grab_set()

class ConstEdit(VarDialog):
    def __init__(self, const_wgt, *a, **kw):
        VarDialog.__init__(self, *a, **kw)

        self.title(_("Edit constant"))

        self.cw = const_wgt

        self.grid()
        self.rowconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 0)
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 1)

        v = self.var = StringVar()
        e = self.entry = HKEntry(self, textvariable = v)
        e.grid(row = 0, column = 0, columnspan = 2, sticky = "NESW")

        e.focus_set()

        val = const_wgt.c.str_value

        if val is None:
            v.set("")
        elif val == "":
            v.set('""')
        else:
            v.set(val)

        VarButton(self, text = _(u"Ok"), command = self.on_ok).grid(
            row = 1, column = 0, sticky = "W"
        )
        VarButton(self, text = _(u"Cancel"), command = self.on_cancel).grid(
            row = 1, column = 1, sticky = "E"
        )

        self.bind("<Return>", self.on_ok, "+")
        self.bind("<Escape>", self.on_cancel, "+")

        self.after(10, self.after_init)

    def after_init(self):
        e = self.entry

        e.selection_range(0, END)
        e.icursor(END)

    def on_cancel(self, __ = None):
        # __ is required to use this as a keyboard event key handler
        self.destroy()

    def on_ok(self, __ = None):
        cw = self.cw

        val = self.var.get()
        if val == "":
            cw.c.str_value = None
        elif val == '""' or val == "''" or val == '""""""' or val == "''''''":
            cw.c.str_value = ""
        else:
            cw.c.str_value = val

        cw.update(self.master)
        self.destroy()

OPERATORS = [x for x in globals().values() if (
    isclass(x)
    and Op in getmro(x)
    and x.ico is not None
)]


# operator selection circle
OP_CIRCLE_R = 100
# operator selection highlighting
OP_HL_CIRCLE_R = 20
OP_HL_THRESHOLD_1 = 50.0 ** 2
OP_HL_THRESHOLD_2 = 150.0 ** 2

SHORTCUTS = tuple(OPERATORS + [
    Const
])

class move_centred(object):
    def __init__(self, wgt, x, y, w = None, h = None):
        self.wgt, self.x, self.y, self.w, self.h = wgt, x, y, w, h
        wgt.after(10, self.move_centred)

    def move_centred(self):
        wgt = self.wgt

        w, h = self.w, self.h
        if w is None:
            w = wgt.winfo_width()
        if h is None:
            h = wgt.winfo_height()

        wgt.geometry("%ux%u+%u+%u" % (
            w, h, self.x - (w >> 1), self.y - (h >> 1)
        ))

class CodeCanvas(CanvasDnD):
    def __init__(self, *a, **kw):
        CanvasDnD.__init__(self, *a, *kw)
        self.__b1_down = None

        # operator addition
        self.__ops_shown = False
        self.__ops_ids = []
        self.__op_circle = None
        self.__op_hl_idx = None

        self.id2wgt = {}

        self.canvas.bind("<Double-Button-1>", self.on_double_button_1, "+")

    def on_double_button_1(self, event):
        c = self.canvas

        ex, ey = event.x, event.y
        x, y = c.canvasx(ex), c.canvasy(ey)

        touched = c.find_overlapping(x - 1, y - 1, x + 1, y + 1)
        i2w = self.id2wgt

        for i in touched:
            if i not in i2w:
                continue

            wgt = i2w[i]

            if isinstance(wgt, ConstWgt):
                move_centred(ConstEdit(wgt, self),
                    c.winfo_rootx() + ex,
                    c.winfo_rooty() + ey,
                    w = 200
                )
                break

    # overrides
    def down(self, event):
        CanvasDnD.down(self, event)

        if self.dragging:
            return

        x, y = event.x, event.y
        self.__b1_down = (x, y)

        self.show_ops(x, y)

    def up(self, event):
        hl_idx = self.__op_hl_idx
        if hl_idx is not None:
            cls = SHORTCUTS[hl_idx]
            if cls is Const:
                wgt = ConstWgt()
            else:
                wgt = OpWgt(cls)

            wgt.init(self, *self.__b1_down)

            i2w = self.id2wgt
            for i in wgt.ids():
                i2w[i] = wgt

        self.hide_ops()

        self.__b1_down = None
        CanvasDnD.up(self, event)

    def motion(self, event):
        CanvasDnD.motion(self, event)

        if self.dragging:
            return

        if self.__ops_shown:
            x, y = event.x, event.y
            dx, dy = x - self.__b1_down[0], y - self.__b1_down[1]

            r2 = dx ** 2 + dy ** 2
            if OP_HL_THRESHOLD_1 < r2 and r2 < OP_HL_THRESHOLD_2:
                a = atan2(dy, dx)

                idx = bisect_left(self.__op_segments, a)
                idx %= len(SHORTCUTS)
                self.__op_hl_idx = idx

                # print(SHORTCUTS[idx].__name__)

                op_a = self.__op_segments[idx] - self.__op_step / 2
                op_x, op_y = (
                    self.__b1_down[0] + OP_CIRCLE_R * cos(op_a),
                    self.__b1_down[1] + OP_CIRCLE_R * sin(op_a)
                )

                oval = (
                    op_x - OP_HL_CIRCLE_R, op_y - OP_HL_CIRCLE_R,
                    op_x + OP_HL_CIRCLE_R, op_y + OP_HL_CIRCLE_R
                )

                cnv = self.canvas

                circ = self.__op_circle
                if circ is None:
                    circ = cnv.create_oval(oval)
                    self.__op_circle = circ
                else:
                    cnv.coords(circ, oval)
            else:
                self.__hide_op_hl()

    def __hide_op_hl(self):
        "hides operator selection highlighting"
        circ = self.__op_circle
        if circ is not None:
            self.canvas.delete(circ)
            self.__op_circle = None
            self.__op_hl_idx = None

    def show_ops(self, x, y):
        if self.__ops_shown:
            return

        self.__ops_shown = True

        cnv = self.canvas
        ids = self.__ops_ids

        step = 2.0 * pi / len(SHORTCUTS)
        a = -pi

        # for user selection identification
        seg = a + step / 2
        op_segments = []
        for op in SHORTCUTS:
            ids.append(
                cnv.create_text(
                    (x + OP_CIRCLE_R * cos(a), y + OP_CIRCLE_R * sin(a)),
                    text = op.ico
                )
            )
            op_segments.append(seg)
            a += step
            seg += step

        self.__op_step = step
        self.__op_segments = op_segments

    def hide_ops(self):
        if self.__ops_shown:
            self.__ops_shown = False

            cnv = self.canvas
            for _id in self.__ops_ids:
                cnv.delete(_id)
            self.__ops_ids.clear()

            self.__hide_op_hl()

if __name__ == "__main__":
    root = VarTk()
    root.grid()
    root.rowconfigure(0, weight = 1)
    root.columnconfigure(0, weight = 1)

    dnd_cnv = CodeCanvas(root)
    dnd_cnv.grid(row = 0, column = 0, sticky = "NESW")

    root.geometry("800x800+400+400")

    root.mainloop()
