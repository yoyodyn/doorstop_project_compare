"""
    project publish will try to publish all the documents into a single page
    The OVR (overview) document will have special purpose as a header and 
    project overview.
"""
import os
import shutil
import doorstop
from doorstop.core.types import is_item, is_tree, iter_documents, iter_items, is_document

# Could define some part of the document config that flags these, but we'll hard code for now
OVERVIEW_DOCUMENT = 'OVR'

def publish_project(obj, project_name, path):
    """method to publish a project which is the difference between two branches in doorstop
    requirements.
    A project will have different publishing requirements.  We don't want to split up all 
    the documents into separate pages, we should be able to get everything into a single 
    html page.
    
    :param obj: the tree where the requirements are stored
    :param project_name: the name of the project.  This should match the branch name, and the name
                         of the overview document item
    :param path: the local folder to publish the files to.
    
    Currently only html will be supported.

    The overview document is currently hard coded.  But we could base this on some attribute of the 
    document configiration "yml" instead
    
    1. generate the html for the overview document item for this project.
    2. generate the html for each of the other document types with changes for this project.
    3. any table changes should be generated last.

    This is a different way to publish the requirements from doorstop, so we can't just override the
    line generation methods
    """
    if not is_tree(obj):
        return

    ovr_document = obj.find_document(OVERVIEW_DOCUMENT)
    project_ovr = None

    for item in iter_items(ovr_document):
        if item.uid.name in project_name:
            project_ovr = item
            break

    if publish_path == None:
        publish_path = "public"

    ovr_lines = publish_lines(project_ovr, ".html")

    # first delete the temp path if it exists
    if os.path.isdir(publish_path):
        shutil.rmtree(publish_path)

    # publish_filename = os.path.join(publish_path, "".join([document_name, ".html"]))
    # doorstop.publisher.publish(tab_document, publish_filename, ".html", toc=False)

PUBLISH_GENERATORS = {
    "REQ" : _lines_requirements,
    "OVR" : _lines_overview,
    "TAB" : _lines_tables,
}

def get_generator(obj, ext):
    """find the lines generator for the obj type"""
    if not is_document(obj):
        return None

    doc_types = ", ".join(doc for doc in PUBLISH_GENERATORS)
    msg = "Unknown document type: {} (options: {})".format(obj.prefix, doc_types)
    exc = doorstop.DoorstopError(msg)

    try:
        gen = PUBLISH_GENERATORS[obj.prefix]
    except KeyError:
        raise exc from None

    return gen

def publish_lines(obj, ext='.txt', **kwargs):
    """method to return the lines for various document types"""
    gen = get_generator(obj, ext)
    yield from gen(obj, **kwargs)

tree = doorstop.build()
publish_project(tree, 'ProjA', 'public')