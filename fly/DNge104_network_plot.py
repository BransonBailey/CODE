#!/usr/bin/env python3

import os
import webbrowser
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

import navis
import navis.interfaces.neuprint as neu
from neuprint import (
    Client,
    fetch_adjacencies,
    set_default_client,
)


SERVER = "https://neuprint.janelia.org"
DATASET = "male-cns:v1.0"
NEURON_TYPE = "DNge104"
N_TARGETS = 10

OUTPUT_FILE = "DNge104_network.html"
CONNECTION_OUTPUT_FILE = "DNge104_connections.csv"


# ----------------------------------------------------------------------
# Anatomical orientation settings
# ----------------------------------------------------------------------
#
# Set these only after inspecting the X+, Y+, and Z+ axes in the graph.
#
# Examples:
#
#   FRONT_AXIS = "X"
#   FRONT_SIGN = -1
#
# means the front/eyes are toward decreasing X.
#
# Valid axes: "X", "Y", "Z"
# Valid signs: 1 or -1
#
# Leave FRONT_AXIS as None to display only the coordinate axes.
#

FRONT_AXIS = None
FRONT_SIGN = 1


def get_coordinate_bounds(circuit):
    """Return the minimum and maximum X, Y, Z coordinates."""

    all_points = np.vstack(
        [
            neuron.nodes[["x", "y", "z"]].to_numpy()
            for neuron in circuit
        ]
    )

    minimum = all_points.min(axis=0)
    maximum = all_points.max(axis=0)

    return minimum, maximum


def add_coordinate_axes(fig, circuit):
    """
    Add diagnostic X+, Y+, and Z+ axes to the Plotly scene.

    This does not assume which axis points toward the fly's front.
    """

    minimum, maximum = get_coordinate_bounds(circuit)

    x_min, y_min, z_min = minimum
    x_max, y_max, z_max = maximum

    ranges = maximum - minimum

    x_range = max(ranges[0], 1)
    y_range = max(ranges[1], 1)
    z_range = max(ranges[2], 1)

    # Put the coordinate triad outside the neuron cloud.
    origin = np.array(
        [
            x_min - 0.20 * x_range,
            y_min - 0.20 * y_range,
            z_min - 0.20 * z_range,
        ]
    )

    axis_length = max(
        x_range,
        y_range,
        z_range,
    ) * 0.35

    axes = [
        ("X+", np.array([1.0, 0.0, 0.0]), "red"),
        ("Y+", np.array([0.0, 1.0, 0.0]), "green"),
        ("Z+", np.array([0.0, 0.0, 1.0]), "blue"),
    ]

    for label, direction, color in axes:
        endpoint = origin + direction * axis_length

        # Axis line.
        fig.add_trace(
            go.Scatter3d(
                x=[origin[0], endpoint[0]],
                y=[origin[1], endpoint[1]],
                z=[origin[2], endpoint[2]],
                mode="lines",
                line=dict(
                    color=color,
                    width=10,
                ),
                name=label,
                hoverinfo="skip",
                showlegend=True,
            )
        )

        # Axis label.
        fig.add_trace(
            go.Scatter3d(
                x=[endpoint[0]],
                y=[endpoint[1]],
                z=[endpoint[2]],
                mode="text",
                text=[label],
                textfont=dict(
                    color=color,
                    size=18,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # Arrowhead.
        fig.add_trace(
            go.Cone(
                x=[origin[0]],
                y=[origin[1]],
                z=[origin[2]],
                u=[direction[0]],
                v=[direction[1]],
                w=[direction[2]],
                sizemode="absolute",
                sizeref=max(axis_length * 0.12, 1),
                anchor="tail",
                colorscale=[
                    [0, color],
                    [1, color],
                ],
                showscale=False,
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
        )
    )


def add_front_back_labels(fig, circuit):
    """
    Add FRONT / EYES and BACK / BUTT labels after the correct
    anatomical axis and direction have been identified.
    """

    if FRONT_AXIS not in {"X", "Y", "Z"}:
        print(
            "\nFRONT_AXIS is None, so only coordinate axes "
            "will be displayed."
        )
        return

    if FRONT_SIGN not in {-1, 1}:
        raise ValueError(
            "FRONT_SIGN must be either 1 or -1."
        )

    minimum, maximum = get_coordinate_bounds(circuit)

    x_min, y_min, z_min = minimum
    x_max, y_max, z_max = maximum

    ranges = maximum - minimum

    x_range = max(ranges[0], 1)
    y_range = max(ranges[1], 1)
    z_range = max(ranges[2], 1)

    # Select the coordinate index for the configured axis.
    axis_index = {
        "X": 0,
        "Y": 1,
        "Z": 2,
    }[FRONT_AXIS]

    front_coordinate = (
        minimum[axis_index]
        if FRONT_SIGN < 0
        else maximum[axis_index]
    )

    back_coordinate = (
        maximum[axis_index]
        if FRONT_SIGN < 0
        else minimum[axis_index]
    )

    # Place labels to the side of the neuron cloud.
    x_marker = x_min - 0.10 * x_range
    z_marker = z_min - 0.10 * z_range

    if FRONT_AXIS == "X":
        front_point = [front_coordinate, y_min, z_marker]
        back_point = [back_coordinate, y_min, z_marker]

    elif FRONT_AXIS == "Y":
        front_point = [x_marker, front_coordinate, z_marker]
        back_point = [x_marker, back_coordinate, z_marker]

    else:
        front_point = [x_marker, y_min, front_coordinate]
        back_point = [x_marker, y_min, back_coordinate]

    # Draw the biological orientation line.
    fig.add_trace(
        go.Scatter3d(
            x=[front_point[0], back_point[0]],
            y=[front_point[1], back_point[1]],
            z=[front_point[2], back_point[2]],
            mode="lines",
            line=dict(
                color="black",
                width=8,
            ),
            name="front ↔ back",
            hoverinfo="skip",
            showlegend=True,
        )
    )

    # Front label.
    fig.add_trace(
        go.Scatter3d(
            x=[front_point[0]],
            y=[front_point[1]],
            z=[front_point[2]],
            mode="text",
            text=["FRONT / EYES"],
            textfont=dict(
                color="darkgreen",
                size=16,
            ),
            textposition="middle left",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Back label.
    fig.add_trace(
        go.Scatter3d(
            x=[back_point[0]],
            y=[back_point[1]],
            z=[back_point[2]],
            mode="text",
            text=["BACK / BUTT"],
            textfont=dict(
                color="darkred",
                size=16,
            ),
            textposition="middle left",
            hoverinfo="skip",
            showlegend=False,
        )
    )


def main():
    # ------------------------------------------------------------------
    # Connect to neuPrint
    # ------------------------------------------------------------------

    token = os.environ.get(
        "NEUPRINT_APPLICATION_CREDENTIALS"
    )

    if not token:
        raise RuntimeError(
            "NEUPRINT_APPLICATION_CREDENTIALS is not set.\n\n"
            "Set it with:\n"
            "export NEUPRINT_APPLICATION_CREDENTIALS='your-token'"
        )

    client = Client(
        SERVER,
        dataset=DATASET,
        token=token,
    )

    neu.set_default_client(client)

    # ------------------------------------------------------------------
    # Find DNge104 neurons
    # ------------------------------------------------------------------

    source_criteria = neu.NeuronCriteria(
        type=NEURON_TYPE
    )

    source_neurons, _ = neu.fetch_neurons(
        source_criteria
    )

    if source_neurons.empty:
        raise RuntimeError(
            f"No neurons found with type {NEURON_TYPE!r}"
        )

    source_ids = (
        source_neurons["bodyId"]
        .astype(int)
        .tolist()
    )

    print(
        f"Found {len(source_ids)} "
        f"{NEURON_TYPE} neurons:"
    )

    columns_to_print = [
        column
        for column in [
            "bodyId",
            "instance",
            "type",
            "class",
            "superclass",
            "nt",
        ]
        if column in source_neurons.columns
    ]

    print(
        source_neurons[columns_to_print]
        .to_string(index=False)
    )

    # ------------------------------------------------------------------
    # Fetch downstream connections
    # ------------------------------------------------------------------

    print("\nFetching downstream connections...")

    _, connections = fetch_adjacencies(
        source_criteria,
        None,
    )

    if connections.empty:
        raise RuntimeError(
            f"No downstream connections found for "
            f"{NEURON_TYPE!r}"
        )

    print("\nConnection columns:")
    print(connections.columns.tolist())

    top_connections = (
        connections
        .groupby(
            ["bodyId_pre", "bodyId_post"],
            as_index=False,
        )["weight"]
        .sum()
        .sort_values(
            "weight",
            ascending=False,
        )
    )

    print("\nStrongest downstream connections:")
    print(
        top_connections
        .head(20)
        .to_string(index=False)
    )

    top_connections.to_csv(
        CONNECTION_OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved connection table: "
        f"{CONNECTION_OUTPUT_FILE}"
    )

    # ------------------------------------------------------------------
    # Select target neurons
    # ------------------------------------------------------------------

    target_ids = (
        top_connections
        .drop_duplicates("bodyId_post")
        .head(N_TARGETS)["bodyId_post"]
        .astype(int)
        .tolist()
    )

    all_ids = list(
        dict.fromkeys(source_ids + target_ids)
    )

    print(
        f"\nFetching skeletons for "
        f"{len(all_ids)} neurons..."
    )

    circuit = neu.fetch_skeletons(
        neu.NeuronCriteria(bodyId=all_ids)
    )

    if len(circuit) == 0:
        raise RuntimeError(
            "No skeletons were returned."
        )

    print("\nFetched neurons:")
    print(circuit)

    # ------------------------------------------------------------------
    # Fix missing names
    # ------------------------------------------------------------------

    for neuron in circuit:
        if not isinstance(neuron.name, str):
            neuron.name = f"bodyId_{neuron.id}"
        elif neuron.name.lower() == "nan":
            neuron.name = f"bodyId_{neuron.id}"

    # ------------------------------------------------------------------
    # Print neuron details
    # ------------------------------------------------------------------

    print("\nNeuron details:")

    for neuron in circuit:
        print(
            f"body ID={neuron.id} | "
            f"name={neuron.name} | "
            f"nodes={neuron.n_nodes:,} | "
            f"leafs={neuron.n_leafs:,} | "
            f"cable length="
            f"{neuron.cable_length / 1_000_000:.2f} mm"
        )

    # ------------------------------------------------------------------
    # Create interactive 3D graph
    # ------------------------------------------------------------------

    source_id_set = {
        int(body_id)
        for body_id in source_ids
    }

    colors = [
        (
            "red"
            if int(neuron.id) in source_id_set
            else "royalblue"
        )
        for neuron in circuit
    ]

    print("\nCreating interactive 3D graph...")

    fig = navis.plot3d(
        circuit,
        backend="plotly",
        color=colors,
        hover_name=True,
        width=1400,
        height=950,
    )

    fig.update_layout(
        title=(
            f"{NEURON_TYPE}: strongest downstream partners"
            "<br>"
            "<sup>"
            "Red = DNge104 | "
            "Blue = downstream targets"
            "</sup>"
        ),
        showlegend=True,
        margin=dict(
            l=0,
            r=0,
            t=80,
            b=0,
        ),
    )

    # Always show diagnostic coordinate axes.
    add_coordinate_axes(fig, circuit)

    # These labels remain disabled until FRONT_AXIS is configured.
    add_front_back_labels(fig, circuit)

    # ------------------------------------------------------------------
    # Save and open graph
    # ------------------------------------------------------------------

    output_path = Path(
        OUTPUT_FILE
    ).resolve()

    fig.write_html(output_path)

    print("\nSaved interactive graph:")
    print(f"  {output_path}")

    webbrowser.open(
        output_path.as_uri()
    )

    print(
        "\nThe graph should now be open in your browser."
    )
    print(
        "Use the red, green, and blue coordinate axes "
        "to determine the anatomical orientation."
    )


if __name__ == "__main__":
    main()

