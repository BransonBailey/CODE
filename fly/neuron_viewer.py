#!/usr/bin/env python3

"""Native GPU-accelerated neuPrint neuron viewer.

Uses VisPy/OpenGL for the 3D viewport and Qt for the desktop UI.
Skeleton geometry is never simplified or downsampled.
"""

import os
import pickle
import sys
from pathlib import Path

# VisPy + Qt OpenGL embedding is currently more reliable through XWayland/X11
# on Linux desktops running Wayland. Respect an explicit user choice.
if sys.platform.startswith("linux") and "QT_QPA_PLATFORM" not in os.environ:
    if os.environ.get("WAYLAND_DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
from functools import lru_cache

import navis
import pandas as pd
import numpy as np
from neuprint import Client, NeuronCriteria
import navis.interfaces.neuprint as neu

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QPushButton,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:
    raise RuntimeError(
        "PyQt5 is required. Install the viewer dependencies with:\n\n"
        "    pip install vispy PyQt5\n"
    ) from exc

try:
    from vispy import app as vispy_app
    from vispy import scene
    from vispy.color import Color
    from vispy.scene import visuals
except ImportError as exc:
    raise RuntimeError(
        "VisPy is required. Install the viewer dependencies with:\n\n"
        "    pip install vispy PyQt5\n"
    ) from exc


SERVER = "https://neuprint.janelia.org"
DATASET = "male-cns:v1.0"

HOST = "127.0.0.1"  # retained for compatibility with older configs
PORT = 8050         # retained for compatibility with older configs

MAX_SELECTED_NEURONS = 1_000_000
SKELETON_BATCH_SIZE = 250
METADATA_CACHE_VERSION = 1


# ----------------------------------------------------------------------
# Connect to neuPrint
# ----------------------------------------------------------------------

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
neu.set_default_client(client)


# ----------------------------------------------------------------------
# Persistent neuron metadata cache
# ----------------------------------------------------------------------

# Keep the existing skeleton cache location exactly as before.
SKELETON_CACHE_DIR = Path(
    os.environ.get(
        "NEURON_BROWSER_CACHE",
        "~/.cache/neuron_browser/skeletons",
    )
).expanduser()
SKELETON_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Store the neuron-list cache beside the skeleton directory. This preserves
# the existing ~/.cache/neuron_browser/ hierarchy without touching skeletons.
METADATA_CACHE_PATH = SKELETON_CACHE_DIR.parent / "neuron_metadata.pkl"


def load_cached_neuron_metadata():
    """Load metadata without contacting neuPrint when server/dataset match."""
    if not METADATA_CACHE_PATH.is_file():
        return None

    try:
        with METADATA_CACHE_PATH.open("rb") as file:
            payload = pickle.load(file)

        if payload.get("version") != METADATA_CACHE_VERSION:
            return None
        if payload.get("server") != SERVER:
            return None
        if payload.get("dataset") != DATASET:
            return None

        cached = payload.get("neurons")
        if not isinstance(cached, pd.DataFrame) or "bodyId" not in cached.columns:
            return None

        cached = cached.copy()
        cached["bodyId"] = cached["bodyId"].astype(int)
        return cached
    except (OSError, EOFError, pickle.PickleError, AttributeError,
            ImportError, ValueError, KeyError, TypeError):
        return None


def save_neuron_metadata(neurons):
    """Atomically write the neuron metadata cache."""
    METADATA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = METADATA_CACHE_PATH.with_suffix(".pkl.tmp")

    payload = {
        "version": METADATA_CACHE_VERSION,
        "server": SERVER,
        "dataset": DATASET,
        "neurons": neurons,
    }

    with temporary_path.open("wb") as file:
        pickle.dump(payload, file, protocol=pickle.HIGHEST_PROTOCOL)

    temporary_path.replace(METADATA_CACHE_PATH)


def fetch_neuron_metadata():
    print("Loading neuron list...")
    neurons = load_cached_neuron_metadata()

    if neurons is not None:
        print(f"  Loaded cached neuron list: {METADATA_CACHE_PATH}")
        print(f"  Neurons: {len(neurons):,}")
        return neurons

    print("  Metadata cache missing/stale; fetching from neuPrint...")
    result = neu.fetch_neurons(NeuronCriteria())

    if isinstance(result, tuple):
        neurons = result[0]
    else:
        neurons = result

    if neurons.empty:
        raise RuntimeError("neuPrint returned no neurons.")

    neurons = neurons.copy()
    neurons["bodyId"] = neurons["bodyId"].astype(int)
    save_neuron_metadata(neurons)
    print(f"  Saved neuron list: {METADATA_CACHE_PATH}")
    print(f"  Neurons: {len(neurons):,}")
    return neurons


neurons = fetch_neuron_metadata()


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
        "type", "instance", "class", "superclass", "subclass",
        "cellBodyFiber", "hemilineage", "somaNeuromere", "entryNerve",
        "exitNerve", "modality", "description",
    ]
    return " ".join(safe_text(row.get(field, "")) for field in fields).lower()


def classify_family(row):
    text = metadata_text(row)

    if any(word in text for word in [
        "optic", "visual", "lamina", "medulla", "lobula", "lobula plate", "ocellar",
    ]):
        return "Optical / visual"
    if any(word in text for word in [
        "sensory", "sens", "johnston", "mechanosens", "olfactory", "gustatory",
        "auditory", "proprio", "receptor",
    ]):
        return "Sensory"
    if any(word in text for word in ["motor", "motoneuron", "motor neuron"]):
        return "Motor"
    if any(word in text for word in ["descending", "dn"]):
        return "Descending"
    if any(word in text for word in ["ascending", "ascending neuron"]):
        return "Ascending"
    if any(word in text for word in ["projection", "pn"]):
        return "Projection"
    if any(word in text for word in ["local", "interneuron", "interneural"]):
        return "Local interneuron"
    if any(word in text for word in ["mushroom body", "kenyon", "mbon", "kc"]):
        return "Mushroom body"
    if any(word in text for word in [
        "central complex", "central-complex", "fan-shaped", "ellipsoid", "protocerebral bridge",
    ]):
        return "Central complex"
    return "Other / unclassified"


def make_neuron_label(row):
    body_id = int(row["bodyId"])
    neuron_type = safe_text(row.get("type", ""))
    instance = safe_text(row.get("instance", ""))
    family = safe_text(row.get("family", ""))

    label = f"bodyId {body_id}"
    if neuron_type:
        label += f" | type={neuron_type}"
    if instance and instance != neuron_type:
        label += f" | instance={instance}"
    if family:
        label += f" | [{family}]"
    return label


neurons["family"] = neurons.apply(classify_family, axis=1)
neurons["label"] = neurons.apply(make_neuron_label, axis=1)

family_values = sorted(neurons["family"].dropna().unique().tolist())


# ----------------------------------------------------------------------
# Persistent skeleton cache
# ----------------------------------------------------------------------

def skeleton_cache_path(body_id):
    return SKELETON_CACHE_DIR / f"{int(body_id)}.pkl"


def load_cached_skeleton(body_id):
    path = skeleton_cache_path(body_id)
    if not path.is_file():
        return None
    try:
        with path.open("rb") as file:
            return pickle.load(file)
    except (OSError, EOFError, pickle.PickleError, AttributeError,
            ImportError, ValueError):
        try:
            path.unlink()
        except OSError:
            pass
        return None


def save_cached_skeleton(skeleton):
    body_id = int(skeleton.id)
    path = skeleton_cache_path(body_id)
    temporary_path = path.with_suffix(".pkl.tmp")
    with temporary_path.open("wb") as file:
        pickle.dump(skeleton, file, protocol=pickle.HIGHEST_PROTOCOL)
    temporary_path.replace(path)


def preload_all_skeletons(body_ids, batch_size=SKELETON_BATCH_SIZE):
    body_ids = [int(body_id) for body_id in body_ids]
    missing = [body_id for body_id in body_ids if not skeleton_cache_path(body_id).is_file()]
    cached_count = len(body_ids) - len(missing)

    print("\nSkeleton cache:")
    print(f"  Location: {SKELETON_CACHE_DIR}")
    print(f"  Already cached: {cached_count:,} / {len(body_ids):,}")

    if not missing:
        print("  All skeletons are already downloaded.\n")
        return

    print(f"  Need to download: {len(missing):,}")
    print("  Downloading skeletons...\n")

    downloaded = 0
    for start in range(0, len(missing), batch_size):
        batch = missing[start:start + batch_size]
        skeletons = list(neu.fetch_skeletons(NeuronCriteria(bodyId=batch)))
        for skeleton in skeletons:
            save_cached_skeleton(skeleton)
            downloaded += 1

        total_cached = cached_count + downloaded
        print(
            f"  Cached: {total_cached:,} / {len(body_ids):,}"
            f" ({total_cached / len(body_ids) * 100:.1f}%)"
        )

    print("\nSkeleton cache is up to date.\n")


@lru_cache(maxsize=128)
def fetch_selected_skeletons(body_ids):
    body_ids = tuple(int(body_id) for body_id in body_ids)
    if not body_ids:
        return []

    skeletons = []
    missing = []
    for body_id in body_ids:
        skeleton = load_cached_skeleton(body_id)
        if skeleton is None:
            missing.append(body_id)
        else:
            skeletons.append(skeleton)

    if missing:
        print(f"Fetching {len(missing)} missing skeleton(s) from neuPrint...")
        fetched = list(neu.fetch_skeletons(NeuronCriteria(bodyId=list(missing))))
        for skeleton in fetched:
            save_cached_skeleton(skeleton)
            skeletons.append(skeleton)

    by_id = {int(skeleton.id): skeleton for skeleton in skeletons}
    return [by_id[body_id] for body_id in body_ids if body_id in by_id]


# Pre-download the complete skeleton set once, exactly as the prior viewer did.
preload_all_skeletons(neurons["bodyId"].astype(int).tolist())


# ----------------------------------------------------------------------
# VisPy/OpenGL renderer
# ----------------------------------------------------------------------

PALETTE = [
    "#e53935", "#1e88e5", "#fb8c00", "#8e24aa", "#00897b",
    "#fdd835", "#6d4c41", "#d81b60", "#43a047", "#3949ab",
]


def skeleton_segments(skeleton):
    """Return every parent-child edge as Nx2x3 float32 coordinates."""
    nodes = skeleton.nodes
    if nodes is None or nodes.empty:
        return None

    # itertuples avoids the expensive Series/DataFrame operations used by
    # the former Plotly path builder. We still retain every original edge.
    node_by_id = {int(row.node_id): row for row in nodes.itertuples()}
    segments = []

    for row in nodes.itertuples():
        try:
            parent_id = int(row.parent_id)
        except (TypeError, ValueError):
            continue
        if parent_id < 0 or parent_id not in node_by_id:
            continue

        parent = node_by_id[parent_id]
        segments.append((
            (float(parent.x), float(parent.y), float(parent.z)),
            (float(row.x), float(row.y), float(row.z)),
        ))

    if not segments:
        return None
    return segments


class NeuronCanvas(scene.SceneCanvas):
    """VisPy/OpenGL 3D canvas for complete neuron skeletons.

    The renderer intentionally keeps every parent-child skeleton edge. The
    geometry is packed into a single OpenGL LineVisual to minimize draw-call
    overhead. Camera framing is handled explicitly rather than through
    ``set_range`` so large neuPrint coordinate ranges cannot accidentally
    produce a clipped/empty view.
    """

    def __init__(self, parent=None):
        super().__init__(
            keys="interactive",
            bgcolor="#ffffff",
            parent=parent,
            size=(1000, 800),
            show=False,
            vsync=True,
        )
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(
            fov=45,
            distance=1000,
            elevation=30,
            azimuth=30,
            up="+z",
        )
        self.view.camera.interactive = True
        self.native.setMinimumSize(300, 300)

        # Keep the axis permanently present. It is intentionally not used for
        # camera bounds because it is an orientation aid, not scene geometry.
        self.axis_visual = visuals.XYZAxis(parent=self.view.scene)

        self.geometry_visual = None
        self.label_visual = None
        self.soma_visual = None
        self._scene_origin = None
        self._bounds = None

    def clear_scene(self):
        for attr in ("geometry_visual", "label_visual", "soma_visual"):
            visual = getattr(self, attr, None)
            if visual is not None:
                try:
                    visual.parent = None
                except Exception:
                    pass
                setattr(self, attr, None)
        self._scene_origin = None
        self._bounds = None
        self.update()

    @staticmethod
    def _rgba_from_palette(index):
        return np.asarray(Color(PALETTE[index % len(PALETTE)]).rgba, dtype=np.float32)

    def _frame_camera(self, minimum, maximum):
        """Frame geometry without relying on automatic scene-bound discovery."""
        center = (minimum + maximum) * 0.5
        extent = float(np.max(maximum - minimum))
        if not np.isfinite(extent) or extent <= 0:
            extent = 1.0

        # TurntableCamera uses scale_factor as its zoom/range measure. Set the
        # center and scale explicitly; this is more predictable for large 3D
        # biological coordinate systems than set_range().
        camera = self.view.camera
        camera.center = tuple(center.tolist())
        camera.scale_factor = extent * 1.20
        camera.distance = extent * 2.2
        camera.elevation = 30
        camera.azimuth = 30
        camera.roll = 0
        camera.update()

    def set_neurons(self, skeletons, labels_by_id, show_labels=False):
        import numpy as np

        self.clear_scene()
        if not skeletons:
            return 0, 0

        all_positions = []
        all_colors = []
        label_positions = []
        label_text = []
        label_colors = []
        total_segments = 0

        for index, skeleton in enumerate(skeletons):
            segments = skeleton_segments(skeleton)
            if not segments:
                continue

            color = self._rgba_from_palette(index)
            segment_array = np.asarray(segments, dtype=np.float32).reshape(-1, 3)
            if segment_array.size == 0 or not np.isfinite(segment_array).all():
                continue

            all_positions.append(segment_array)
            all_colors.append(
                np.repeat(color[None, :], segment_array.shape[0], axis=0)
            )
            total_segments += len(segments)

            body_id = int(skeleton.id)
            nodes = skeleton.nodes
            try:
                soma_rows = nodes.loc[nodes["parent_id"] < 0]
                if len(soma_rows):
                    soma = soma_rows.iloc[0]
                    anchor = np.array(
                        [float(soma.x), float(soma.y), float(soma.z)],
                        dtype=np.float32,
                    )
                else:
                    anchor = segment_array.mean(axis=0)
            except (IndexError, KeyError, TypeError, ValueError):
                anchor = segment_array.mean(axis=0)

            label_positions.append(anchor)
            label_text.append(labels_by_id.get(body_id, f"bodyId {body_id}"))
            label_colors.append(color)

        if not all_positions:
            return 0, 0

        positions = np.concatenate(all_positions, axis=0).astype(np.float32, copy=False)
        colors = np.concatenate(all_colors, axis=0).astype(np.float32, copy=False)
        label_positions = np.asarray(label_positions, dtype=np.float32)
        label_colors = np.asarray(label_colors, dtype=np.float32)

        # Translate all coordinates around their global center. This preserves
        # every relative coordinate exactly while avoiding large absolute
        # values in the GPU transform pipeline.
        scene_origin = (positions.min(axis=0) + positions.max(axis=0)) * 0.5
        positions = positions - scene_origin
        label_positions = label_positions - scene_origin
        self._scene_origin = scene_origin

        minimum = positions.min(axis=0)
        maximum = positions.max(axis=0)
        self._bounds = (minimum, maximum)

        # IMPORTANT: create geometry first. Labels are added only after the
        # OpenGL line visual exists, so a text backend problem can never remove
        # the neuron geometry from the scene.
        self.geometry_visual = visuals.Line(
            pos=positions,
            color=colors,
            width=1.0,
            connect="segments",
            method="gl",
            antialias=False,
            parent=self.view.scene,
        )

        # Add soma markers as a lightweight visual. Besides being useful
        # visually, this provides an immediate GPU-rendered point at each
        # neuron's label anchor.
        self.soma_visual = visuals.Markers(
            pos=label_positions,
            size=6,
            face_color=label_colors,
            edge_width=0,
            scaling="fixed",
            parent=self.view.scene,
        )

        # Text labels are optional because they add rendering overhead and can
        # make dense neuron selections harder to read.
        if show_labels:
            try:
                self.label_visual = visuals.Text(
                    text=label_text,
                    pos=label_positions,
                    color="black",
                    font_size=10,
                    anchor_x="left",
                    anchor_y="center",
                    scaling=False,
                    parent=self.view.scene,
                )
            except Exception as exc:
                # Geometry must remain usable even if a platform's text backend
                # rejects the multi-label visual.
                print(f"Warning: neuron labels disabled: {exc}")
                self.label_visual = None

        self._frame_camera(minimum, maximum)
        self.update()
        self.native.update()
        self.native.repaint()

        print(
            f"Rendered {len(label_text):,} neuron(s), "
            f"{total_segments:,} full-resolution skeleton segments"
            + (" with labels." if show_labels else ".")
        )
        return len(label_text), total_segments


# ----------------------------------------------------------------------
# Native Qt application
# ----------------------------------------------------------------------

class NeuronViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NeuPrint Neuron Viewer — {DATASET}")
        self.resize(1600, 950)

        self.labels_by_id = dict(zip(
            neurons["bodyId"].astype(int),
            neurons["label"].astype(str),
        ))
        self.current_filtered_ids = neurons["bodyId"].astype(int).tolist()
        self.selected_ids = set()
        self._updating_list = False

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        controls = QWidget()
        controls.setMinimumWidth(390)
        controls.setMaximumWidth(500)
        controls_layout = QVBoxLayout(controls)

        title = QLabel("NeuPrint Neuron Viewer")
        title.setFont(QFont("Sans Serif", 16, QFont.Bold))
        controls_layout.addWidget(title)

        dataset_label = QLabel(f"Dataset: {DATASET}\nNeurons: {len(neurons):,}")
        dataset_label.setStyleSheet("color: #666;")
        controls_layout.addWidget(dataset_label)

        controls_layout.addWidget(QLabel("Filter by family"))
        self.family_combo = QComboBox()
        self.family_combo.addItem("All families", "__all__")
        for family in family_values:
            self.family_combo.addItem(family, family)
        self.family_combo.currentIndexChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.family_combo)

        controls_layout.addWidget(QLabel("Search neurons"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("bodyId, type, instance, family...")
        self.search.textChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.search)

        self.show_labels_checkbox = QCheckBox("Show neuron labels")
        self.show_labels_checkbox.setChecked(False)
        self.show_labels_checkbox.setToolTip(
            "Render one text label per selected neuron. Disabling labels can "
            "improve rendering speed and reduce visual clutter."
        )
        self.show_labels_checkbox.toggled.connect(self.render_selection)
        controls_layout.addWidget(self.show_labels_checkbox)

        button_row = QHBoxLayout()
        self.select_all_button = QPushButton("Select all filtered")
        self.select_all_button.clicked.connect(self.select_all_filtered)
        button_row.addWidget(self.select_all_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_selection)
        button_row.addWidget(self.clear_button)
        controls_layout.addLayout(button_row)

        self.neuron_list = QListWidget()
        self.neuron_list.setSelectionMode(QListWidget.NoSelection)
        self.neuron_list.itemChanged.connect(self.on_item_changed)
        controls_layout.addWidget(self.neuron_list, stretch=1)

        self.status = QLabel("0 neurons selected")
        self.status.setStyleSheet("color: #555;")
        controls_layout.addWidget(self.status)

        splitter.addWidget(controls)

        self.canvas = NeuronCanvas()
        splitter.addWidget(self.canvas.native)
        splitter.setSizes([420, 1180])

        self.populate_list()

    def apply_filters(self):
        family = self.family_combo.currentData()
        query = self.search.text().strip().lower()

        data = neurons
        if family != "__all__":
            data = data[data["family"] == family]

        if query:
            mask = data["label"].str.lower().str.contains(query, regex=False, na=False)
            data = data[mask]

        self.current_filtered_ids = data["bodyId"].astype(int).tolist()
        self.populate_list()

    def populate_list(self):
        self._updating_list = True
        try:
            self.neuron_list.clear()
            ids = self.current_filtered_ids
            # QListWidget remains virtual enough for normal neuPrint lists, but
            # avoid building an enormous widget when filtering is empty.
            for body_id in ids:
                item = QListWidgetItem(self.labels_by_id[int(body_id)])
                item.setData(Qt.UserRole, int(body_id))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.Checked if int(body_id) in self.selected_ids
                    else Qt.Unchecked
                )
                self.neuron_list.addItem(item)
        finally:
            self._updating_list = False
        self.update_status()

    def on_item_changed(self, item):
        if self._updating_list:
            return
        body_id = int(item.data(Qt.UserRole))
        if item.checkState() == Qt.Checked:
            self.selected_ids.add(body_id)
        else:
            self.selected_ids.discard(body_id)
        self.render_selection()

    def select_all_filtered(self):
        if len(self.selected_ids) + len(self.current_filtered_ids) > MAX_SELECTED_NEURONS:
            self.status.setText(f"Selection exceeds {MAX_SELECTED_NEURONS:,} neurons")
            return
        self.selected_ids.update(self.current_filtered_ids)
        self.populate_list()
        self.render_selection()

    def clear_selection(self):
        self.selected_ids.clear()
        self.populate_list()
        self.render_selection()

    def update_status(self):
        self.status.setText(
            f"{len(self.selected_ids):,} neuron(s) selected | "
            f"{len(self.current_filtered_ids):,} shown"
        )

    def render_selection(self):
        self.update_status()
        if not self.selected_ids:
            self.canvas.clear_scene()
            self.canvas.update()
            return

        if len(self.selected_ids) > MAX_SELECTED_NEURONS:
            return

        body_ids = tuple(sorted(self.selected_ids))
        skeletons = fetch_selected_skeletons(body_ids)
        self.canvas.set_neurons(
            skeletons,
            self.labels_by_id,
            show_labels=self.show_labels_checkbox.isChecked(),
        )


# ----------------------------------------------------------------------
# Start application
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Use VisPy's Qt6 backend explicitly so its OpenGL canvas shares the same
    # Qt event loop as the application controls.
    vispy_app.use_app("pyqt5")
    app = QApplication(sys.argv)
    print(f"Qt platform: {os.environ.get('QT_QPA_PLATFORM', 'default')}")
    print(f"VisPy backend: {vispy_app.use_app()}" )
    app.setApplicationName("NeuPrint Neuron Viewer")
    window = NeuronViewerWindow()
    window.show()
    window.canvas.update()
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(100, window.canvas.update)
    sys.exit(app.exec())

