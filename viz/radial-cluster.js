import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Specify the chart’s dimensions.
const width = 500;
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

    const container = svg.append("g");

    const secondOuterMostNodes = root.descendants().filter(d => d.height === 1);
    const colorScale = d3.scaleOrdinal(secondOuterMostNodes.map(d => d.data.id), d3.schemeCategory10);  // cycle the 10 colours

    // Append links.
    const linkSelection = container.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1.5)
        .selectAll()
        .data(root.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y))
        .attr("stroke", d => {
            if (d.target.height !== 0) {
                return d3.color("grey")
            } else {
                return colorScale(d.target.parent.data.id)
            }
        });

    // Append nodes.
    container.append("g")
        .selectAll()
        .data(root.descendants().filter(d => d.height !== 0))
        .join("circle")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
        .attr("fill", d => {
            if (d.height > 1) {
                // non-leaf nodes
                return d3.color("grey")
            } else if (d.height === 1) {
                // 2nd outermost layer (level = 0)
                return colorScale(d.data.id);
            } else {
                // leaf nodes
                return colorScale(d.parent.data.id)
            }
        })
        .attr("r", 1.0);

    const outerMostNodes = root.descendants().filter(d => d.height === 0);

    var shapes = [
        d3.symbolCircle,
        d3.symbolCross,
        d3.symbolDiamond,
        // d3.symbolDiamond2,
        d3.symbolPlus,
        d3.symbolSquare,
        // d3.symbolSquare2,
        d3.symbolStar,
        d3.symbolTriangle,
        // d3.symbolTriangle2,
        d3.symbolWye,
        d3.symbolTimes,
    ]
    var shapeIdx = 0;

    var categoryToShape = {};

    const outerMostNodesSelection = container.append("g")
        .selectAll()
        .data(outerMostNodes)
        .join("g");

    outerMostNodesSelection.each(function (d) {
        const group = d3.select(this);
        const category = d.data.category;
        if (category !== null && category !== undefined) {
            if (!categoryToShape.hasOwnProperty(category)) {
                categoryToShape[category] = shapes[shapeIdx % shapes.length];
                shapeIdx++;
            }
            group.append('path')
                .attr('d', d3.symbol().type(categoryToShape[category]).size(8))
                .attr('fill', colorScale(d.parent.data.id));
        } else {
            group.append('circle')
                .attr('fill', colorScale(d.parent.data.id))
                .attr('r', 1.0);
        }
    });

    outerMostNodesSelection
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    // i.e. there are categories
    if (Object.keys(categoryToShape).length > 0) {
        console.log("categoryToShape.length is > 0")
        const legendData = Object.entries(categoryToShape).map(([label, shape]) => ({
            label: label, shape: shape
        }))
        const legend = svg.append('g')
            .attr('class', 'legend')
            .attr('transform', 'translate(-250, -250)');  // Adjust position according to your needs

        legend.selectAll('g')
            .data(legendData)
            .enter()
            .append('g')
            .attr('transform', (d, i) => `translate(0, ${i * 8})`)  // Vertical layout, 8 is margin.
            .each(function (d) {
                const entry = d3.select(this);

                // Add the shape
                entry.append('path')
                    .attr('d', d3.symbol().type(d.shape).size(12))  // Size of the symbol
                    .attr('transform', 'translate(10, 0)')  // Center the shape in the legend entry
                    .attr('fill', 'grey');  // Optional: set a fill color

                // Add the text label
                entry.append('text')
                    .attr('x', 25)  // Position the text right of the shape
                    .attr('y', 2)  // Align text vertically
                    .text(d.label)
                    .attr("font-size", "5.5px");
            });
    }

    // only works if there are categories.
    // nodes not in the same category, reduce opacity to 0.2 on mouseover temporarily.

    // Append labels.
    const labelSelection = container.append("g")
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", 3)
        .selectAll()
        .data(root.descendants().filter(d => d.height === 0 || d.height > 1))
        .join("text")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
        .attr("dy", "0.31em")
        .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
        .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
        .attr("paint-order", "stroke")
        .attr("stroke", "white")
        .attr("fill", d => {
            return "currentColor"
        })
        .text(d => d.data.id)
        .attr("font-size", "4.5px")


    outerMostNodesSelection
        .on("mouseover", (event, d) => {
            const activeCategory = d.data.category;
            if (activeCategory !== null && activeCategory !== undefined) {
                outerMostNodesSelection.style("opacity", (n) => {
                    return n.data.category === activeCategory ? 1 : 0.2;
                })
                linkSelection.style(
                    "opacity",
                    (l) => (l.source.data.category === activeCategory || l.target.data.category === activeCategory) ? 1 : 0.2
                )
                labelSelection.style(
                    "opacity",
                    (label) => label.data.category === activeCategory ? 1 : 0.2
                )
            }
        })
        .on("mouseout", () => {
            outerMostNodesSelection.style("opacity", 1);
            linkSelection.style("opacity", 1);
            labelSelection.style("opacity", 1);
        });

    // todo: rotation - not getting the pivot point correctly.
    // let currentRotation = 0;
    //
    // // Allow spinner drag behaviour
    // const drag = d3.drag()
    //     .on("drag", (event) => {
    //         currentRotation += event.dx;
    //         console.log(`currentRotation: ${currentRotation}`);
    //         container
    //             .attr(
    //                 'transform',
    //                 `rotate(${currentRotation},${cx},${cy})`
    //             )
    //     });
    // container.call(drag);
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
    // note: Binder and Local's /files url path starting point are different.
    //  for binder, start replacing as /files where /doc starts.
    //  for local, start replacing as /files right after the origin. (i.e. replace the entire url path)
    let lastIdx = Math.max(window.location.pathname.indexOf("/doc"), 0)
    let prefix = window.location.pathname.slice(0, lastIdx)
    let svg = await fetch(`${prefix}/files/${fname}`)
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

