"""Common module"""
import logging
import subprocess
import re

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

TABLE_FIELDS = [
    "primarykey",
    "typesize",
    "valuelist",
]

# We're going to parse out the code blocks if they exist so we can get complete sections to compare
MARKDOWN_CODE_BLOCK_DELIMITER = "```"
CODE_BLOCK_BOUNDARY = re.compile(r"`{3,}")
CODE_BLOCK_ONE_LINE = re.compile(r"```\w*[^`]+```*")


# markup lines that have been added or removed
REMOVED_LINE = '  <span style="color:red"><del>{0}</del></span>\r\n'
ADDED_LINE = '  <span style="color:blue">{0}</span>\r\n'
# REMOVED_LINE = "  {}\r\n"
# ADDED_LINE = "  {}\r\n"
REMOVED_BLOCK_START = '  <div style="border-left: 5px solid red">\r\n'
ADDED_BLOCK_START = '  <div style="border-left: 5px solid blue">\r\n'
BLOCK_END = '  </div>\r\n'

# Could define some part of the document config that flags these, but we'll hard code for now
OVERVIEW_DOCUMENT = 'OVR'
REQUIREMENTS_DOCUMENT = 'REQ'
TABLES_DOCUMENT = 'TAB'
