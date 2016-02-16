from setuptools import setup

PACKAGE = 'periscope'

setup(name = PACKAGE,
      version = 'subsearch',
      license = "GNU LGPL",
      description = "Fork of periscope used for downloading subtitles for given video file(s) from SubHeaven.org or SubFinland.org through Subsearch.org's search engine",
      author = "Oskari Rauta",
      author_email = "oskari.rauta@gmail.com",
      url = "http://code.google.com/p/periscope/",
      packages= [ "periscope", "periscope/plugins" ],
      py_modules=["periscope"],
      install_requires = ["beautifulsoup4"]
      )
