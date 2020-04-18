# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html
project = 'Cloud Optimized Fits'
copyright = '2020, Joe Curtin'
author = 'Joe Curtin'
# The full version, including alpha/beta/rc tags
with open('../VERSION', 'r') as stream:
    release = stream.read()

html_theme = "sphinx_rtd_theme"

master_doc = 'index'
# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


html_static_path = ['_static']
