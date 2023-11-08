import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Specify the chart’s dimensions.
const width = 928;
const height = width;
const cx = width * 0.5; // adjust as needed to fit
const cy = height * 0.54; // adjust as needed to fit
const radius = Math.min(width, height) / 2 - 80;

/**
 * Builds the radial cluster given data.
 * @param data - radial cluster data object
 * @returns svg - D3 svg to append to DOM.
 */
function build_radial_cluster(data) {

    // Create a radial cluster layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const tree = d3.cluster()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);

    // Sort the tree and apply the layout.
    const root = tree(d3.hierarchy(data)
        .sort((a, b) => d3.ascending(a.data.name, b.data.name)));

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1.5)
        .selectAll()
        .data(root.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y));

    // Append nodes.
    svg.append("g")
        .selectAll()
        .data(root.descendants())
        .join("circle")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
        .attr("fill", d => d.children ? "#555" : "#999")
        .attr("r", 2.5);

    // Append labels.
    svg.append("g")
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", 3)
        .selectAll()
        .data(root.descendants())
        .join("text")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
        .attr("dy", "0.31em")
        .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
        .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
        .attr("paint-order", "stroke")
        .attr("stroke", "white")
        .attr("fill", "currentColor")
        .text(d => d.data.name);

    return svg;
}

// -- python output data pass in --
try {
    let container = document.getElementById(`container-${uuid}`)

    let py_data = null;
    for (let i = 0; i < container.children.length; i++) {
        let child = container.children[i]
        if (child.id === "_py_data") {
            py_data = child;
            break
        }
    }
    if (py_data === null) {
        throw new ReferenceError("Missing _py_data from within container.")
    }

    const fname = py_data?.attributes.getNamedItem("d3-json-path")?.value
    if (fname === undefined) {
        throw new ReferenceError("Missing 'd3-json-path' attribute in _py_data.")
    }
    // -- load file --
    let svg = await fetch(`/files/${fname}`)
        .then((res) => {
            if (res.status === 200) {
                return res.json()
            }
            throw new ReferenceError(`${fname} not found.`)
        })
        .then((j) => build_radial_cluster(j))

    container.append(svg.node())
} catch (err) {
    console.error(err)
}

