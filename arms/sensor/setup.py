from distutils.core import setup, Extension

setup(name="tcp",
      py_modules = ["tcp.py"],
      ext_modules = [
          Extension("_tcp",
                    ["tcp_wrap.c"],
                    include_dirs = [],
                    define_macros = [],
                    undef_macros = [],
                    library_dirs = ["/home/pi/arms/arms/sensor"],
                    libraries = ["tcp"]
                    )
          ]
      )