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


def main():
    # module generation is based on
    # https://docs.python.org/3/extending/extending.html

    add_base_types()

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
            args = (Pointer(Type["struct PyModuleDef"])("def"))
        )
    ])

    # cache
    pyobjptr = Pointer(Type["PyObject"])
    NULL = Type["NULL"]

    # actual sandbox
    sandbox_c = Source("sandbox.c", locked = False)
    sandbox_c.add_types([
        Function(
            name = "sandbox_run",
            body = BodyTree()(
                Call("printf", "Hello from sandbox!\\n"),
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
    paths = []
    # TODO: outline this
    for m in modules:
        f = m.generate()
        with open(m.path, "w") as writer:
            f.generate(writer)
        paths.append(m.path)

    # Building sandbox

    build_dir = join(dirname(__file__), "sandbox_build")
    build_tmp = mkdtemp()

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
