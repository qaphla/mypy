Revision history
================

List of major changes to this document:

- July 2016
    Publish ``mypy-lang`` version 0.4.3 on PyPI.

    Add :ref:`strict_optional`.

    Add :ref:`multi_line_annotation`.

- June 2016
    Publish ``mypy-lang`` version 0.4.2 on PyPI.

    Add :ref:`type-of-class`.

    Add :ref:`cheat-sheet-py2`.

    Add :ref:`reveal-type`.

- May 2016
    Publish ``mypy-lang`` version 0.4 on PyPI.

    Add :ref:`type-variable-upper-bound`.

    Document :ref:`command-line`.

- Feb 2016
    Publish ``mypy-lang`` version 0.3.1 on PyPI.

    Document Python 2 support.

- Nov 2015
    Add :ref:`library-stubs`.

- Jun 2015
    Remove ``Undefined`` and ``Dynamic``, as they are not in PEP 484.

- Apr 2015
    Publish ``mypy-lang`` version 0.2.0 on PyPI.

- Mar 2015
    Update documentation to reflect PEP 484:

    * Add :ref:`named-tuples` and :ref:`optional`.

    * Do not mention type application syntax (for
      example, ``List[int]()``), as it's no longer supported,
      due to PEP 484 compatibility.

    * Rename ``typevar`` to ``TypeVar``.

    * Document ``# type: ignore`` which allows
      locally ignoring spurious errors (:ref:`silencing_checker`).

    * No longer mention
      ``Any(x)`` as a valid cast, as it will be phased out soon.

    * Mention the new ``.pyi`` stub file extension. Stubs can live
      in the same directory as the rest of the program.

- Jan 2015
    Mypy moves closer to PEP 484:

    * Add :ref:`type-aliases`.

    * Update discussion of overloading -- it's now only supported in stubs.

    * Rename ``Function[...]`` to ``Callable[...]``.

- Dec 2014
    Publish mypy version 0.1.0 on PyPI.

- Oct 2014
    Major restructuring.
    Split the HTML documentation into
    multiple pages.

- Sep 2014
    Migrated docs to Sphinx.

- Aug 2014
    Don't discuss native semantics. There is only Python
    semantics.

- Jul 2013
    Rewrite to use new syntax. Shift focus to discussing
    Python semantics. Add more content, including short discussions of
    :ref:`generic-functions` and :ref:`union-types`.
