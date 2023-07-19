"""Common place for some publishing methods"""
def _format_level(level):
    """Convert a level to a string and keep zeros if not a top level."""
    text = str(level)
    if text.endswith(".0") and len(text) > 3:
        text = text[:-2]
    return text

def _format_md_attr_list(item, linkify):
    """Create a Markdown attribute list for a heading."""
    return " {{#{u} }}".format(u=item.uid) if linkify else ""

def _format_md_ref(item):
    """Format an external reference in Markdown."""
    path, line = item.find_ref()
    path = path.replace("\\", "/")  # always use unix-style paths
    if line:
        return "> `{p}` (line {line})".format(p=path, line=line)
    return "> `{p}`".format(p=path)

def _format_md_references(item):
    """Format an external reference in Markdown."""
    references = item.find_references()
    text_refs = []
    for ref_item in references:
        path, line = ref_item
        path = path.replace("\\", "/")  # always use unix-style paths

        if line:
            text_refs.append("> `{p}` (line {line})".format(p=path, line=line))
        else:
            text_refs.append("> `{p}`".format(p=path))

    return "\n".join(ref for ref in text_refs)

def _format_html_item_link(item, linkify=True):
    """Format an item link in HTML."""
    if linkify and is_item(item):
        if item.header:
            link = '<a href="{p}.html#{u}">{u} {h}</a>'.format(
                u=item.uid, h=item.header, p=item.document.prefix
            )
        else:
            link = '<a href="{p}.html#{u}">{u}</a>'.format(
                u=item.uid, p=item.document.prefix
            )
        return link
    else:
        return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

def _format_md_links(items, linkify, to_html=False):
    """Format a list of linked items in Markdown."""
    links = []
    for item in items:
        if to_html:
            link = _format_html_item_link(item, linkify=linkify)
        else:
            link = _format_md_item_link(item, linkify=linkify)
        links.append(link)
    return ", ".join(links)


def _format_md_item_link(item, linkify=True):
    """Format an item link in Markdown."""
    if linkify and is_item(item):
        if item.header:
            return "[{u} {h}]({p}.md#{u})".format(
                u=item.uid, h=item.header, p=item.document.prefix
            )
        return "[{u}]({p}.md#{u})".format(u=item.uid, p=item.document.prefix)
    return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

def _format_md_label_links(label, links, linkify):
    """Join a string of label and links with formatting."""
    if linkify:
        return "*{lb}* {ls}".format(lb=label, ls=links)
    return "*{lb} {ls}*".format(lb=label, ls=links)
