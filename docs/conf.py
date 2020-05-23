import os

here = os.path.dirname(__file__)
top_level = os.path.dirname(here)

# -- General configuration -----------------------------------------------------

project = "pyramid_restler"
version = "2.0a1"  # Short version
release = version  # Full version
author_name = "Wyatt Baldwin"
author_email = "self@wyattbaldwin.com"
copyright = f"2011, 2018, 2020, {author_name} <{author_email}>"
github_username = "wylee"
github_url = f"https://github.com/{github_username}/{project}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]

source_suffix = ".rst"

master_doc = "index"

today_fmt = "%B %d, %Y"

exclude_patterns = ["_build"]

pygments_style = "sphinx"

# reStructuredText options ------------------------------------------------

# This makes `xyz` the same as ``xyz``.
default_role = "literal"

# This is appended to the bottom of all docs.
rst_epilog = """
.. |project| replace:: {project}
.. |github_url| replace:: {github_url}
""".format_map(
    locals()
)

# Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.6", None),
}

# -- Options for HTML output -------------------------------------------

html_theme = "alabaster"

html_theme_options = {
    "description": "Resourceful routes & views for Pyramid",
    "github_user": github_username,
    "github_repo": project,
    "page_width": "1200px",
    "fixed_sidebar": True,
    "sidebar_width": "300px",
    "extra_nav_links": {"Source (GitHub)": github_url,},
}

html_sidebars = {"**": ["about.html", "navigation.html", "searchbox.html",]}

html_static_path = []

html_last_updated_fmt = "%b %d, %Y"

# Output file base name for HTML help builder.
htmlhelp_basename = f"{project}doc"


# -- Options for LaTeX output ------------------------------------------

latex_documents = [
    (
        "index",
        f"{project}.tex",
        "pyramid\\_restler Documentation",
        author_name,
        "manual",
    ),
]

# -- Options for manual page output ------------------------------------

man_pages = [("index", project, f"{project} Documentation", [author_name], 1,)]
