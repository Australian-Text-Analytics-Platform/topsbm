from IPython.display import HTML
from uuid import uuid4


def embed_js(js_path: str, d3_json: str) -> HTML:
    """ Embeds JS within HTML for the jupyter notebook.
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
    with open('./viz/template.html', 'r', encoding='utf-8') as h:
        template = h.read()
    with open(js_path, 'r', encoding='utf-8') as h:
        js = h.read()
    id_ = uuid4()
    js = f"const uuid = \"{id_}\";\n" + js
    html = template.format(uuid=id_, js=js, d3_json_path=d3_json)
    return HTML(html)
