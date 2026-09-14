#!/usr/bin/env python3

import os
from functools import lru_cache

import navis
import pandas as pd
import plotly.graph_objects as go

from dash import Dash, Input, Output, dcc, html
from neuprint import Client, NeuronCriteria
import navis.interfaces.neuprint as neu


SERVER = "https://neuprint.janelia.org"
DATASET = "male-cns:v1.0"

HOST = "127.0.0.1"
PORT = 8050

MAX_SELECTED_NEURONS = 20


# ----------------------------------------------------------------------
# Connect to neuPrint
# ----------------------------------------------------------------------

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

# navis.interfaces.neuprint uses a module-level default client.
neu.set_default_client(client)


# ----------------------------------------------------------------------
# Fetch neuron metadata
# ----------------------------------------------------------------------

print("Fetching neuron list from neuPrint...")

result = neu.fetch_neurons(
    NeuronCriteria(),
)

# Different installed versions return different shapes:
#
#   DataFrame
#   (neurons, roi_counts)
#   (neurons, roi_counts, additional_data)
#
# We only need the first item: the neuron metadata table.

if isinstance(result, tuple):
    neurons = result[0]
else:
    neurons = result

if neurons.empty:
    raise RuntimeError(
        "neuPrint returned no neurons."
    )

neurons["bodyId"] = (
    neurons["bodyId"]
    .astype(int)
)


# ----------------------------------------------------------------------
# Metadata helpers
# ----------------------------------------------------------------------

def safe_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value)


def metadata_text(row):
    fields = [
        "type",
        "instance",
        "class",
        "superclass",
        "subclass",
        "cellBodyFiber",
        "hemilineage",
        "somaNeuromere",
        "entryNerve",
        "exitNerve",
        "modality",
        "description",
    ]

    return " ".join(
        safe_text(row.get(field, ""))
        for field in fields
    ).lower()


def classify_family(row):
    """
    Assign a broad family using neuron metadata.

    These categories are keyword-based. The original neuPrint
    metadata is still shown in the dropdown labels.
    """

    text = metadata_text(row)

    if any(
        word in text
        for word in [
            "optic",
            "visual",
            "lamina",
            "medulla",
            "lobula",
            "lobula plate",
            "ocellar",
        ]
    ):
        return "Optical / visual"

    if any(
        word in text
        for word in [
            "sensory",
            "sens",
            "johnston",
            "mechanosens",
            "olfactory",
            "gustatory",
            "auditory",
            "proprio",
            "receptor",
        ]
    ):
        return "Sensory"

    if any(
        word in text
        for word in [
            "motor",
            "motoneuron",
            "motor neuron",
        ]
    ):
        return "Motor"

    if any(
        word in text
        for word in [
            "descending",
            "dn",
        ]
    ):
        return "Descending"

    if any(
        word in text
        for word in [
            "ascending",
            "ascending neuron",
        ]
    ):
        return "Ascending"

    if any(
        word in text
        for word in [
            "projection",
            "pn",
        ]
    ):
        return "Projection"

    if any(
        word in text
        for word in [
            "local",
            "interneuron",
            "interneural",
        ]
    ):
        return "Local interneuron"

    if any(
        word in text
        for word in [
            "mushroom body",
            "kenyon",
            "mbon",
            "kc",
        ]
    ):
        return "Mushroom body"

    if any(
        word in text
        for word in [
            "central complex",
            "central-complex",
            "fan-shaped",
            "ellipsoid",
            "protocerebral bridge",
        ]
    ):
        return "Central complex"

    return "Other / unclassified"


def make_neuron_label(row):
    body_id = int(row["bodyId"])

    neuron_type = safe_text(
        row.get("type", "")
    )

    instance = safe_text(
        row.get("instance", "")
    )

    family = safe_text(
        row.get("family", "")
    )

    label = f"bodyId {body_id}"

    if neuron_type:
        label += f" | type={neuron_type}"

    if instance and instance != neuron_type:
        label += f" | instance={instance}"

    if family:
        label += f" | [{family}]"

    return label


neurons["family"] = neurons.apply(
    classify_family,
    axis=1,
)

neurons["label"] = neurons.apply(
    make_neuron_label,
    axis=1,
)


def make_dropdown_options(dataframe):
    return [
        {
            "label": row["label"],
            "value": int(row["bodyId"]),
        }
        for _, row in dataframe.iterrows()
    ]


family_options = [
    {
        "label": family,
        "value": family,
    }
    for family in sorted(
        neurons["family"]
        .dropna()
        .unique()
        .tolist()
    )
]

all_neuron_options = make_dropdown_options(
    neurons
)


# ----------------------------------------------------------------------
# Skeleton cache
# ----------------------------------------------------------------------

@lru_cache(maxsize=128)
def fetch_selected_skeletons(body_ids):
    """
    Fetch skeletons for selected body IDs.

    The tuple is cached so repeatedly selecting and deselecting
    neurons does not unnecessarily download the same skeletons.
    """

    body_ids = tuple(
        int(body_id)
        for body_id in body_ids
    )

    if not body_ids:
        return []

    print(
        f"Fetching skeletons for "
        f"{len(body_ids)} neurons..."
    )

    skeletons = neu.fetch_skeletons(
        NeuronCriteria(
            bodyId=list(body_ids),
        )
    )

    return list(skeletons)


# ----------------------------------------------------------------------
# Plot helpers
# ----------------------------------------------------------------------

def empty_figure(message):
    fig = go.Figure()

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
        ),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=18),
            )
        ],
    )

    return fig


def make_figure(selected_body_ids):
    if not selected_body_ids:
        return empty_figure(
            "Select one or more neurons."
        )

    if len(selected_body_ids) > MAX_SELECTED_NEURONS:
        return empty_figure(
            f"Select no more than "
            f"{MAX_SELECTED_NEURONS} neurons."
        )

    body_ids = tuple(
        sorted(
            int(body_id)
            for body_id in selected_body_ids
        )
    )

    skeletons = fetch_selected_skeletons(
        body_ids
    )

    if not skeletons:
        return empty_figure(
            "No skeletons were returned."
        )

    colors = [
        "red",
        "royalblue",
        "darkorange",
        "purple",
        "teal",
        "gold",
        "brown",
        "magenta",
        "limegreen",
        "navy",
    ]

    for neuron in skeletons:
        if not isinstance(neuron.name, str):
            neuron.name = (
                f"bodyId_{neuron.id}"
            )

    fig = navis.plot3d(
        skeletons,
        backend="plotly",
        color=[
            colors[index % len(colors)]
            for index in range(len(skeletons))
        ],
        hover_name=True,
        width=1200,
        height=800,
    )

    fig.update_layout(
        template="plotly_white",
        title=(
            f"Selected neurons: "
            f"{len(skeletons)}"
        ),
        margin=dict(
            l=0,
            r=0,
            t=60,
            b=0,
        ),
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
    )

    return fig


# ----------------------------------------------------------------------
# Dash application
# ----------------------------------------------------------------------

app = Dash(
    __name__,
    title="NeuPrint Neuron Browser",
)


app.layout = html.Div(
    [
        html.H1(
            "NeuPrint Neuron Browser",
            style={
                "marginBottom": "4px",
            },
        ),

        html.Div(
            [
                "Dataset: ",
                html.Code(DATASET),
            ],
            style={
                "color": "#555",
                "marginBottom": "20px",
            },
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Filter by family"
                        ),

                        dcc.Dropdown(
                            id="family-dropdown",
                            options=family_options,
                            value=[],
                            multi=True,
                            clearable=True,
                            placeholder=(
                                "Select one or more "
                                "families"
                            ),
                        ),
                    ],
                    style={
                        "marginBottom": "16px",
                    },
                ),

                html.Div(
                    [
                        html.Label(
                            "Select neurons"
                        ),

                        dcc.Dropdown(
                            id="neuron-dropdown",
                            options=all_neuron_options,
                            value=[],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            placeholder=(
                                "Select neurons to display"
                            ),
                        ),
                    ],
                ),

                html.Div(
                    id="selection-status",
                    style={
                        "marginTop": "12px",
                        "color": "#555",
                    },
                ),
            ],
            style={
                "width": "380px",
                "padding": "18px",
                "backgroundColor": "#f4f4f4",
                "borderRadius": "8px",
                "flexShrink": "0",
            },
        ),

        html.Div(
            [
                dcc.Graph(
                    id="neuron-graph",
                    figure=empty_figure(
                        "Select one or more neurons."
                    ),
                    style={
                        "height": "calc(100vh - 100px)",
                    },
                    config={
                        "displaylogo": False,
                        "scrollZoom": True,
                    },
                ),
            ],
            style={
                "flexGrow": "1",
                "minWidth": "0",
            },
        ),
    ],
    style={
        "display": "flex",
        "gap": "18px",
        "padding": "18px",
        "fontFamily": "Arial, sans-serif",
        "height": "100vh",
        "boxSizing": "border-box",
    },
)


# ----------------------------------------------------------------------
# Family filter callback
# ----------------------------------------------------------------------

@app.callback(
    Output(
        "neuron-dropdown",
        "options",
    ),
    Output(
        "neuron-dropdown",
        "value",
    ),
    Input(
        "family-dropdown",
        "value",
    ),
    Input(
        "neuron-dropdown",
        "value",
    ),
)
def update_neuron_dropdown(
    selected_families,
    selected_body_ids,
):
    selected_families = selected_families or []
    selected_body_ids = selected_body_ids or []

    if selected_families:
        filtered_neurons = neurons[
            neurons["family"].isin(
                selected_families
            )
        ]
    else:
        filtered_neurons = neurons

    options = make_dropdown_options(
        filtered_neurons
    )

    valid_body_ids = set(
        filtered_neurons["bodyId"]
        .astype(int)
        .tolist()
    )

    retained_body_ids = [
        int(body_id)
        for body_id in selected_body_ids
        if int(body_id) in valid_body_ids
    ]

    return options, retained_body_ids


# ----------------------------------------------------------------------
# Graph callback
# ----------------------------------------------------------------------

@app.callback(
    Output(
        "neuron-graph",
        "figure",
    ),
    Output(
        "selection-status",
        "children",
    ),
    Input(
        "neuron-dropdown",
        "value",
    ),
)
def update_graph(selected_body_ids):
    selected_body_ids = selected_body_ids or []

    if len(selected_body_ids) > MAX_SELECTED_NEURONS:
        return (
            empty_figure(
                f"Select no more than "
                f"{MAX_SELECTED_NEURONS} neurons."
            ),
            (
                f"Too many neurons selected: "
                f"{len(selected_body_ids)}"
            ),
        )

    figure = make_figure(
        selected_body_ids
    )

    status = (
        f"{len(selected_body_ids)} "
        f"neuron(s) selected"
    )

    return figure, status


# ----------------------------------------------------------------------
# Start application
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print(
        f"\nOpen this address in your browser:"
        f"\nhttp://{HOST}:{PORT}\n"
    )

    app.run(
        host=HOST,
        port=PORT,
        debug=True,
    )

