"""Frozen P3 public data views and source routing."""

from __future__ import annotations

import pathlib

import numpy as np

from .p2_data import (
    PilotGraph,
    label_hash_subcells,
    load_blogcatalog,
    load_deezer_europe,
    load_facebook,
    load_github_social,
    load_lastfm,
    load_polblogs,
    public_coarsening,
)


def load_p3_graph(raw_root: pathlib.Path, dataset: str) -> PilotGraph:
    if dataset == "blogcatalog-v3":
        return load_blogcatalog(raw_root / dataset / "blogcatalog-v3.zip")
    if dataset == "facebook-musae":
        return load_facebook(raw_root / dataset, include_target_features=False)
    if dataset == "polblogs-newman":
        return load_polblogs(raw_root / dataset / f"{dataset}.zip")
    if dataset == "lastfm-asia-snap":
        return load_lastfm(
            raw_root / dataset / f"{dataset}.zip", include_target_features=False
        )
    if dataset == "github-social-snap":
        return load_github_social(raw_root / dataset / f"{dataset}.zip")
    if dataset == "deezer-europe-snap":
        return load_deezer_europe(raw_root / dataset / f"{dataset}.zip")
    raise ValueError(f"unsupported P3 dataset: {dataset}")


def p3_public_cells(graph: PilotGraph, dataset: str, config: dict) -> np.ndarray:
    coarsening = config["public_coarsening"]
    if dataset == "polblogs-newman":
        special = coarsening[dataset]
        if graph.public_labels is None:
            raise ValueError("PolBlogs requires its registered public labels")
        return label_hash_subcells(
            dataset,
            graph.external_ids,
            graph.public_labels,
            subcells_per_label=special["subcells_per_label"],
            seed=config["home_assignment"]["seed"],
        )
    default = coarsening["default"]
    return public_coarsening(
        graph.public_features,
        cells=default["cells"],
        components=default["components"],
        random_state=default["random_state"],
    )
