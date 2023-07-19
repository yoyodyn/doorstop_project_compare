"""Common module"""
import logging
import subprocess

logging.basicConfig(filename='startfile.log', filemode='w', level=1)

logger = logging.getLogger
log = logger(__name__)

PIPE = subprocess.PIPE
ITEM_FORMAT_YAML = "yaml"
ITEM_FORMAT_MARKDOWN = "markdown"
DEFAULT_ITEMFORMAT = ITEM_FORMAT_YAML

NON_NORMATIVE_FIELDS = [
    "active",
    "derived",
    "header",
    "level",
    "normative",
    "reviewed"
]

# markup lines that have been added or removed
# REMOVED_LINE = "  <span style=\"color:red\"><del>{0}</del></span>\r\n"
# ADDED_LINE = "  <span style=\"color:blue\">{0}</span>\r\n"
REMOVED_LINE = "  {}\r\n"
ADDED_LINE = "  {}\r\n"
