TBVaccine
---------

.. image:: https://www.codeshelter.co/static/badges/badge-flat.svg
    :target: https://www.codeshelter.co
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

TBVaccine is a utility that pretty-prints Python tracebacks. It automatically
highlights lines you care about and deemphasizes lines you don't, and colorizes
the various elements in a traceback to make it easier to parse.

Here are some screenshots. This is the before:

.. image:: misc/before.png

And this is the after:

.. image:: misc/after.png

If you add the hook or call TBVaccine in your code, it can also print all
variables in each stack frame. That is, it turns this:

.. image:: misc/before-vars.png

into this:

.. image:: misc/after-vars.png


Installation
============

To install, use ``pip``::

    pip install tbvaccine

You are done!


Global usage
============

You can have TBVaccine insert itself all up in your system and stick its tentacles in
all your libraries, like a cute, useful Cthulhu. That way, every single Python
traceback in your system will be pretty. Just set the `TBVACCINE` environment
variable to 1, and you're done.

E.g. for bash::

    export TBVACCINE=1

Or fish::

    set -x TBVACCINE=1

If you want to prettify tracebacks even when stderr is not a tty, set
`TBVACCINE_FORCE` to 1::

    export TBVACCINE=1
    export TBVACCINE_FORCE=1
    python -c '1/0' 2>&1 | cat  # pretty!

NOTE: If you're on Ubuntu, you most likely have Apport installed, which overrides
TBVaccine's hook with its own. To disable Apport for Python, delete a file named
``/etc/python<version>/sitecustomize.py``. Note that this will disable Apport for
Python, and you won't be asked to submit info to Ubuntu when Python programs crash
any more. For some, this is a good thing.


Usage as a command-line utility
===============================

TBVaccine can be used from the command line several ways.::

    python -m tbvaccine myscript.py

Or just pipe STDERR into it from the program you want to watch::

    ./myscript.py 2>&1 | tbvaccine

And all the tracebacks will now be pretty!


Usage as a Python library
=========================

There are various ways to use TBVaccine as a Python library.

Initialize it like so::

    from tbvaccine import TBVaccine
    tbv = TBVaccine(
        code_dir="/my/code/dir",
        isolate=True
    )

``code_dir`` marks the directory we code about. Files under that directory that
appear in the traceback will be highlighted. If not passed, the current
directory, as returned by ``os.getcwd()`` will be used.

If ``isolate`` is ``False``, all lines are colorized, and ``code_dir`` is
ignored.

If ``show_vars`` is ``False``, variables will not be printed in each stack
frame.

To use it in an ``except`` block::

    from tbvaccine import TBVaccine
    try:
        some_stuff()
    except:
        print(TBVaccine().format_exc())


To make it the default way of printing tracebacks, use ``add_hook()`` (which
also accepts any argument the ``TBVaccine`` class does)::

    import tbvaccine
    tbvaccine.add_hook(isolate=False)

    1 / 0

Bam! Instant pretty tracebacks.


Logging integration
===================

You can integrate TBVaccine with logging like so::

    class TbVaccineFormatter(logging.Formatter):
        def  formatException(self, exc_info):
            return TBVaccine(isolate=True).format_exc()

    sh = logging.StreamHandler()
    sh.setFormatter(TbVaccineFormatter('[%(levelname)s] %(asctime)s : %(message)s', '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(sh)


Configuration
=============

To configure TBVaccine, open its configuration file in ``~/.config/tbvaccine/tbvaccine.cfg`` (or your
operating system's equivalent) and edit it. You can currently configure the color style there by
specifying one of the `Pygments styles <http://pygments.org/demo/6778888/?style=monokai>`.


Epilogue
========

This library is still pretty new, please contribute patches if something doesn't
work as intended, and also please tell your friends about it! Hopefully one day
it will be implemented in the Python interpreters themselves.

-- Stavros
