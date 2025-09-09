Lightweight stand-ins for heavy third-party dependencies used only during
tests.  These modules implement just the tiny portions of the libraries that
our test-suite exercises so the code base stays small and easy to maintain.

``tests/conftest.py`` adds this directory to ``sys.path`` so imports like
``pydantic`` resolve to these simplified versions during testing.  The
application and build process rely on the actual packages from
``site-packages``.
