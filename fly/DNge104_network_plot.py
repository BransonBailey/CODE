#!/usr/bin/env python3

import os
import webbrowser
from pathlib import Path

import navis
import navis.interfaces.neuprint as neu
from neuprint import Client, fetch_adjacencies, set_default_client


SERVER = "https://neuprint.janelia.org"
DATASET = "male-cns:v1.0"
NEURON_TYPE = "DNge104"
N_TARGETS = 10
OUTPUT_FILE = "DNge104_network.html"


def main():
    # ------------------------------------------------------------------
    # Connect to neuPrint
    # ------------------------------------------------------------------

    token = os.environ.get("NEUPRINT_APPLICATION_CREDENTIALS")

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

    # Your installed neuprint-python version uses module-level functions.
    set_default_client(client)

    # ------------------------------------------------------------------
    # Find the DNge104 source neurons
    # ------------------------------------------------------------------

    source_criteria = neu.NeuronCriteria(type=NEURON_TYPE)

    source_neurons, _ = neu.fetch_neurons(source_criteria)

    if source_neurons.empty:
        raise RuntimeError(
            f"No neurons found with type {NEURON_TYPE!r}"
        )

    source_ids = (
        source_neurons["bodyId"]
        .astype(int)
        .tolist()
    )

    print(f"Found {len(source_ids)} {NEURON_TYPE} neurons:")

    columns_to_print = [
        column
        for column in ["bodyId", "instance", "type", "class", "superclass", "nt"]
        if column in source_neurons.columns
    ]

    print(
        source_neurons[columns_to_print]
        .to_string(index=False)
    )

    # ------------------------------------------------------------------
    # Find downstream connections
    # ------------------------------------------------------------------

    print("\nFetching downstream connections...")

    _, connections = fetch_adjacencies(
        source_criteria,
        None,
    )

    if connections.empty:
        raise RuntimeError(
            f"No downstream connections found for {NEURON_TYPE!r}"
        )

    print("\nConnection columns:")
    print(connections.columns.tolist())

    # A neuron pair can have connections in several ROIs.
    # Sum those rows to obtain one total weight per neuron pair.
    top_connections = (
        connections
        .groupby(
            ["bodyId_pre", "bodyId_post"],
            as_index=False,
        )["weight"]
        .sum()
        .sort_values("weight", ascending=False)
    )

    print("\nStrongest downstream connections:")
    print(
        top_connections
        .head(20)
        .to_string(index=False)
    )

    # Save the complete aggregated connection table.
    top_connections.to_csv(
        "DNge104_connections.csv",
        index=False,
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

    # Include the two DNge104 neurons and remove duplicate IDs.
    all_ids = list(
        dict.fromkeys(source_ids + target_ids)
    )

    print(
        f"\nFetching skeletons for {len(all_ids)} neurons..."
    )

    circuit = neu.fetch_skeletons(
        neu.NeuronCriteria(bodyId=all_ids)
    )

    if len(circuit) == 0:
        raise RuntimeError("No skeletons were returned.")

    print("\nFetched neurons:")
    print(circuit)

    # ------------------------------------------------------------------
    # Fix missing names
    # ------------------------------------------------------------------

    # One target has name=nan. navis/Plotly requires every name to be
    # a string, so replace missing names with the body ID.
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
            f"cable length={neuron.cable_length / 1_000_000:.2f} mm"
        )

    # ------------------------------------------------------------------
    # Create an interactive Plotly 3D graph
    # ------------------------------------------------------------------

    source_ids = {int(body_id) for body_id in source_ids}

    colors = [
        "red" if int(neuron.id) in source_ids else "royalblue"
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
            "<sup>Red = DNge104 | Blue = downstream targets</sup>"
        ),
        showlegend=True,
    )

    # ------------------------------------------------------------------
    # Save and open the graph
    # ------------------------------------------------------------------

    output_path = Path(OUTPUT_FILE).resolve()

    fig.write_html(output_path)

    print("\nSaved interactive graph:")
    print(f"  {output_path}")

    webbrowser.open(output_path.as_uri())

    print("\nThe graph should now be open in your browser.")
    print("Hover over neurons, rotate, zoom, and use the legend.")


if __name__ == "__main__":
    main()

