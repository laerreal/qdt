#!/usr/bin/python2

from examples import \
    Q35Project_2_6_0, \
    Q35MachineNode_2_6_0

from widgets import \
    HistoryWindow, \
    askopen, \
    asksaveas, \
    AddDescriptionDialog, \
    __dict__ as widgets_dict, \
    GUIProject, \
    HotKeyBinding, \
    HotKey, \
    ProjectWidget, \
    VarMenu, \
    GUITk

import argparse

from qemu_device_creator import \
    arg_type_directory

import cPickle
import qemu

from common import \
    PyGenerator, \
    mlget as _

from Tkinter import \
    BooleanVar, \
    StringVar

from tkMessageBox import \
    askyesno, \
    showerror

class QDCGUIWindow(GUITk):
    def __init__(self, project = None):
        GUITk.__init__(self, wait_msec = 1)

        self.title_suffix = _("Qemu device creator GUI")
        self.title_suffix.trace_variable("w", self.__on_title_suffix_write__)

        self.title_not_saved_asterisk = StringVar()
        self.title_not_saved_asterisk.trace_variable("w",
            self.__on_title_suffix_write__)
        self.saved_operation = None

        self.var_title = StringVar()
        self.title(self.var_title)

        # Hot keys, accelerators
        self.hk = hotkeys = HotKey(self)
        hotkeys.add_bindings([
            HotKeyBinding(
                self.invert_history_window,
                key_code = 43, # H
                description = _("If operation history window is hidden then \
show it else hide it.")
            ),
            HotKeyBinding(
                self.on_load,
                key_code = 32, # O
                description = _("Load project from file.")
            ),
            HotKeyBinding(
                self.on_new_project,
                key_code = 57, # N
                description = _("Create new project.")
            ),
            HotKeyBinding(
                self.on_add_description,
                key_code = 40, # D
                description = _("Add description to the project")
            ),
            HotKeyBinding(
                self.on_delete,
                key_code = 24, # Q
                description = _("Shutdown the application.")
            ),
            HotKeyBinding(
                self.undo,
                key_code = 52, # Z
                description = _("Revert previous editing.")
            ),
            HotKeyBinding(
                self.redo,
                key_code = 29, # Y
                description = _("Make reverted editing again.")
            ),
            HotKeyBinding(
                self.on_save,
                key_code = 39, # S
                description = _("Save project.")
            )
        ])

        hotkeys.add_key_symbols({
            43: "H",
            32: "O",
            57: "N",
            40: "D",
            24: "Q",
            52: "Z",
            29: "Y",
            39: "S"
        })

        # Menu bar
        menubar = VarMenu(self)

        filemenu = VarMenu(menubar, tearoff = False)
        filemenu.add_command(
            label = _("Add description"),
            command = self.on_add_description,
            accelerator = hotkeys.get_keycode_string(self.on_add_description)
        )
        filemenu.add_separator()
        filemenu.add_command(
            label = _("New project"),
            command = self.on_new_project,
            accelerator = hotkeys.get_keycode_string(self.on_new_project)
        ),
        filemenu.add_command(
            label = _("Save"),
            command = self.on_save,
            accelerator = hotkeys.get_keycode_string(self.on_save)
        ),
        filemenu.add_command(
            label = _("Save project as..."),
            command = self.on_save_as
        )
        filemenu.add_command(
            label = _("Load"),
            command = self.on_load,
            accelerator = hotkeys.get_keycode_string(self.on_load)
        ),
        filemenu.add_separator()
        filemenu.add_command(
            label=_("Quit"),
            command = self.quit,
            accelerator = hotkeys.get_keycode_string(self.on_delete)
        )
        menubar.add_cascade(label=_("File"), menu = filemenu)

        self.editmenu = editmenu = VarMenu(menubar, tearoff = False)
        editmenu.add_command(
            label = _("Undo"),
            command = self.undo,
            accelerator = hotkeys.get_keycode_string(self.undo)
        )
        self.undo_idx = editmenu.count - 1

        editmenu.add_command(
            label = _("Redo"),
            command = self.redo,
            accelerator = hotkeys.get_keycode_string(self.redo)
        )
        self.redo_idx = editmenu.count - 1

        editmenu.add_separator()

        v = self.var_history_window = BooleanVar()
        v.set(False)

        self.__on_var_history_window = v.trace_variable("w",
            self.__on_var_history_window__
        )

        editmenu.add_checkbutton(
            label = _("Editing history window"),
            variable = v,
            accelerator = hotkeys.get_keycode_string(self.invert_history_window)
        )

        menubar.add_cascade(label = _("Edit"), menu = editmenu)

        self.config(menu = menubar)

        # Widget layout
        self.grid()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.set_project(GUIProject() if project is None else project)

        self.protocol("WM_DELETE_WINDOW", self.on_delete)

        self.__update_title__()
        self.__check_saved_asterisk__()

    def __on_history_window_destroy__(self, *args, **kw):
        self.var_history_window.trace_vdelete("w",
            self.__on_var_history_window
        )

        self.var_history_window.set(False)

        self.__on_var_history_window = self.var_history_window.trace_variable(
            "w", self.__on_var_history_window__
        )

    def __on_var_history_window__(self, *args):
        if self.var_history_window.get():
            self._history_window = HistoryWindow(self.proj.pht, self)
            self._history_window.bind("<Destroy>",
                self.__on_history_window_destroy__, "+"
            )
        else:
            try:
                self._history_window.destroy()
            except AttributeError:
                pass
            else:
                del self._history_window

    def invert_history_window(self):
        self.var_history_window.set(not self.var_history_window.get())

    def __on_title_suffix_write__(self, *args, **kw):
        self.__update_title__()

    def __update_title__(self):
        try:
            title_prefix = str(self.current_file_name)
        except AttributeError:
            title_prefix = "[New project]"

        self.var_title.set(
            title_prefix
                + self.title_not_saved_asterisk.get()
                + " - "
                + self.title_suffix.get()
        )

    def chack_undo_redo(self):
        can_do = self.proj.pht.can_do()

        self.hk.set_enabled(self.redo, can_do)
        if can_do:
            self.editmenu.entryconfig(self.redo_idx, state = "normal")
        else:
            self.editmenu.entryconfig(self.redo_idx, state = "disabled")

        can_undo = self.proj.pht.can_undo()

        self.hk.set_enabled(self.undo, can_undo)
        if can_undo:
            self.editmenu.entryconfig(self.undo_idx, state = "normal")
        else:
            self.editmenu.entryconfig(self.undo_idx, state = "disabled")

    def set_current_file_name(self, file_name = None):
        if file_name is None:
            try:
                del self.current_file_name
            except AttributeError:
                pass
        else:
            self.current_file_name = file_name

        self.__update_title__()

    def set_project(self, project):
        try:
            proj = self.proj
        except AttributeError:
            # Project was never been set
            pass
        else:
            proj.pht.remove_on_changed(self.on_changed)

        try:
            self.pw.destroy()
        except AttributeError:
            # project widget was never been created
            pass

        # Close history window
        if self.var_history_window.get():
            self.var_history_window.set(False)

        self.proj = project

        self.pw = ProjectWidget(self.proj, self)
        self.pw.grid(column = 0, row = 0, sticky = "NEWS")

        self.proj.pht.add_on_changed(self.on_changed)
        self.chack_undo_redo()

    def __saved_asterisk__(self, saved = True):
        if saved:
            if self.title_not_saved_asterisk.get() != "":
                self.title_not_saved_asterisk.set("")
        else:
            if self.title_not_saved_asterisk.get() != "*":
                self.title_not_saved_asterisk.set("*")

    def __check_saved_asterisk__(self):
        if self.saved_operation == self.proj.pht.pos:
            self.__saved_asterisk__(True)
        else:
            self.__saved_asterisk__(False)

    def on_changed(self, *args, **kw):
        self.chack_undo_redo()
        self.__check_saved_asterisk__()

    def undo(self):
        self.pw.undo()

    def redo(self):
        self.pw.redo()

    def on_delete(self):
        self.quit()

    def on_add_description(self):
        d = AddDescriptionDialog(self.proj.pht, self)

    def load_project_from_file(self, file_name):
        loaded_variables = {}
        available_names = dict(qemu.__dict__)
        available_names.update(widgets_dict)

        try:
            execfile(file_name, available_names, loaded_variables)
        except Exception as e:
            raise e
        else:
            for v in loaded_variables.values():
                if isinstance(v, GUIProject):
                    self.set_project(v)
                    self.set_current_file_name(file_name)
                    self.saved_operation = v.pht.pos
                    self.__check_saved_asterisk__()
                    break
            else:
                raise Exception("No GUI project object was loaded")

    def save_project_to_file(self, file_name):
        self.pw.refresh_layouts()
        PyGenerator().serialize(open(file_name, "wb"), self.proj)

        self.set_current_file_name(file_name)
        self.saved_operation = self.proj.pht.pos
        self.__check_saved_asterisk__()

    def try_save_project_to_file(self, file_name):
        try:
            open(file_name, "wb").close()
        except Exception as e:
            try:
                os.delete(file_name)
            except:
                pass

            showerror(
                title = _("Cannot save project").get(),
                message = str(e)
            )
            return

        self.save_project_to_file(file_name)

    def on_save_as(self):
        fname = asksaveas([(_("QDC GUI Project defining script"), ".py")],
            title = _("Save project")
        )

        if not fname:
            return

        self.try_save_project_to_file(fname)

    def on_save(self):
        try:
            fname = self.current_file_name
        except AttributeError:
            self.on_save_as()
        else:
            self.try_save_project_to_file(fname)

    def check_unsaved(self):
        if self.title_not_saved_asterisk.get() == "*":
            return askyesno(
                title = self.title_suffix.get(),
                message =
_("Current project has unsaved changes. They will be lost. Continue?").get()
            )
        else:
            return True

    def on_new_project(self):
        if not self.check_unsaved():
            return

        self.set_project(GUIProject())
        self.set_current_file_name()

        """ There is nothing to save in just created project. So declare that
all changes are saved. """  
        self.saved_operation = self.proj.pht.pos
        self.__check_saved_asterisk__()

    def on_load(self):
        if not self.check_unsaved():
            return

        fname = askopen([(_("QDC GUI Project defining script"), ".py")],
            title = _("Load project")
        )

        if not fname:
            return

        try:
            self.load_project_from_file(fname)
        except Exception as e:
            showerror(
                title = _("Project loading failed").get(),
                message = str(e)
            )

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--qemu-build', '-b',
        default = '.',
        type = arg_type_directory,
        metavar = 'path_to_qemu_build',
        )

    arguments = parser.parse_args()

    qemu.load_build_path_list()
    qemu.account_build_path(arguments.qemu_build)

    try:
        qemu.qvd_load_with_cache(arguments.qemu_build)
    except Exception, e:
        print "QVD load filed: " + str(e) + "\n"

    root = QDCGUIWindow()

    try:
        root.load_project_from_file("project.py")
    except Exception, e:
        print "Project load filed: " + str(e) + "\n"

        project = GUIProject()

        try:
            variables = {}
            execfile("serialize-test.py", qemu.__dict__, variables)
    
            for v in variables.values():
                if isinstance(v, qemu.MachineNode):
                    mach = v
                    break
            else:
                raise Exception(
                    "No MachineNode instance was found in serialize-test.py")
        except Exception, e:
            print "Machine load failed: " + str(e) + "\n"
            mach = Q35MachineNode_2_6_0()

        project.add_description(mach)

        try:
            layout = cPickle.load(open("layout.p", "rb"))
        except Exception, e:
            print "Layout load filed: " + str(e) + "\n"
        else:
            project.layouts.append((mach.name, layout))

        tmp_p = Q35Project_2_6_0()
        for desc in list(tmp_p.descriptions):
            if not isinstance(desc, qemu.MachineNode):
                desc.remove_from_project()
                project.add_description(desc)

        root.set_project(project)
        root.set_current_file_name("project.py")

    root.proj.build_path = arguments.qemu_build

    root.geometry("1000x750")

    root.mainloop()

    root.save_project_to_file("project.py")

if __name__ == '__main__':
    main()