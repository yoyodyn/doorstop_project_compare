"""
    project publish will try to publish all the documents into a single page
    The OVR (overview) document will have special purpose as a header and 
    project overview.
"""
import os
#import shutil
import bottle
import doorstop
import markdown

#from itertools import chain
from bottle import template as bottle_template
from doorstop.core.types import is_item, is_tree, iter_documents, iter_items, is_document, Prefix
from common import log, OVERVIEW_DOCUMENT, REQUIREMENTS_DOCUMENT, TABLES_DOCUMENT
from publish_common import (_format_md_ref, _format_md_references, _format_md_links,
                           _format_md_label_links, _format_md_attr_list)
from publish_table import _tab_lines_markdown
#from vcs_common import _check_active_branch, _check_branch_fastforward, _read_branch_diff


def publish_project(obj, project_name, publish_path):
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
    template=doorstop.publisher.HTMLTEMPLATE

    if not is_tree(obj):
        return

    if publish_path == None:
        publish_path = "public"

    doc_lines = {}
    for obj2, path2 in iter_documents(obj, publish_path, ".html"):
        doc_lines[obj2.prefix] = publish_lines(obj2, ".html")

    lines = []
    special_doc_types = [Prefix(OVERVIEW_DOCUMENT), Prefix(REQUIREMENTS_DOCUMENT), 
                         Prefix(TABLES_DOCUMENT)]
    for doc_type in special_doc_types:
        lines.extend(doc_lines[doc_type])

    for prefix, line in doc_lines.items():
        if prefix in special_doc_types:
            continue
        lines.extend(line)

    body = ""
    for it in lines:
        for element in it:
            body += element

    try:
        bottle.TEMPLATE_PATH.insert(
            0, os.path.join(os.path.dirname(__file__), "views"))
        if "baseurl" not in bottle.SimpleTemplate.defaults:
            bottle.SimpleTemplate.defaults["baseurl"] = ""
        html = bottle_template(template, body=body, toc="", parent=obj.parent, document=obj)
    except Exception:
        log.error("Problem parsing the template %s", template)
        raise
    html = html.split(os.linesep)

    doorstop.common.write_lines(html, os.path.join(publish_path, "index.html"), 
                                end=doorstop.settings.WRITE_LINESEPERATOR)

    # take this out for now
    # if obj2.copy_assets(assets_dir):
    #     log.info("Copied assets from %s to %s", obj.assets, assets_dir)

def _req_lines_markdown(obj, **kwargs):
    """Yield lines for a Markdown report.

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks (for conversion to HTML)

    :return: iterator of lines of text

    """
    linkify = kwargs.get("linkify", False)
    to_html = kwargs.get("to_html", False)
    for item in iter_items(obj):
        text_lines = item.text.splitlines()

        if item.heading:
            if item.header:
                text_lines.insert(0, item.header)
            # Level and Text
            standard = "- {t}".format(t=text_lines[0] if text_lines else "")
            attr_list = _format_md_attr_list(item, True)
            yield ""
            yield standard + attr_list
            yield from text_lines[1:]
        else:
            uid = item.uid
            if item.header:
                uid = "- {h} <small>{u}</small>".format(h=item.header, u=item.uid)
            else:
                uid = "- <small>[{u}]</small>".format(u=item.uid)

            # Level and UID
            standard = "{u}".format(u=uid)

            t = text_lines[0] if text_lines else ""

            attr_list = _format_md_attr_list(item, True)
            yield standard + " " + t
            # Text
            if item.text:
                yield from text_lines[1:]
            # Reference
            if item.ref:
                yield ""  # break before reference
                yield _format_md_ref(item)
            # Reference
            if item.references:
                yield ""  # break before reference
                yield _format_md_references(item)
            # Parent links
            if item.links:
                yield ""  # break before links
                items2 = item.parent_items
                label = "Parent links:"
                links = _format_md_links(items2, linkify, to_html=to_html)
                label_links = _format_md_label_links(label, links, linkify)
                yield label_links
            # Child links
            items2 = item.find_child_items()
            if items2:
                yield ""  # break before links
                label = "Child links:"
                links = _format_md_links(items2, linkify, to_html=to_html)
                label_links = _format_md_label_links(label, links, linkify)
                yield label_links
            # Add custom publish attributes
            if item.document and item.document.publish:
                header_printed = False
                for attr in item.document.publish:
                    if not item.attribute(attr):
                        continue
                    if not header_printed:
                        header_printed = True
                        yield ""
                        yield "| Attribute | Value |"
                        yield "| --------- | ----- |"
                    yield "| {} | {} |".format(attr, item.attribute(attr))
                yield ""

def _ovr_lines_markdown(obj, **kwargs):
    """Yield lines for a Markdown report.

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks (for conversion to HTML)

    :return: iterator of lines of text

    """
    linkify = kwargs.get("linkify", False)
    to_html = kwargs.get("to_html", False)
    for item in iter_items(obj):
        text_lines = item.text.splitlines()
        if item.header:
            yield ""
            yield f"##### {item.header}"
            yield ""
        # Text
        if item.text:
            yield from text_lines[0:]
        # Reference
        if item.ref:
            yield ""  # break before reference
            yield _format_md_ref(item)
        # Reference
        if item.references:
            yield ""  # break before reference
            yield _format_md_references(item)
        # Parent links
        if item.links:
            yield ""  # break before links
            items2 = item.parent_items
            label = "Parent links:"
            links = _format_md_links(items2, linkify, to_html=to_html)
            label_links = _format_md_label_links(label, links, linkify)
            yield label_links
        # Child links
        items2 = item.find_child_items()
        if items2:
            yield ""  # break before links
            label = "Child links:"
            links = _format_md_links(items2, linkify, to_html=to_html)
            label_links = _format_md_label_links(label, links, linkify)
            yield label_links
        # Add custom publish attributes
        if item.document and item.document.publish:
            header_printed = False
            for attr in item.document.publish:
                if not item.attribute(attr):
                    continue
                if not header_printed:
                    header_printed = True
                    yield ""
                    yield "| Attribute | Value |"
                    yield "| --------- | ----- |"
                yield "| {} | {} |".format(attr, item.attribute(attr))
            yield ""

def _lines_overview(obj):
    # Determine if a full HTML document should be generated
    extensions=doorstop.publisher.EXTENSIONS

    text = "\n".join(_ovr_lines_markdown(obj, linkify=False, to_html=True))
    if len(text) > 0:
        text = "### Overview\n" + text
    body = markdown.markdown(text, extensions=extensions)

    yield body

def _lines_requirements(obj):
    extensions=doorstop.publisher.EXTENSIONS

    text = "\n".join(_req_lines_markdown(obj, linkify=False, to_html=True))
    if len(text) > 0:
        text = "### Requirements Changes\n" + text
    body = markdown.markdown(text, extensions=extensions)
    yield body

def _lines_tables(obj):
    extensions=doorstop.publisher.EXTENSIONS

    text = "\n".join(_tab_lines_markdown(obj, linkify=False, to_html=True))
    if len(text) > 0:
        text = "### Table Changes\n" + text
    body = markdown.markdown(text, extensions=extensions)
    yield body

PUBLISH_GENERATORS = {
    "REQ" : _lines_requirements,
    "OVR" : _lines_overview,
    "TAB" : _lines_tables,
}

def get_generator(obj, ext):
    """find the lines generator for the obj type"""
    if is_document(obj):
        doc_name = "{}".format(obj.prefix)
    elif is_item(obj):
        doc_name = "{}".format(obj.document.prefix)

    doc_types = ", ".join(doc for doc in PUBLISH_GENERATORS)
    msg = "Unknown document type: {} (options: {})".format(doc_name, doc_types)
    #exc = doorstop.DoorstopError(msg)

    try:
        gen = PUBLISH_GENERATORS[doc_name]
    except KeyError:
        log.error(msg)
        gen = PUBLISH_GENERATORS["REQ"]
    return gen

def publish_lines(obj, ext='.txt', **kwargs):
    """method to return the lines for various document types"""
    gen = get_generator(obj, ext)
    yield from gen(obj, **kwargs)

# tree = doorstop.build()
# publish_project(tree, 'ProjA', 'public')