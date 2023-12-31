# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os
sys.path.append(os.path.abspath('../../src/'))

project = 'atompy'
copyright = 'Max Kircher, CC BY-NC 4.0'
author = 'Max Kircher'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "numpydoc",
    "sphinx.ext.viewcode",
]
autodoc_type_aliases = {
    'ArrayLike': 'ArrayLike',
}
autodoc_typehints = "none"
numpydoc_class_members_toctree = False

templates_path = ['_templates']
exclude_patterns = []

html_theme_options = {
    "show_nav_level": 4,
    "navigation_depth": 4,
    "collapse_navigation": False
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
