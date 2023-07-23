""" testing writing custom publisher 
    borrowed most of this from the main doorstop publisher.py methods
    Will proably remove some of them since they aren't needed for table specs
"""

import os
import shutil
import bottle
import markdown
import doorstop

from bottle import template as bottle_template
from doorstop.core.types import is_item, is_tree, iter_documents, iter_items
from publish_common import (_format_level, _format_md_ref, _format_md_references, 
                            _format_md_links, _format_md_label_links)


KEY_IMAGE = "<img src=assets/doorstop/key.png />"

def _tab_lines_markdown(obj, **kwargs):
    """Yield lines for a Markdown report.

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks (for conversion to HTML)

    :return: iterator of lines of text

    """
    def _start_table(pub_list):
        columns = [ "Column" ]
        columns.extend(pub_list)
        columns.append("Notes")

        return "\n".join(["|" + "|".join(columns) + "|", "|" + " ---- |" * len(columns)])

    linkify = kwargs.get("linkify", False)
    to_html = kwargs.get("to_html", False)
    table_started = False
    for item in iter_items(obj):
        level = _format_level(item.level)

        text_lines = item.text.splitlines()

        if item.heading:
            if item.header:
                text_lines.insert(0, item.header)
            # Level and Text
            standard = "\n### {lev} {t}".format(
                lev=level, t=text_lines[0] if text_lines else ""
            )

            table_started = True
            yield standard
            yield _start_table(item.document.publish)
        else:
            key = item.attribute("primarykey") == True

            columns = [ '{}{} <small>[{}]</small>'.format(KEY_IMAGE if key else '',
                                                          text_lines[0], item.uid) ]
            for attr in item.document.publish:
                to_add = item.attribute(attr)
                if isinstance(to_add, str):
                    to_add = to_add.replace('\n', '<br />')
                columns.append(f"{to_add}")

            # Reference
            if item.ref:
                text_lines.append(_format_md_ref(item))

            # Reference
            if item.references:
                text_lines.extend(_format_md_references(item))

            # Parent links
            if item.links:
                items2 = item.parent_items
                label = "Parent links:"
                links = _format_md_links(items2, linkify, to_html=to_html)
                label_links = _format_md_label_links(label, links, linkify)
                text_lines.append(label_links)

            # Child links
            items2 = item.find_child_items()
            if items2:
                yield ""  # break before links
                label = "Child links:"
                links = _format_md_links(items2, linkify, to_html=to_html)
                label_links = _format_md_label_links(label, links, linkify)
                text_lines.append(label_links)

            if not table_started:
                yield _start_table(item.document.publish)
                table_started = True
            columns.append("<br />".join(text_lines[1:]))

            yield "|" + "|".join(columns) + "|"

def _table_of_contents_md(obj, linkify=None):
    toc = "### Table of Contents\n\n"

    for item in iter_items(obj):
        if item.depth == 1:
            prefix = " * "
        else:
            prefix = "    " * (item.depth - 1)
            prefix += "* "

        if item.heading:
            lines = item.text.splitlines()
            if item.header:
                heading = item.header
            else:
                heading = lines[0] if lines else ""
        elif item.header:
            heading = "{h}".format(h=item.header)
        else:
            heading = item.uid

        level = _format_level(item.level)
        lbl = "{lev} {h}".format(lev=level, h=heading)

        if linkify:
            line = "{p}[{lbl}](#{uid})\n".format(p=prefix, lbl=lbl, uid=item.uid)
        else:
            line = "{p}{lbl}\n".format(p=prefix, lbl=lbl)
        toc += line
    return toc

def _tab_lines_html(
    obj, linkify=False, extensions=doorstop.publisher.EXTENSIONS,
    template=doorstop.publisher.HTMLTEMPLATE,
    toc=True):
    """Yield lines for an HTML report.

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks

    :return: iterator of lines of text

    """
    # Determine if a full HTML document should be generated
    try:
        iter(obj)
    except TypeError:
        document = False
    else:
        document = True

    text = "\n".join(_tab_lines_markdown(obj, linkify=linkify, to_html=True))
    body = markdown.markdown(text, extensions=extensions)

    if toc:
        toc_md = _table_of_contents_md(obj, True)
        toc_html = markdown.markdown(toc_md, extensions=extensions)
    else:
        toc_html = ""

    if document:
        try:
            bottle.TEMPLATE_PATH.insert(
                0, os.path.join(os.path.dirname(__file__), "views")
            )
            if "baseurl" not in bottle.SimpleTemplate.defaults:
                bottle.SimpleTemplate.defaults["baseurl"] = ""
            html = bottle_template(
                template, body=body, toc=toc_html, parent=obj.parent, document=obj
            )
        except Exception:
            #log.error("Problem parsing the template %s", template)
            raise
        yield "\n".join(html.split(os.linesep))
    else:
        yield body

def publish_tables(obj, document_name = 'TAB', publish_path = None):
    """method for publishing tables from doorstop requirement files
    Currently can only be called witha tree object.  
    Currently will only publish to html.  
        (but it goes through a markdown step, so adding markdown in the future should 
        not be difficult)
    
    :param obj: tree object to publish.
    :param document_name: the name of the document that contains the table definitions
        defaults to "TAB"
    :param path: the output path for the html output.
    """
    if not is_tree(obj):
        return

    tab_document = obj.find_document(document_name)

    # replaces the publisher method in doorstop
    _original_publisher = doorstop.publisher.FORMAT_LINES['.html']
    doorstop.publisher.FORMAT_LINES['.html'] = _tab_lines_html

    if publish_path is None:
        publish_path = "public"

    # first delete the temp path if it exists
    if os.path.isdir(publish_path):
        shutil.rmtree(publish_path)

    publish_filename = os.path.join(publish_path, "".join([document_name, ".html"]))
    doorstop.publisher.publish(tab_document, publish_filename, ".html", toc=False)

    # bug in develop branch of doorstop copying "template", but looking for "assets"
    os.rename(os.path.join(publish_path, "template"), os.path.join(publish_path, "assets"))

    file_path = os.path.dirname(os.path.realpath(__file__))
    dest_path = os.path.realpath(os.path.join(publish_path, 'assets', 'doorstop', "key.png"))

    shutil.copyfile(os.path.join(file_path, "resources", "key.png"), dest_path)

    # restore the original publisher in doorstop
    doorstop.publisher.FORMAT_LINES['.html'] = _original_publisher
