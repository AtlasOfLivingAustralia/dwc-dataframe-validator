# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import dwc_validator

# add path for dwc_validator
sys.path.insert(0,"../../dwc_validator/")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# basic author, project and copyright information
project = 'dwc_validator'
copyright = '2024, Dave Martin, Amanda Buyan'
author = 'Dave Martin, Amanda Buyan'

# versions
version = str(dwc_validator.__version__)
release = version
source_path = os.path.dirname(os.path.abspath(__file__))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser',
              'sphinx-prompt',
              'sphinxcontrib.programoutput',
              'sphinx.ext.napoleon',
              'sphinx.ext.autosectionlabel',]

templates_path = ['_templates']
exclude_patterns = []

autosectionlabel_prefix_document = True

myst_enable_extensions = ["colon_fence"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
