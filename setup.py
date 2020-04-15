import setuptools

include_dirs = [
    'include',
    'include/traceevent',
    'include/trace-cmd',
    'include/tracefs',
    'lib/traceevent/include',
    'lib/trace-cmd/include',
    'lib/tracefs/include',
    'tracecmd/include',
]

ctracecmd = setuptools.Extension(
    'ctracecmd',
    ['python/ctracecmd.i'],
    swig_opts=[
        '-Wall',
        # '-modern', # ???
        '-noproxy',
        '-I./include/traceevent',
        '-I./include/trace-cmd',
    ],
    include_dirs=include_dirs,
    libraries=[
        './lib/trace-cmd/libtracecmd.a',
        './lib/tracefs/libtracefs.a',
        './lib/traceevent/libtraceevent.a',
        'tracecmd',
        'traceevent',
        'tracefs',
        'rt',
    ],
    library_dirs=[
        './lib/trace-cmd',
        './lib/traceevent',
        './lib/tracefs',
    ]
)

setuptools.setup(
    name="tracecmd",
    packages=['tracecmd'],
    package_dir={'tracecmd': 'python'},
    ext_modules=[ctracecmd],
    python_requires='>=3.7',
)
