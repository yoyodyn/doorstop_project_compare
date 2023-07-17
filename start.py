"""Script file as a starting point to get the diff from two branches in the requirements repo 
    and try to publish a set of project specifications."""

import subprocess
import os
import shutil
import io
import logging
import doorstop
import frontmatter

from unidiff import PatchSet

logging.basicConfig(filename='startfile.log', filemode='w', level=1)

logger = logging.getLogger
log = logger(__name__)

PIPE = subprocess.PIPE
mainbranch = 'master'               # eventually the branch names should be parameters
projectbranch = 'project/ProjA'

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

# Printing the current working directory
log.info("The Current working directory is: {0}".format(os.getcwd()))

# should not have to change the working directory once deployed as this should be run
# from the requirements repo folder
# Changing the current working directory
os.chdir('C:\\Projects\\QMSI\\RequirementsManagement\\req_test')

# Print the current working directory
log.info("The Current working directory now is: {0}".format(os.getcwd()))

# place to put the files for generating the alternate project requirement "documents"
# This could also be a passed in parameter with a default to the branch name
tempPath = projectbranch.replace('/', '_')

# first delete the temp path if it exists
if os.path.isdir(tempPath):
    shutil.rmtree(tempPath)
# create the temp folder
os.makedirs(tempPath)

# get the diff between the two branches.  Save the output.
# git diff --no-prefix -U100 master project/ProjA 
process = subprocess.Popen(['git', 'diff', '--no-prefix', '-U10000', mainbranch, projectbranch],
                           stdout=PIPE, stderr=PIPE)
stdoutput, stderroutput = process.communicate()

# if 'fatal' in str:
#     # Handle error case
#     print("failed")
#     print(stderroutput)
#     exit()

# using PatchSet to parse the diff output easily
patch_set = PatchSet(io.BytesIO(stdoutput), encoding='utf-8')

# markup lines that have been removed
REMOVED_LINE = "  <span style=\"color:red\"><del>{0}</del></span>\r\n"
ADDED_LINE = "  <span style=\"color:blue\">{0}</span>\r\n"

docList = []

for patched_file in patch_set:
    currentItem = []
    file_path = patched_file.path  # file name
    file_name = os.path.basename(file_path)
    name, file_ext = os.path.splitext(file_name)

    log.info("file name : %s", file_path)

    item_format = DEFAULT_ITEMFORMAT

    # Ensure the file extension is valid, dev version of doorstop has EXTENSTIONS as a dictionary.
    # trying to make this compatible for both.  Explains why the DEFAULT wasn't available.
    found_ext = False
    if isinstance(doorstop.Item.EXTENSIONS, dict):
        for f, exts in doorstop.Item.EXTENSIONS.items():
            if file_ext.lower() in exts:
                found_ext = True
                item_format = f
                break
    else:
        for f in doorstop.Item.EXTENSIONS:
            if file_ext.lower() in f:
                found_ext = True
                break
    if not found_ext:
        msg = f"'{file_path}' extension for itemformat {file_ext} not valid"
        raise doorstop.DoorstopError(msg)

    # check if we need to copy the .doorstop.yml file over to the temp location
    docPath = os.path.dirname(file_path)
    tempDocPath = os.path.join(tempPath, docPath)

    # skipping a folder is apparently a problem,
    # so we need to account for intermediate documents that won't include any changes
    def check_folders(path, path_list):
        """recusrivly checks for and adds temp folders for the project comparison
            Will also add intermediate folders for documents with no changes"""
        folders = os.path.split(path)

        if folders[0] != '' and folders[0] not in path_list:
            check_folders(folders[0], path_list)

        checkDocPath = os.path.join(tempPath, path)
        tempDocConfig = os.path.join(checkDocPath, ".doorstop.yml")
        if not os.path.exists(checkDocPath):
            os.makedirs(checkDocPath, exist_ok=True)
        if not os.path.isfile(tempDocConfig):
            shutil.copy(os.path.join(path, ".doorstop.yml"), tempDocConfig)

    check_folders(docPath, docList)

    normative_change = False
    delimiter_count = 0
    if item_format == ITEM_FORMAT_MARKDOWN:
        handler = frontmatter.YAMLHandler()

    current_field = ''
    normativeField = False

    # we should have included enough context lines that there is only one hunk per file
    for hunk in patched_file:
        for line in hunk:
            # normal parsers to tell.  So will just have to use the delimiters manually.
            if item_format == ITEM_FORMAT_MARKDOWN:
                if handler.FM_BOUNDARY.search(line.value):
                    if line.is_added or line.is_context:
                        currentItem.append(line.value)
                        delimiter_count += 1
                        continue

            # only want to check the field name when in the yaml section
            # this should allow for multi-line field values
            if item_format == ITEM_FORMAT_YAML or delimiter_count == 1:
                if not line.value.startswith(" "):
                    field, value = line.value.split(':', 2)
                    if field != current_field:
                        current_field = field
                        normativeField = field not in NON_NORMATIVE_FIELDS

            # declare a normative change so the file gets added to the document/tree
            # potential problem with MD files here as the header will be included if there is one
            if normativeField or delimiter_count >= 2:
                if line.is_removed or line.is_added:
                    normative_change = True
            
            # we only want to decorate the added and removed lines in the text section
            if (current_field == "text" and line.value.startswith(" ")) or delimiter_count >= 2:
                if line.is_removed:
                    currentItem.append(REMOVED_LINE.format(line.value.strip()))
                elif line.is_added:
                    currentItem.append(ADDED_LINE.format(line.value.strip()))
                else:
                    currentItem.append(line.value)
                continue

            # do not add removed lines from the other fields
            if line.is_added or line.is_context:
                currentItem.append(line.value)

    # working on checking to make sure the normative parts of the file have changed
    # before adding the file to the project folder.
    # need to be able to load yaml and md files here.
    # Plus will the parsing we are doing in the loop above work with MD files and yaml front matter?
    if normative_change:
        if item_format == ITEM_FORMAT_YAML:
            whatisThis = doorstop.common.load_yaml(''.join(currentItem), '')
        elif item_format == ITEM_FORMAT_MARKDOWN:
            whatisThis = doorstop.common.load_markdown(''.join(currentItem), '',
                                                       doorstop.Item.MARKDOWN_TEXT_ATTRIBUTES)
        doorstop.common.write_lines(currentItem, os.path.join(tempDocPath, file_name), "")
        if docPath not in docList:
            docList.append(docPath)

documents = []

# need to get all the "documents" added.  Can we build the tree manually?
def add_docs(doc_path):
    """Recursive method to check and add the document to the list, 
        including any missing document levels"""
    folders = os.path.split(doc_path)
    if folders[0] != '' and folders[0] not in docList:
        add_docs(folders[0])

    document = doorstop.Document(os.path.join(os.path.abspath(tempPath), doc_path), None)
    documents.append(document)

for d in docList:
    add_docs(d)

tree = doorstop.Tree.from_list(documents, None)

# Create the output path only.
publish_folder = os.path.join(tempPath, "public")
if os.path.isdir(publish_folder):
    shutil.rmtree(publish_folder)
if not os.path.exists(publish_folder):
    os.makedirs(publish_folder, exist_ok=True)

#doorstop.publisher.publish(document, "public_Project/req.html", ".html", toc=False)
doorstop.publisher.publish(tree, publish_folder, ".html", toc=False)
