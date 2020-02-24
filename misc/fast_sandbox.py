from setuptools import (
    Distribution,
    Extension
)
import os
from copy import (
    deepcopy
)
from sys import (
    path as PYTHONPATH
)
from os.path import (
    dirname,
    join
)
from tempfile import (
    mkdtemp
)
from shutil import (
    rmtree
)

# TODO: only used types
from source import *
from common import (
    get_cleaner
)
from subprocess import (
    Popen
)


def main():
    add_base_types()

    misc_dir = dirname(__file__)
    build_dir = join(misc_dir, "sandbox_build")
    build_tmp = mkdtemp()

    # generate payload
    Windows_h = Header("Windows.h", is_global = True)
    Windows_h.add_types([
        Macro("HWND"),
        Macro("LPCTSTR"),
        Macro("UINT"),
        Macro("DWORD"),
        Macro("LPVOID"),
        Macro("HMODULE"),
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messagebox
        Function("MessageBox", # in winuser.h actually
            ret_type = Type["int"],
            args = (
                Type["HWND"]("hWnd"),
                Type["LPCTSTR"]("lpText"),
                Type["LPCTSTR"]("lpCaption"),
                Type["UINT"]("uType")
            )
        )
    ])

    payload_c = Source("payload.c", locked = False)
    payload_c.add_types([
        Function("main",
            ret_type = Type["int"],
            args = [
                Type["int"]("argc"),
                Pointer(Pointer(Type["const char"]))("argv")
            ],
            body = BodyTree()(
                Call("MessageBox",
                    hWnd = 0,
                    lpText = "Hello!",
                    lpCaption = "Payload",
                    uType = 0
                ),
                Return(0),
            )
        )
    ])

    payload_c_path = join(build_dir, payload_c.path)
    payload_exe_path = join(build_dir, "payload.exe")
    testdll_path = join(build_dir, "TestDLL.dll")

    with open(payload_c_path, "w") as writer:
        payload_c.generate().generate(writer)

    print("Start payload building")
    gcc = Popen(["gcc", "-luser32", "-o", payload_exe_path, payload_c_path])
    assert gcc.wait() == 0
    print("Payload built")

    # test executable
    # payload = Popen([payload_exe_path])
    # assert payload.wait() == 0

    # module generation is based on
    # https://docs.python.org/3/extending/extending.html
    Python_h = Header("Python.h", is_global = True)
    # XXX: some types are defined as macros for simplicity but it can be wrong.
    Python_h.add_types([
        Macro("NULL"), # XXX: find right place
        Type("PyObject"),
        Macro("Py_INCREF", ["obj"]),
        Type("PyCFunction"),
        Macro("Py_None"),
        Macro("Py_ssize_t"),
        # see https://docs.python.org/3/c-api/structures.html
        Structure("PyMethodDef",
            Pointer(Type["const char"])("ml_name"),
            Pointer(Type["PyCFunction"])("ml_meth"),
            Type["int"]("ml_flags"),
            Pointer(Type["const char"])("ml_doc"),
        ),
        Structure("struct PyModuleDef",
            Pointer(Type["void"])("m_base"), # XXX: not exactly
            Pointer(Type["const char"])("m_name"),
            Pointer(Type["const char"])("m_doc"),
            Type["Py_ssize_t"]("m_size"),
            Pointer(Type["PyMethodDef"])("m_methods"),
            # TODO: other fields
        ),
        Macro("METH_VARARGS"),
        Macro("PyModuleDef_HEAD_INIT"),
        Macro("PyMODINIT_FUNC"),
        Function("PyModule_Create",
            args = [Pointer(Type["struct PyModuleDef"])("def")]
        )
    ])

    # cache
    pyobjptr = Pointer(Type["PyObject"])
    NULL = Type["NULL"]

    # PE loader
    Loader_h = Header("SimplePELoader/Loader/Loader.h").add_types([
        Function("LOADER_FNVIRTUALALLOC"),
        Function("LOADER_FNVIRTUALFREE"),
        Function("LOADER_FNGETPROCADDRESS"),
        Function("LOADER_FNLOADLIBRARYA"),
        Structure("LOADER_FUNCTION_TABLE",
            Type["LOADER_FNVIRTUALALLOC"]("fnVirtualAlloc"),
            Type["LOADER_FNVIRTUALFREE"]("fnVirtualFree"),
            Type["LOADER_FNGETPROCADDRESS"]("fnGetProcAddress"),
            Type["LOADER_FNLOADLIBRARYA"]("fnLoadLibraryA"),
        ),
        Structure("LOADED_MODULE",
            Pointer(Type["void"])("entry"),
            # TODO: no all fields
        )
    ])
    Loader_h.add_types([
        Function("Loader_LoadFromBuffer",
            ret_type = Type["DWORD"],
            args = (
                Pointer(Type["LOADER_FUNCTION_TABLE"])("pFunTable"), # CONST
                Type["LPVOID"]("pBuffer"), # CONST
                Type["DWORD"]("cbBuffer"),
                Pointer(Type["LOADED_MODULE"])("pResult"),
            )
        )
    ])

    # actual sandbox
    sandbox_c = Source("sandbox.c", locked = False)

    load_and_run = Function("load_and_run",
        args = [Pointer(Type["const char"])("file_name")],
        body = """\
    LOADER_FUNCTION_TABLE funTab = { 0 };

    funTab.fnGetProcAddress = &GetProcAddress;
    funTab.fnLoadLibraryA = &LoadLibraryA;
    funTab.fnVirtualAlloc = &VirtualAlloc;
    funTab.fnVirtualFree = &VirtualFree;

    LOADED_MODULE loadedModule = { 0 };

    FILE *f = fopen(file_name, "rb+");
    if (!f) {
        printf("File opening failed\\n");
        return;
    }
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    printf("File size %lu\\n", fsize);
    if (!fsize) {
        fclose(f);
        return;
    }
    fseek(f, 0, SEEK_SET);
    void *buf = malloc(fsize);
    if (fread(buf, 1, fsize, f) != fsize) {
        free(buf);
        fclose(f);
        printf("fread failed\\n");
        return;
    }
    fclose(f);
    int res = Loader_LoadFromBuffer(&funTab, buf, fsize, &loadedModule);
    printf("loading result %d\\n", res);
    loadedModule.pEntryPoint(loadedModule.hModule, DLL_PROCESS_ATTACH, NULL);
    free(buf);
"""     ,
        used_types = [Type["Loader_LoadFromBuffer"], Type["FILE"]]
    )

    sandbox_c.add_types([
        Function(
            name = "sandbox_run",
            body = BodyTree()(
                Call("printf", "Hello from sandbox!\n"),
                Call(load_and_run, testdll_path), # payload_exe_path),
                MCall("Py_INCREF", "Py_None"),
                Return(Type["Py_None"]),
            ),
            ret_type = pyobjptr,
            args = (pyobjptr("self"), pyobjptr("args")),
            static = True
        ),
        # OpaqueCode("#error test")
    ])
    sandbox_methods = Type["PyMethodDef"]("sandbox_methods",
        array_size = 0,
        static = True,
        initializer = [
            dict(
              ml_name = '"run"',
              ml_meth = Type["sandbox_run"],
              ml_flags = Type["METH_VARARGS"],
              ml_doc = '"Run the sandbox"'
            ),
            [ NULL, NULL, 0, NULL ],
        ]
    )
    sandbox_c.add_global_variable(sandbox_methods)

    sandbox_module = Type["struct PyModuleDef"]("sandbox_module",
        initializer = [Type["PyModuleDef_HEAD_INIT"], '"sandbox"',
            NULL, -1, sandbox_methods
        ],
        static = True
    )

    sandbox_c.add_global_variable(sandbox_module)

    sandbox_c.add_type(Function("PyInit_sandbox",
        ret_type = Type["PyMODINIT_FUNC"],
        body = BodyTree()(
            Return(Call("PyModule_Create", OpAddr(sandbox_module)))
        )
    ))

    modules = [sandbox_c]
    paths = [join(misc_dir, "SimplePELoader", "Loader", "Loader.cpp")]
    # TODO: outline this
    for m in modules:
        f = m.generate()
        m_path = join(build_dir, m.path)
        with open(m_path, "w") as writer:
            f.generate(writer)
        paths.append(m_path)

    # Building sandbox

    # TODO: get_cleaner().rmtree(build_tmp) # for Windows Cleaner does not work

    # hacking setuptools & distutils
    ext = Extension("sandbox", paths)
    dist = Distribution(attrs = dict(
        name = "sandbox",
        ext_modules = [ext]
    ))
    dist.commands = ["build_ext"]
    # see `Distribution._set_command_options`
    dist.command_options["build_ext"] = dict(
        # see distutils.command.build_ext
        build_lib = (
            __file__, # source of option
            build_dir
        ),
        build_temp = (
            __file__,
            build_tmp
        ),
        include_dirs = (
            __file__,
            [misc_dir]
        )
    )

    # comment from weave.build_tools.build_extension
    # distutils for MSVC messes with the environment, so we save the
    # current state and restore them afterward.
    environ_back = deepcopy(os.environ)

    try:
        # TODO: this fails under PyDev debugging under Windows
        dist.run_commands()
    except:
        raise
    finally:
        os.environ = environ_back
        rmtree(build_tmp)

    PYTHONPATH.insert(0, build_dir)

    import sandbox

    sandbox.run()

if __name__ == "__main__":
    exit(main() or 0)
