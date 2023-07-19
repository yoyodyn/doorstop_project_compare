"""Building main to eventually be used as the primary command line interface"""

import argparse
import os
import shutil
import doorstop
import frontmatter

from common import logger, DEFAULT_ITEMFORMAT, ITEM_FORMAT_MARKDOWN, ITEM_FORMAT_YAML, NON_NORMATIVE_FIELDS, REMOVED_LINE, ADDED_LINE
from vcs_common import _check_active_branch, _check_branch_fastforward, _read_branch_diff
from publish_project import publish_project

log = logger(__name__)

def main(args=None):
    """Process command line arguments and run the program"""
    # Shared options
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("main", help="Main branch")
    parser.add_argument("project", help="Project branch")

    # Parse arguments
    args = vars(parser.parse_args(args=args))

    mainbranch = args["main"]
    projectbranch = args["project"]

    # Printing the current working directory
    log.info("The Current working directory is: %s", os.getcwd())

    _check_active_branch(projectbranch)
    _check_branch_fastforward(mainbranch, projectbranch)
    patch_set = _read_branch_diff(mainbranch, projectbranch)

    # place to put the files for generating the alternate project requirement "documents"
    # This could also be a passed in parameter with a default to the branch name
    temp_path = projectbranch.replace('/', '_')

    # first delete the temp path if it exists
    if os.path.isdir(temp_path):
        shutil.rmtree(temp_path)
    # create the temp folder
    os.makedirs(temp_path)

    doc_list = _process_diff(patch_set, temp_path)

    documents = []

    # need to get all the "documents" added.  Can we build the tree manually?
    def add_docs(doc_path):
        """Recursive method to check and add the document to the list, 
            including any missing document levels"""
        folders = os.path.split(doc_path)
        if folders[0] != '' and folders[0] not in doc_list:
            add_docs(folders[0])

        document = doorstop.Document(os.path.join(os.path.abspath(temp_path), doc_path), None)
        documents.append(document)

    for doc in doc_list:
        add_docs(doc)

    tree = doorstop.Tree.from_list(documents, None)

    # Create the output path only.
    publish_folder = os.path.join(temp_path, "public")
    if os.path.isdir(publish_folder):
        shutil.rmtree(publish_folder)
    if not os.path.exists(publish_folder):
        os.makedirs(publish_folder, exist_ok=True)

    # doorstop.publisher.publish(tree, publish_folder, ".html", toc=False)
    publish_project(tree, projectbranch, publish_folder)

def _process_diff(patch_set, temp_path):
    doc_list = []

    for patched_file in patch_set:
        current_item = []
        file_path = patched_file.path  # file name
        file_name = os.path.basename(file_path)
        _, file_ext = os.path.splitext(file_name)

        log.info("file name : %s", file_path)

        item_format = DEFAULT_ITEMFORMAT

        # Ensure the file extension is valid,
        # dev version of doorstop has EXTENSTIONS as a dictionary.
        # trying to make this compatible for both.  Explains why the DEFAULT wasn't available.
        found_ext = False
        if isinstance(doorstop.Item.EXTENSIONS, dict):
            for accepted_format, exts in doorstop.Item.EXTENSIONS.items():
                if file_ext.lower() in exts:
                    found_ext = True
                    item_format = accepted_format
                    break
        else:
            for exts in doorstop.Item.EXTENSIONS:
                if file_ext.lower() in exts:
                    found_ext = True
                    break
        if not found_ext:
            msg = f"'{file_path}' extension for itemformat {file_ext} not valid"
            raise doorstop.DoorstopError(msg)

        # check if we need to copy the .doorstop.yml file over to the temp location
        doc_path = os.path.dirname(file_path)
        temp_doc_path = os.path.join(temp_path, doc_path)

        # skipping a folder is apparently a problem,
        # so we need to account for intermediate documents that won't include any changes
        def check_folders(path, path_list):
            """recusrivly checks for and adds temp folders for the project comparison
                Will also add intermediate folders for documents with no changes"""
            folders = os.path.split(path)

            if folders[0] != '' and folders[0] not in path_list:
                check_folders(folders[0], path_list)

            check_doc_path = os.path.join(temp_path, path)
            temp_doc_config = os.path.join(check_doc_path, ".doorstop.yml")
            if not os.path.exists(check_doc_path):
                os.makedirs(check_doc_path, exist_ok=True)
            if not os.path.isfile(temp_doc_config):
                shutil.copy(os.path.join(path, ".doorstop.yml"), temp_doc_config)

        check_folders(doc_path, doc_list)

        normative_change = False
        delimiter_count = 0
        if item_format == ITEM_FORMAT_MARKDOWN:
            handler = frontmatter.YAMLHandler()

        current_field = ''
        normative_field = False

        # we should have included enough context lines that there is only one hunk per file
        for hunk in patched_file:
            for line in hunk:
                # normal parsers to tell.  So will just have to use the delimiters manually.
                if item_format == ITEM_FORMAT_MARKDOWN:
                    if handler.FM_BOUNDARY.search(line.value):
                        if line.is_added or line.is_context:
                            current_item.append(line.value)
                            delimiter_count += 1
                            continue

                # only want to check the field name when in the yaml section
                # this should allow for multi-line field values
                if item_format == ITEM_FORMAT_YAML or delimiter_count == 1:
                    if not line.value.startswith(" "):
                        field, _ = line.value.split(':', 2)
                        if field != current_field:
                            current_field = field
                            normative_field = field not in NON_NORMATIVE_FIELDS

                # declare a normative change so the file gets added to the document/tree
                # potential problem with MD files here as the header will be included
                # if there is one
                if normative_field or delimiter_count >= 2:
                    if line.is_removed or line.is_added:
                        normative_change = True

                # we only want to decorate the added and removed lines in the text section
                if (current_field == "text" and line.value.startswith(" ")) or delimiter_count >= 2:
                    if line.is_removed:
                        current_item.append(REMOVED_LINE.format(line.value.strip()))
                    elif line.is_added:
                        current_item.append(ADDED_LINE.format(line.value.strip()))
                    else:
                        current_item.append(line.value)
                    continue

                # do not add removed lines from the other fields
                if line.is_added or line.is_context:
                    current_item.append(line.value)

        # working on checking to make sure the normative parts of the file have changed
        # before adding the file to the project folder.
        # need to be able to load yaml and md files here.
        # Plus will the parsing we are doing in the loop above work
        # with MD files and yaml front matter?
        if normative_change:
            if item_format == ITEM_FORMAT_YAML:
                whatisThis = doorstop.common.load_yaml(''.join(current_item), '')
            elif item_format == ITEM_FORMAT_MARKDOWN:
                whatisThis = doorstop.common.load_markdown(''.join(current_item), '',
                                                        doorstop.Item.MARKDOWN_TEXT_ATTRIBUTES)
            doorstop.common.write_lines(current_item, os.path.join(temp_doc_path, file_name), "")
            if doc_path not in doc_list:
                doc_list.append(doc_path)
    return doc_list


if __name__ == "__main__":
    main()
