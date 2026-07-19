"""P2 real-source parsing and edge-independent benchmark construction."""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import zipfile
from dataclasses import dataclass

import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from threadpoolctl import threadpool_limits


@dataclass(frozen=True)
class PilotGraph:
    dataset_id: str
    external_ids: tuple[str, ...]
    public_features: sparse.csr_matrix
    edges: np.ndarray


@dataclass(frozen=True)
class PilotSplit:
    train_positive: np.ndarray
    train_negative: np.ndarray
    validation_positive: np.ndarray
    validation_negative: np.ndarray
    test_positive: np.ndarray
    test_negative: np.ndarray


def _canonicalize_edges(
    external_edges: list[tuple[str, str]], external_ids: tuple[str, ...]
) -> np.ndarray:
    lookup = {node: index for index, node in enumerate(external_ids)}
    canonical = {
        (min(lookup[left], lookup[right]), max(lookup[left], lookup[right]))
        for left, right in external_edges
        if left != right
    }
    result = np.asarray(sorted(canonical), dtype=np.int64)
    return result.reshape(-1, 2)


def load_blogcatalog(archive: pathlib.Path) -> PilotGraph:
    with zipfile.ZipFile(archive) as handle:
        prefix = "BlogCatalog-dataset/data/"

        def rows(name: str):
            with handle.open(prefix + name) as stream:
                yield from csv.reader(line.decode("utf-8").strip() for line in stream)

        external_ids = tuple(sorted((row[0] for row in rows("nodes.csv") if row)))
        groups = tuple(sorted((row[0] for row in rows("groups.csv") if row)))
        external_edges = [tuple(row[:2]) for row in rows("edges.csv") if row]
        memberships = [tuple(row[:2]) for row in rows("group-edges.csv") if row]

    node_lookup = {node: index for index, node in enumerate(external_ids)}
    group_lookup = {group: index for index, group in enumerate(groups)}
    feature_rows = [node_lookup[node] for node, _ in memberships]
    feature_columns = [group_lookup[group] for _, group in memberships]
    features = sparse.csr_matrix(
        (np.ones(len(memberships)), (feature_rows, feature_columns)),
        shape=(len(external_ids), len(groups)),
        dtype=np.float64,
    )
    return PilotGraph(
        dataset_id="blogcatalog-v3",
        external_ids=external_ids,
        public_features=features,
        edges=_canonicalize_edges(external_edges, external_ids),
    )


def load_facebook(directory: pathlib.Path) -> PilotGraph:
    with (directory / "facebook_target.csv").open(
        newline="", encoding="utf-8", errors="replace"
    ) as handle:
        target_rows = list(csv.DictReader(handle))
    external_ids = tuple(sorted(row["id"] for row in target_rows))
    node_lookup = {node: index for index, node in enumerate(external_ids)}

    raw_features = json.loads((directory / "facebook.json").read_text(encoding="utf-8"))
    dimension = max(index for values in raw_features.values() for index in values) + 1
    feature_rows: list[int] = []
    feature_columns: list[int] = []
    for node, indices in raw_features.items():
        feature_rows.extend([node_lookup[node]] * len(indices))
        feature_columns.extend(indices)

    categories = sorted({row["page_type"] for row in target_rows})
    category_lookup = {category: index for index, category in enumerate(categories)}
    for row in target_rows:
        feature_rows.append(node_lookup[row["id"]])
        feature_columns.append(dimension + category_lookup[row["page_type"]])
    features = sparse.csr_matrix(
        (np.ones(len(feature_rows)), (feature_rows, feature_columns)),
        shape=(len(external_ids), dimension + len(categories)),
        dtype=np.float64,
    )

    with (directory / "facebook_edges.csv").open(newline="", encoding="utf-8") as handle:
        external_edges = [
            (row["id_1"], row["id_2"]) for row in csv.DictReader(handle)
        ]
    return PilotGraph(
        dataset_id="facebook-musae",
        external_ids=external_ids,
        public_features=features,
        edges=_canonicalize_edges(external_edges, external_ids),
    )


def balanced_sha256_homes(
    dataset_id: str, external_ids: tuple[str, ...], *, clients: int, seed: int
) -> np.ndarray:
    if clients < 2 or len(external_ids) < clients:
        raise ValueError("clients must be between two and the node count")
    ranked = sorted(
        range(len(external_ids)),
        key=lambda index: hashlib.sha256(
            f"{dataset_id}|{seed}|{external_ids[index]}".encode()
        ).digest(),
    )
    homes = np.empty(len(external_ids), dtype=np.int64)
    homes[np.asarray(ranked)] = np.arange(len(ranked), dtype=np.int64) % clients
    return homes


def public_coarsening(
    features: sparse.csr_matrix,
    *,
    cells: int,
    components: int,
    random_state: int,
) -> np.ndarray:
    if features.shape[0] < cells or features.shape[1] < 2:
        raise ValueError("public coarsening requires enough nodes and descriptors")
    normalized = normalize(features, norm="l2", axis=1, copy=True)
    rank = min(components, features.shape[1] - 1, features.shape[0] - 1)
    projected = TruncatedSVD(
        n_components=rank, algorithm="randomized", random_state=random_state
    ).fit_transform(normalized)
    with threadpool_limits(limits=1):
        labels = KMeans(
            n_clusters=cells, n_init=20, random_state=random_state, algorithm="lloyd"
        ).fit_predict(projected)
    return labels.astype(np.int64)


def _split_count(size: int) -> tuple[int, int]:
    return int(np.floor(0.7 * size)), int(np.floor(0.1 * size))


def _sample_nonedges(
    *,
    nodes: int,
    homes: np.ndarray,
    existing: set[int],
    selected: set[int],
    count: int,
    cross: bool,
    rng: np.random.Generator,
) -> np.ndarray:
    pairs: list[tuple[int, int]] = []
    while len(pairs) < count:
        batch = max(1024, 3 * (count - len(pairs)))
        left = rng.integers(0, nodes, size=batch)
        right = rng.integers(0, nodes, size=batch)
        low = np.minimum(left, right)
        high = np.maximum(left, right)
        for u, v in zip(low, high, strict=True):
            if u == v or (homes[u] != homes[v]) != cross:
                continue
            key = int(u) * nodes + int(v)
            if key in existing or key in selected:
                continue
            selected.add(key)
            pairs.append((int(u), int(v)))
            if len(pairs) == count:
                break
    return np.asarray(pairs, dtype=np.int64).reshape(-1, 2)


def stratified_link_split(
    edges: np.ndarray, homes: np.ndarray, *, seed: int
) -> PilotSplit:
    edges = np.asarray(edges, dtype=np.int64)
    homes = np.asarray(homes, dtype=np.int64)
    if edges.ndim != 2 or edges.shape[1] != 2:
        raise ValueError("edges must have shape [m,2]")
    rng = np.random.default_rng(seed)
    positive_parts: dict[str, list[np.ndarray]] = {
        "train": [], "validation": [], "test": []
    }
    negative_parts: dict[str, list[np.ndarray]] = {
        "train": [], "validation": [], "test": []
    }
    node_count = len(homes)
    existing = {int(u) * node_count + int(v) for u, v in edges}
    selected: set[int] = set()

    for cross in (False, True):
        subset = edges[(homes[edges[:, 0]] != homes[edges[:, 1]]) == cross].copy()
        rng.shuffle(subset)
        train_end, validation_size = _split_count(len(subset))
        validation_end = train_end + validation_size
        splits = {
            "train": subset[:train_end],
            "validation": subset[train_end:validation_end],
            "test": subset[validation_end:],
        }
        for name, positives in splits.items():
            positive_parts[name].append(positives)
            negative_parts[name].append(
                _sample_nonedges(
                    nodes=node_count,
                    homes=homes,
                    existing=existing,
                    selected=selected,
                    count=len(positives),
                    cross=cross,
                    rng=rng,
                )
            )

    def merged(parts: dict[str, list[np.ndarray]], name: str) -> np.ndarray:
        result = np.concatenate(parts[name], axis=0)
        rng.shuffle(result)
        return result

    return PilotSplit(
        train_positive=merged(positive_parts, "train"),
        train_negative=merged(negative_parts, "train"),
        validation_positive=merged(positive_parts, "validation"),
        validation_negative=merged(negative_parts, "validation"),
        test_positive=merged(positive_parts, "test"),
        test_negative=merged(negative_parts, "test"),
    )
