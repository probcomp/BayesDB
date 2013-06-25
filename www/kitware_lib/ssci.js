/*jslint browser: true, unparam: true*/

/*globals $, d3 */

function visCrossCat(spec) {
    "use strict";
    var that,
        matrix,
        margin,
        color,
        cellSize,
        rows,
        columns,
        views,
        columnPermute,
        rowPermute,
        partitions,
        numPartitions,
        firstColumnInView,
        svg,
        transitionDuration,
        zoom,
        view,
        rowFilter,
        columnFilter;

    function columnPosition(j) {
        j = Math.max(0, j);
        return columnPermute[j] * cellSize + 115 * views[j];
    }

    function rowPosition(i, j) {
        j = Math.max(0, j);
        var numParts = numPartitions[views[j]],
            partOffset;
        if (numParts === 1) {
            partOffset = 100;
        } else {
            partOffset = 100 / (numParts - 1) * partitions[views[j]][i];
        }
        return rowPermute[views[j]][i] * cellSize + partOffset;
    }

    function updateTransform(dur) {
        var extent,
            gap,
            trans,
            offset,
            viewWidth,
            windowWidth,
            viewMinX,
            viewMaxX;

        if (rows === undefined) {
            return;
        }

        // Clamp view to a valid range in case we lost a view
        view = Math.max(0, Math.min(view, partitions.length - 1));

        extent = {x: 0, y: 0};
        offset = {x: 0, y: 0};
        extent.x = cellSize * columns.length + 115 * partitions.length;
        extent.y = cellSize * rows.length + 100 + margin.top;
        extent.x *= zoom;
        extent.y *= zoom;

        windowWidth = $(window).width();
        if (extent.x < windowWidth) {
            offset.x = (windowWidth - extent.x) / 2 + zoom * 115;
        } else {
            if (view < partitions.length - 1) {
                viewMaxX = zoom * (columnPosition(firstColumnInView[view + 1]) - 115);
            } else {
                viewMaxX = extent.x;
            }
            viewMinX = zoom * (columnPosition(firstColumnInView[view]) - 115);
            viewWidth = viewMaxX - viewMinX;
            gap = (windowWidth - viewWidth) / 2;
            offset.x = gap - viewMinX;
        }
        offset.y = Math.max(0, ($(window).height() - $(".gutter").height() - extent.y) / 2);
        offset.y += zoom * margin.top;

        trans = d3.select("#transform");
        if (dur !== undefined) {
            trans = trans.transition().duration(dur);
        }
        trans.attr("transform", "translate(" + offset.x + "," + offset.y + "),scale(" + zoom + ")");
    }

    function selected(d) {
        var rowSelected,
            columnSelected;
        rowSelected = !rowFilter || rows[d.i].indexOf(rowFilter) >= 0;
        columnSelected = !columnFilter || columns[d.j].indexOf(columnFilter) >= 0;
        return rowSelected && columnSelected;
    }

    function cellOpacity(d) {
        var opacity = 1;
        if (d.value === 0) {
            opacity = 0.5;
        }
        return opacity;
    }

    function selectedOpacity(d) {
        var opacity = cellOpacity(d);
        if (!selected(d)) {
            opacity *= 0.1;
        }
        return opacity;
    }

    function updateSelection() {
        d3.selectAll(".row text.row-text").classed("active", function (d) { return !rowFilter || d.indexOf(rowFilter) >= 0; });
        d3.selectAll(".column text").classed("active", function (d, i) { return !columnFilter || columns[i].indexOf(columnFilter) >= 0; });
        d3.selectAll(".cell").attr("opacity", selectedOpacity);
    }

    function updateVisualization() {
        var cell,
            column,
            delayFactor,
            row,
            updateCellRow;

        function mouseover(p) {
            d3.selectAll(".row text.row-text").classed("active", function (d) { return d === rows[p.i]; });
            d3.selectAll(".column text").classed("active", function (d, i) { return i === p.j; });
            d3.selectAll(".cell").attr("opacity", function (d) {
                var opacity = cellOpacity(d);
                if (d.i !== p.i) {
                    opacity *= 0.1;
                }
                return opacity;
            });
        }

        function mouseout() {
            updateSelection();
        }

        updateCellRow = function (partition, viewIndex) {
            var col = firstColumnInView[viewIndex],
                rowText = d3.select(this).selectAll(".row-text").data(rows);

            rowText.enter().append("text")
                .attr("class", "row-text")
                .attr("x", -6)
                .attr("y", cellSize / 2)
                .attr("dy", ".32em")
                .attr("transform", function (d, i) { return "translate(" + columnPosition(col) + "," + rowPosition(i, col) + ")"; })
                .attr("text-anchor", "end")
                .text(function (d, i) { return d; });
            rowText.style("visibility", col < 0 ? "hidden" : "visible");
            rowText.transition().duration(transitionDuration)
                .delay(function (d) { return delayFactor * columnPosition(col); })
                .attr("transform", function (d, i) { return "translate(" + columnPosition(col) + "," + rowPosition(i, col) + ")"; });
        };

        delayFactor = 0.5 * transitionDuration / (cellSize * columns.length + 115 * partitions.length);

        column = svg.selectAll(".column")
            .data(columns);
        column.enter().append("g")
            .attr("class", "column")
            .attr("transform", function (d, i) { return "translate(" + columnPosition(i) + ")rotate(-90)"; })
            .append("text")
            .attr("x", 6)
            .attr("y", cellSize / 2)
            .attr("dy", ".32em")
            .attr("text-anchor", "start")
            .text(function (d) { return d; });
        column.transition().duration(transitionDuration)
            .delay(function (d, i) { return delayFactor * columnPosition(i); })
            .attr("transform", function (d, i) { return "translate(" + columnPosition(i) + ")rotate(-90)"; });

        row = svg.selectAll(".row")
            .data(partitions);
        row.enter().append("g")
            .attr("class", "row")
            .each(updateCellRow);
        row.exit().remove();
        row.transition().duration(transitionDuration)
            .each(updateCellRow);

        cell = svg.selectAll(".cell")
            .data(matrix);
        cell.enter().append("rect")
            .attr("class", "cell")
            .attr("x", function (d) { return columnPosition(d.j); })
            .attr("y", function (d) { return rowPosition(d.i, d.j); })
            .attr("width", cellSize)
            .attr("height", cellSize)
            .attr("opacity", cellOpacity)
            .style("fill", function (d) { return color(d.value); })
            .on("mouseover", mouseover)
            .on("mouseout", mouseout)
            .append("title")
            .text(function (d) { return rows[d.i] + " " + columns[d.j] + "? " + (d.value); });
        cell.transition().duration(transitionDuration)
            .delay(function (d) { return delayFactor * columnPosition(d.j); })
            .attr("x", function (d) { return columnPosition(d.j); })
            .attr("y", function (d) { return rowPosition(d.i, d.j); });

        updateTransform(transitionDuration);
    }

    function updateData(columnOrder, rowOrder, columnPartitions, rowPartitions) {
        var column,
            columnName,
            columnPermuteInverted,
            rowName,
            view;

        // Sort columns first by view, then by column name.
        function sortColumns(i, j) {
            if (views[i] !== views[j]) {
                return d3.ascending(views[i], views[j]);
            }
            return d3.ascending(columns[i], columns[j]);
        }

        // Sort rows first by partition, then by row name.
        function sortRows(view) {
            return function (i, j) {
                if (partitions[view][i] !== partitions[view][j]) {
                    return d3.ascending(partitions[view][i], partitions[view][j]);
                }
                return d3.ascending(rows[i], rows[j]);
            };
        }

        // Given an array containing a permutation (i.e. it has values in the
        // range 0 to arr.length - 1 that each appear only once), find
        // the inverse permutation such that inverse[arr[i]] === i for all i.
        function invertPermutation(arr) {
            var i,
                inverse = [];
            for (i = 0; i < arr.length; i = i + 1) {
                inverse[arr[i]] = i;
            }
            return inverse;
        }

        // Computes new values for an array by re-indexing values
        // so that all values not present in the array are skipped,
        // preserving the original ordering of the values.
        // For example,
        //     > result = removeEmpty([1, 4, 1, 3]);
        //     > result;
        //     [0, 2, 0, 1]
        // The returned array also contains a remappedIndex field
        // that contains an array mapping old indices to new indices.
        // In our example,
        //     > result.remappedIndex;
        //     [undefined, 0, undefined, 1, 2]
        //     > remappedIndex[1] => 0
        //     > remappedIndex[3] => 1
        //     > remappedIndex[4] => 2
        function removeEmpty(arr) {
            var i,
                notEmpty = [],
                numEmpty = 0,
                result = [];

            for (i = 0; i < arr.length; i = i + 1) {
                notEmpty[arr[i]] = true;
            }

            result.remappedIndex = [];
            for (i = 0; i < notEmpty.length; i = i + 1) {
                if (notEmpty[i]) {
                    result.remappedIndex[i] = i - numEmpty;
                } else {
                    numEmpty = numEmpty + 1;
                }
            }

            for (i = 0; i < arr.length; i = i + 1) {
                result[i] = result.remappedIndex[arr[i]];
            }

            return result;
        }

        rows = [];
        for (rowName in rowOrder.labelToIndex) {
            if (rowOrder.labelToIndex.hasOwnProperty(rowName)) {
                rows[rowOrder.labelToIndex[rowName] - 1] = rowName.toLowerCase();
            }
        }

        columns = [];
        for (columnName in columnOrder.labelToIndex) {
            if (columnOrder.labelToIndex.hasOwnProperty(columnName)) {
                columns[columnOrder.labelToIndex[columnName] - 1] = columnName.replace(/_/g, " ");
            }
        }

        // Reindex all indices to be zero-based and eliminate empty views/partitions.
        views = removeEmpty(columnPartitions.columnPartitionAssignments);
        partitions = [];
        for (view = 0; view < rowPartitions.rowPartitionAssignments.length; view = view + 1) {
            if (views.remappedIndex[view + 1] !== undefined) {
                partitions[views.remappedIndex[view + 1]] = removeEmpty(rowPartitions.rowPartitionAssignments[view]);
            }
        }

        // Determine the ordering of columns and rows in this view.
        columnPermuteInverted = d3.range(columns.length).sort(sortColumns);
        columnPermute = invertPermutation(columnPermuteInverted);
        rowPermute = [];
        for (view = 0; view < partitions.length; view = view + 1) {
            rowPermute[view] = invertPermutation(d3.range(rows.length).sort(sortRows(view)));
        }

        // Compute the number of partitions in each view.
        numPartitions = [];
        for (view = 0; view < partitions.length; view = view + 1) {
            numPartitions[view] = d3.max(partitions[view]) + 1;
        }

        // We need the first column in each view to know where to place the row labels.
        firstColumnInView = [];
        for (column = 0; column < views.length; column = column + 1) {
            while (views[columnPermuteInverted[column]] >= firstColumnInView.length) {
                firstColumnInView[views[columnPermuteInverted[column]]] = columnPermuteInverted[column];
            }
        }
        while (firstColumnInView.length < partitions.length) {
            firstColumnInView.push(-1);
        }

        updateVisualization();
        updateSelection();
    }

    // Set up defaults
    matrix = spec.matrix;
    margin = spec.margin || {top: 150, right: 800, bottom: 200, left: 150};
    color = spec.color || d3.scale.category20().domain([1, 0]);
    cellSize = spec.cellSize || 20;
    zoom = spec.zoom || 0.3;
    transitionDuration = spec.transitionDuration || 1000;
    view = 0;

    svg = d3.select("#svg").append("g").attr("id", "transform");
    updateTransform();
    $(window).resize(updateTransform);

    that = {};

    that.update = function (id) {
        d3.json("data/M_c.json", function (columnOrder) {
            d3.json("data/M_r.json", function (rowOrder) {
                d3.json("data/X_L_" + id + ".json", function (columnPartitions) {
                    d3.json("data/X_D_" + id + ".json", function (rowPartitions) {
                        updateData(columnOrder, rowOrder, columnPartitions, rowPartitions);
                    });
                });
            });
        });
    };

    that.zoom = function (level) {
        if (level === undefined) {
            return zoom;
        }
        zoom = level;
        updateTransform(1000);
    };

    that.view = function (index) {
        if (index === undefined) {
            return view;
        }
        view = index;
        if (partitions !== undefined) {
            view = Math.max(0, Math.min(view, partitions.length - 1));
        }
        updateTransform(1000);
    };

    that.rowFilter = function (text) {
        if (text === undefined) {
            return rowFilter;
        }
        rowFilter = text;
        updateSelection();
    };

    that.columnFilter = function (text) {
        if (text === undefined) {
            return columnFilter;
        }
        columnFilter = text;
        updateSelection();
    };

    return that;
}

window.onload = function () {
    "use strict";

    d3.json("data/json_indices", function (indices_data) {
    d3.json("data/T.json", function (data) {
        var i,
            ids,
            j,
            matrix,
            playing,
            timerId,
            vis;

        function updater() {
            var time = d3.select("#time").node();
            time.selectedIndex = (time.selectedIndex + 1) % ids.length;
            vis.update(ids[time.selectedIndex]);
        }

	ids = indices_data["ids"]
        // ids = [
        //     "73524567995_00",
        //     "73524568270_01",
        //     "73524568278_02",
        //     "73524568287_03",
        //     "73524568298_04",
        //     "73524568305_05",
        //     "73524568313_06",
        //     "73524568322_07",
        //     "73524568328_08",
        //     "73524568338_09",
        //     "73524568345_10",
        //     "73524568352_11"
        // ];

        playing = true;

        matrix = [];
        for (i = 0; i < data.length; i = i + 1) {
            for (j = 0; j < data[i].length; j = j + 1) {
                matrix.push({i: i, j: j, value: data[i][j]});
            }
        }
        vis = visCrossCat({matrix: matrix});

        d3.select("#time").selectAll("option")
            .data(ids)
            .enter().append("option")
            .attr("value", function (d) { return d; })
            .text(function (d) { return d.split("_")[1]; });

        d3.select("#time").on("change", function () {
            playing = false;
            d3.select("#play i").classed("icon-play", true).classed("icon-pause", false);
            clearTimeout(timerId);
            vis.update(this.value);
        });

        d3.select("#play").on("click", function () {
            playing = !playing;
            d3.select("#play i").classed("icon-pause", playing).classed("icon-play", !playing);
            if (playing) {
                timerId = setInterval(updater, 5000);
            } else {
                clearTimeout(timerId);
            }
        });

        d3.select("#zoom-in").on("click", function () {
            vis.zoom(vis.zoom() * 1.5);
        });

        d3.select("#zoom-out").on("click", function () {
            vis.zoom(vis.zoom() / 1.5);
        });

        d3.select("#prev").on("click", function () {
            vis.view(vis.view() - 1);
        });

        d3.select("#next").on("click", function () {
            vis.view(vis.view() + 1);
        });

        d3.select("#row-search").on("keyup", function () {
            vis.rowFilter(this.value);
        });

        d3.select("#column-search").on("keyup", function () {
            vis.columnFilter(this.value);
        });

        vis.update(d3.select("#time").node().value);
        if (playing) {
            timerId = setInterval(updater, 4000);
        }
    });
    });
};
