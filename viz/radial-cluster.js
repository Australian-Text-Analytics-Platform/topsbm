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
function build_radial_cluster(data, width, height) {

    // Create a radial cluster layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const radius = Math.min(width, height) / 2 - 80;
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
        .attr("viewBox", [-(width * 0.5), -(height * 0.54), width, height])
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

    const outerMostNodes = root.descendants().filter(d => d.height === 0);

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
        const legendData = Object.entries(categoryToShape).map(([label, shape]) => ({
            label: label, shape: shape
        }))
        const legend = svg.append('g')
            .attr('class', 'legend')
            // .attr('transform', 'translate(-250, -250)');  // Adjust position according to your needs
            .attr('transform', `translate(${-(width / 2) + 5}, ${-(height / 2)})`);  // Adjust position according to your needs

        const fontSize = Math.min(Math.max(width, height) * 0.013, 20)
        const shapeSize = Math.min(Math.max(width, height) * 0.013, 20)
        legend.selectAll('g')
            .data(legendData)
            .enter()
            .append('g')
            .attr('transform', (d, i) => `translate(0, ${i * fontSize})`)  // Vertical layout, 8 is margin.
            .each(function (d) {
                const entry = d3.select(this);

                // Add the shape
                entry.append('path')
                    .attr('d', d3.symbol().type(d.shape).size(shapeSize))  // Size of the symbol
                    .attr('transform', 'translate(10, 0)')  // Center the shape in the legend entry
                    .attr('fill', 'grey');  // Optional: set a fill color

                // Add the text label
                entry.append('text')
                    .attr('x', 25)  // Position the text right of the shape
                    .attr('y', 2)  // Align text vertically
                    .text(d.label)
                    .attr("font-size", `${fontSize}px`);
            });
    }


    /*
    ++ TEXT Labels ++

    Below configures the text labels for each node.
     */
    const labelSelection = container.append("g")
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", 1.5)
        .selectAll()
        // .data(root.descendants().filter(d => d.height === 0 || d.height > 1))
        .data(root.descendants())
        .join("text")
        .attr("data-event-ref", d => {
                if (d.height === 0 && d.parent !== undefined) {
                    return `label-${d.parent.data.id}-${d.data.id}`
                }
            }
        )
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
        .attr("dy", "0.31em")
        .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
        .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
        .attr("paint-order", "stroke")
        // .attr("stroke", "white")
        .attr("fill", d => {
            return "currentColor"
        })
        .text(d => d.data.id)
        .attr("font-size", d => {
            if (d.height === 0) {
                return "3px"
            } else {
                return "6px"
            }
        })
        .on("mouseover", (event, d) => {
            if (d.height === 0) {
                d3.select(event.currentTarget)
                    .interrupt()
                    .transition()
                    .duration(150)
                    .attr("font-size", "6px")
                // .attr("stroke", "white")
                // .attr("stroke-width", "6px")
                // .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y + 8},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
            }

        })
        .on("mouseout", (event, d) => {
            if (d.height === 0) {
                d3.select(event.currentTarget)
                    .interrupt()
                    .transition()
                    .duration(150)
                    .attr("font-size", d.height === 0 ? "3px" : "6px") // Revert to original font size based on height
                // .attr("stroke", "")
                // .attr("stroke-width", 1.5)
                // .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
            }
        });


    /*
    ++ USER EVENT: Mouse Hover or Mouse Over. ++

    only works if there are categories.
    nodes not in the same category, reduce opacity to 0.2 on mouseover temporarily.
     */
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
            d3.select(`[data-event-ref="label-${d.parent.data.id}-${d.data.id}"]`)
                .interrupt()
                .transition()
                .duration(150)
                .attr("font-size", "4px")
                .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y + 15},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
        })
        .on("mouseout", (event, d) => {
            outerMostNodesSelection.style("opacity", 1);
            linkSelection.style("opacity", 1);
            labelSelection.style("opacity", 1);
            d3.select(`[data-event-ref="label-${d.parent.data.id}-${d.data.id}"]`)
                .interrupt()
                .transition()
                .duration(150)
                .attr("font-size", d.height === 0 ? "3px" : "6px") // Revert to original font size based on height
                .attr("transform", d => {
                    if (d.lockLabelTranslate === undefined || !d.lockLabelTranslate) {
                        return `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`
                    } else {
                        return `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y + 15},0) rotate(${d.x >= Math.PI ? 180 : 0})`
                    }
                })
        })
        .on("click", (event, d) => {
            if (d.lockLabelTranslate === undefined || !d.lockLabelTranslate) {
                d3.select(`[data-event-ref="label-${d.parent.data.id}-${d.data.id}"]`)
                    .interrupt()
                    .transition()
                    .duration(150)
                    .attr("font-size", "4px")
                    .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y + 15},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
                d.lockLabelTranslate = true
            } else {
                d3.select(`[data-event-ref="label-${d.parent.data.id}-${d.data.id}"]`)
                    .interrupt()
                    .transition()
                    .duration(150)
                    .attr("font-size", d.height === 0 ? "3px" : "6px") // Revert to original font size based on height
                    .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
                d.lockLabelTranslate = false
            }
        })
    ;


    /*
    ++ LEGEND (Instructions) ++

    Below show the legends on the visualisation.
     */

    if (outerMostNodes.length > 0 && outerMostNodes[0].data?.category !== undefined) {
        svg.append("text")
            .attr("x", width / 2 - 20)  // Position from the right edge of the SVG
            .attr("y", -(height / 2))          // Position from the top of the SVG
            .attr("text-anchor", "end")  // Align text to the right
            .attr("fill", "#999")  // Text color
            .attr("font-family", "'Helvetica Neue', Arial, sans-serif")  // Font family
            .attr("font-size", `${Math.min(Math.max(width, height) * 0.015, 20)}px`)  // Font size
            .style("pointer-events", "none")  // Make the text non-interactive
            .text("💡 Hover to leaf nodes to find documents in the same category");  // Instruction text
    }

    svg.append("text")
        .attr("x", width / 2 - 20)  // Position from the right edge of the SVG
        .attr("y", -(height / 2) + 20)          // Position from the top of the SVG
        .attr("text-anchor", "end")  // Align text to the right
        .attr("fill", "#999")  // Text color
        .attr("font-family", "'Helvetica Neue', Arial, sans-serif")  // Font family
        .attr("font-size", `${Math.min(Math.max(width, height) * 0.015, 20)}px`)  // Font size
        .style("pointer-events", "none")  // Make the text non-interactive
        .text("You may Zoom and Pan");  // Instruction text


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

    function handleZoom(e) {
        container.attr("transform", e.transform)
    }

    svg.call(
        d3.zoom().extent([[0, 0], [width, height]]).scaleExtent([1, 8]).on('zoom', handleZoom)
    );

    return svg;
}

// function magnify(dataEventRef) {
//     d3.select(`[data-event-ref="${dataEventRef}"]`)
//         .transition()
//         .duration(150)
//         .attr("font-size", "10px")
//         .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y + 10},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
// }
//
// function deMagnify(dataEventRef) {
//     d3.select(`[data-event-ref="${dataEventRef}"]`)
//         .transition()
//         .duration(150)
//         .attr("font-size", d.height === 0 ? "3px" : "6px") // Revert to original font size based on height
//         .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
// }
function enableCenterView(button, svg) {
    button.addEventListener("click", () => {
        const container = svg.select("g");

        // Calculate the bounding box of the container
        const bbox = container.node().getBBox();

        // Center the content by calculating translation offsets
        const offsetX = -bbox.x - bbox.width / 2;
        const offsetY = -bbox.y - bbox.height / 2;

        // Apply a transform to center the content in the SVG viewport
        container.attr("transform", `translate(${offsetX}, ${offsetY})`);
    })
}

// function enableExportAsSVGButton(button, svg) {
//     button.addEventListener("click", () => {
//         // console.log("Clicked");
//         // console.log(svg);
//         // console.log(svg.select("g"));
//         // todo: retrieve the HTML SVG element for the d3 graph
//         //  remove the text elements e.g. "Zoom and Pan",
//         //  modify the svg to add xmlns="http://www.w3.org/2000/svg" in the svg's attribute.
//         //  download the svg as a file.
//     })
// }
function enableExportAsSVGButton(button, svg) {
    button.addEventListener("click", () => {
        // Retrieve the HTML SVG element for the D3 graph
        const svgNode = svg.node();

        // Clone the SVG node to avoid modifying the original
        const clone = svgNode.cloneNode(true);

        // Remove the instruction text elements from the clone
        clone.querySelectorAll("text").forEach(textElem => {
            if (textElem.textContent.includes("💡") ||
                textElem.textContent.includes("Zoom and Pan")) {
                textElem.remove();
            }
        });

        // Ensure the clone has the xmlns attribute
        if (!clone.hasAttribute("xmlns")) {
            clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        }

        // Serialize the cloned SVG to a string
        const serializer = new XMLSerializer();
        let svgString = serializer.serializeToString(clone);

        // Add XML declaration
        svgString = '<?xml version="1.0" standalone="no"?>\r\n' + svgString;

        // Create a Blob from the SVG string
        const blob = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});

        // Create a link to download the Blob as a file
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "topsbm_topics.svg";

        // Simulate a click on the link to trigger the download
        document.body.appendChild(link);
        link.click();

        // Clean up
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    });
}

// -- python output data pass in --
try {
    const container = document.getElementById(`container-${uuid}`)

    const style = window.getComputedStyle(container)
    const width = parseInt(style.getPropertyValue("width").replace("px"));
    const height = parseInt(style.getPropertyValue("height").replace("px"));

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
    const lastIdx = Math.max(window.location.pathname.indexOf("/doc"), 0)
    const prefix = window.location.pathname.slice(0, lastIdx)
    let svg = await fetch(`${prefix}/files/${fname}`)
        .then((res) => {
            if (res.status === 200) {
                return res.json()
            }
            throw new ReferenceError(`${fname} not found.`)
        })
        .then((j) => build_radial_cluster(j, width, height))

    container.append(svg.node())

    enableCenterView(document.getElementById("center-view-btn"), svg)
    enableExportAsSVGButton(document.getElementById("export-svg-btn"), svg)
} catch (err) {
    console.error(err)
}

