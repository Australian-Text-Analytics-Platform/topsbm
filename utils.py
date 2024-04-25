from IPython.display import HTML
from uuid import uuid4
from copy import deepcopy


def embed_js(js_path: str, d3_json: str) -> HTML:
    """Embeds JS within HTML for the jupyter notebook.
    :arg js_path - the path to the JS file using D3.
    :arg d3_json - the path to the input d3 data json.

    This loads a HTML template and embed your JS code within it.
    Embedding JS is lightweight and flexible and does not require
    CORs to be enabled in the server. Also allows ES6 module syntax
    to be used.

    A unique container is added to the HTML distinguished by uuid.
    Otherwise, getElementById on 'container' only will jumbo up the output cells.

    Within your JS script:
    The container can be accessed via id=container-${uuid}
        Append your D3 svg.node() to this div.
    Access d3-json-path from the child node of container with id=_py_data.
        Retrieve the D3 input data json path from here.
        i.e. fetch(`/files/${d3-json-path}`)
    Note: you won't be able to import other JS modules within your JS script.
    """
    with open("./viz/template.html", "r", encoding="utf-8") as h:
        template = h.read()
    with open(js_path, "r", encoding="utf-8") as h:
        js = h.read()
    id_ = uuid4()
    js = f'const uuid = "{id_}";\n' + js
    html = template.format(uuid=id_, js=js, d3_json_path=d3_json)
    return HTML(html)


MAX_MERGE_LEVEL_FROM_MAX_DEPTH: int = -2


def progressive_merge(tree_data: dict) -> dict[int, dict]:
    """Progressively merges the tree data dictionaries based on their depths.
    Outputs a number of merged tree_data for all possible depths.

    Currently, it'll only allow up to max depth/level - 2.
    e.g. max level = 5, we'll have clusters of lvl 0, lvl 1, lvl 2.
    """
    min_level: int = 0
    max_level: int = tree_data["level"]

    # todo: get first child, access level, loop until level = 1
    #   get all children of level 1 and merge the list.
    #   now, this means level 1 will have a list of ids instead of clusters.
    #   do this for all level 1s

    # so, get to level 1, and then merge children. Assign level one children to merged children.
    # for each child in level 5, then each child in level 4, each child in level 3
    merged_0 = deepcopy(tree_data)
    merged_0 = _progressive_merge_leafs(merged_0, merge_level=1)

    return dict()


def _progressive_merge_leafs(tree_data: dict, merge_level: int):
    if tree_data["level"] == (merge_level - 1):
        return tree_data["children"]
    elif tree_data["level"] == merge_level:
        merged = list()
        for child in tree_data["children"]:
            merged.extend(_progressive_merge_leafs(child, merge_level))
        tree_data["children"] = merged
    else:
        for child in tree_data["children"]:
            _progressive_merge_leafs(child, merge_level)
        return tree_data


def _merge_children(children: list[dict]) -> list[dict]:
    # note: if level=-1, there won't be children.
    return list(
        [inner_child for child in children for inner_child in child["children"]]
    )

