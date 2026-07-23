"""Run the frozen R5 graph-phase confirmatory test exactly once."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
from cryptography.fernet import Fernet

from fed_dp_lp.accounting import (
    DEFAULT_ORDERS,
    calibrate_gaussian,
    epsilon_from_rdp,
)
from fed_dp_lp.gap_adaptation import (
    client_owned_edges,
    public_svd_encoder,
    release_private_aggregations,
    score_pairs_from_channels,
    undirected_adjacency,
)
from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)
from fed_dp_lp.p2_sealing import array_commitment
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.private_certificate import certificate_lower_bound
from fed_dp_lp.r5_holdout import (
    certification_mask,
    corrupted_pairs,
    finite_population_penalty,
    ranking_advantage,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/r5_graph_phase_confirmatory.json"
P3_MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
P3_SELECTION_PATH = ROOT / "results/p3_gap_validation/summary.json"
SOURCE_CONTRACT_PATH = ROOT / "data/manifests/p3_source_contract.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
SEALED = ROOT / "data/sealed/p3_benchmark"
OUTPUT = ROOT / "results/r5_graph_phase_confirmatory"
ACCESS = OUTPUT / "access.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def require_clean_worktree() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    ).strip()
    if status:
        raise SystemExit("refusing one-time R5 test from a dirty worktree")


def load_protocol_state() -> tuple[dict, dict, dict, dict]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    master = json.loads(P3_MASTER_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if config["datasets"] != master["datasets"]:
        raise RuntimeError("R5 and P3 dataset orders differ")
    if config["seeds"] != master["split"]["seeds"]:
        raise RuntimeError("R5 and P3 seed orders differ")
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise RuntimeError("P3 split audit is not clean")
    if (
        manifest["test_status"] != "encrypted_never_accessed"
        or manifest["test_access_count"] != 0
    ):
        raise RuntimeError("P3 sealed holdout is not untouched")
    return config, master, manifest, split_audit


def manifest_lookup(manifest: dict) -> dict[tuple[str, int], dict]:
    return {
        (dataset["dataset"], int(record["seed"])): record
        for dataset in manifest["datasets"]
        for record in dataset["splits"]
    }


def verify_sealed_payloads(config: dict, records: dict) -> None:
    for dataset in config["datasets"]:
        for seed in config["seeds"]:
            path = SEALED / f"{dataset}_seed_{seed}.fernet"
            expected = records[(dataset, seed)]["commitments"][
                "sealed_payload_sha256"
            ]
            if not path.exists() or sha256(path) != expected:
                raise RuntimeError(f"sealed payload hash mismatch: {dataset}/{seed}")


def unseal(
    dataset: str,
    seed: int,
    record: dict,
    cipher: Fernet,
    commitment_key: bytes,
) -> tuple[np.ndarray, np.ndarray]:
    path = SEALED / f"{dataset}_seed_{seed}.fernet"
    plaintext = cipher.decrypt(path.read_bytes())
    with np.load(io.BytesIO(plaintext), allow_pickle=False) as payload:
        positive = payload["test_positive"]
        negative = payload["test_negative"]
    for name, values in (("test_positive", positive), ("test_negative", negative)):
        observed = array_commitment(
            commitment_key, f"{dataset}|{seed}|{name}", values
        )
        if observed != record["commitments"][name]:
            raise RuntimeError(f"commitment mismatch: {dataset}/{seed}/{name}")
    return positive, negative


def training_calibration(config: dict, epsilon: float, hops: int):
    return calibrate_gaussian(
        target_epsilon=epsilon,
        delta=config["privacy"]["delta_training"],
        sensitivity=config["privacy"]["training_sensitivity_per_hop"],
        steps=hops,
        orders=DEFAULT_ORDERS,
    )


def certification_calibration(config: dict, epsilon: float):
    return calibrate_gaussian(
        target_epsilon=epsilon,
        delta=config["privacy"]["delta_certification"],
        sensitivity=config["privacy"]["certification_l2_sensitivity"],
        steps=1,
        orders=DEFAULT_ORDERS,
    )


def composed_privacy(training, certification, config: dict) -> dict:
    combined = np.asarray(training.rdp) + np.asarray(certification.rdp)
    delta = (
        config["privacy"]["delta_training"]
        + config["privacy"]["delta_certification"]
    )
    epsilon, order = epsilon_from_rdp(DEFAULT_ORDERS, combined, delta=delta)
    return {
        "epsilon": epsilon,
        "delta": delta,
        "selected_order": order,
        "orders": [float(value) for value in DEFAULT_ORDERS],
        "rdp": [float(value) for value in combined],
        "composition": "sequential_training_plus_certification",
    }


def private_certificate_release(
    values: np.ndarray,
    owners: np.ndarray,
    *,
    clients: int,
    calibration,
    visibility: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, float, int]:
    local = np.zeros((clients, 2), dtype=np.float64)
    np.add.at(local[:, 0], owners, values)
    np.add.at(local[:, 1], owners, 1.0)
    if visibility == "visible_messages":
        messages = local + rng.normal(
            0.0, calibration.noise_std, size=local.shape
        )
        return messages.sum(axis=0), calibration.noise_std * np.sqrt(clients), clients
    if visibility == "ideal_secagg":
        aggregate = local.sum(axis=0) + rng.normal(
            0.0, calibration.noise_std, size=2
        )
        return aggregate, calibration.noise_std, 1
    raise ValueError("unknown visibility model")


def scoped_auc(
    positive: np.ndarray,
    negative: np.ndarray,
    positive_scores: np.ndarray,
    negative_scores: np.ndarray,
    homes: np.ndarray,
) -> dict[str, float]:
    pairs, labels = candidate_arrays(positive, negative)
    scores = np.concatenate([positive_scores, negative_scores])
    return evaluate_scores(labels, scores, metric_masks(pairs, homes))


def write_jsonl(path: pathlib.Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def is_primary(record: dict, config: dict) -> bool:
    primary = config["confirmatory_primary_cell"]
    return (
        record["training_epsilon_target"] == primary["training_epsilon"]
        and record["certification_epsilon_target"]
        == primary["certification_epsilon"]
        and record["visibility"] == primary["visibility"]
    )


def summarize(records: list[dict], config: dict, provenance: dict) -> dict:
    primary = [record for record in records if record["confirmatory_primary"]]
    activated = [record for record in primary if record["activated"]]
    false_activations = [
        record for record in activated
        if record["full_holdout_pairwise_advantage"]
        < config["certificate"]["material_gain_gamma"]
    ]
    mean_policy_gain = float(
        np.mean([record["q5_policy_pairwise_gain"] for record in primary])
    )
    gates = {
        "primary_record_count": (
            len(primary) == config["confirmatory_primary_cell"]["records"]
        ),
        "maximum_false_material_activations": (
            len(false_activations)
            <= config["decision_gates"]["maximum_false_material_activations"]
        ),
        "minimum_activated_primary_cells": (
            len(activated)
            >= config["decision_gates"]["minimum_activated_primary_cells"]
        ),
        "minimum_activated_datasets": (
            len({record["dataset"] for record in activated})
            >= config["decision_gates"]["minimum_activated_datasets"]
        ),
        "minimum_mean_Q5_policy_gain": (
            mean_policy_gain
            >= config["decision_gates"]["minimum_mean_Q5_policy_gain"]
        ),
        "all_privacy_accountants_reproduced": all(
            record["accountant_reproduced"] for record in records
        ),
        "all_commitments_verified": provenance["all_commitments_verified"],
        "single_test_access": provenance["test_access_count"] == 1,
        "no_test_tuning": provenance["test_tuning"] is False,
    }
    safety_keys = {
        "primary_record_count",
        "maximum_false_material_activations",
        "all_privacy_accountants_reproduced",
        "all_commitments_verified",
        "single_test_access",
        "no_test_tuning",
    }
    safety_pass = all(gates[key] for key in safety_keys)
    nonvacuity_pass = all(gates.values())
    labels = config["decision_labels"]
    decision = (
        labels["pass"]
        if nonvacuity_pass
        else labels["safe_abstention"]
        if safety_pass
        else labels["fail"]
    )
    cells = {}
    for training_epsilon in config["privacy"]["training_epsilon_grid"]:
        for certification_epsilon in config["privacy"][
            "certification_epsilon_grid"
        ]:
            for visibility in config["privacy"]["visibility_models"]:
                subset = [
                    record for record in records
                    if record["training_epsilon_target"] == training_epsilon
                    and record["certification_epsilon_target"]
                    == certification_epsilon
                    and record["visibility"] == visibility
                ]
                key = f"train={training_epsilon}/cert={certification_epsilon}/{visibility}"
                active = [record for record in subset if record["activated"]]
                cells[key] = {
                    "records": len(subset),
                    "activated": len(active),
                    "activated_datasets": len(
                        {record["dataset"] for record in active}
                    ),
                    "false_material_activations": sum(
                        record["activated"]
                        and record["full_holdout_pairwise_advantage"]
                        < config["certificate"]["material_gain_gamma"]
                        for record in subset
                    ),
                    "mean_q5_policy_gain": float(
                        np.mean(
                            [record["q5_policy_pairwise_gain"] for record in subset]
                        )
                    ),
                }
    return {
        "protocol": config["protocol"],
        "decision": decision,
        "test_accessed": True,
        "provenance": provenance,
        "primary": {
            "records": len(primary),
            "activated": len(activated),
            "activated_datasets": sorted(
                {record["dataset"] for record in activated}
            ),
            "false_material_activations": len(false_activations),
            "mean_q5_policy_gain": mean_policy_gain,
        },
        "gates": gates,
        "diagnostic_cells": cells,
    }


def preflight() -> None:
    config, _, manifest, _ = load_protocol_state()
    records = manifest_lookup(manifest)
    verify_sealed_payloads(config, records)
    selection = json.loads(P3_SELECTION_PATH.read_text(encoding="utf-8"))
    observed = {
        dataset: {
            "projection_dimension": int(values["selected"]["projection_dimension"]),
            "hops": int(values["selected"]["hops"]),
        }
        for dataset, values in selection["selections"].items()
    }
    if observed != config["candidate"]["selected_validation_hyperparameters"]:
        raise RuntimeError("frozen candidate differs from validation selection")
    for dataset in config["datasets"]:
        graph = load_p3_graph(RAW, dataset)
        with np.load(
            PROCESSED / dataset / "public_layout.npz", allow_pickle=False
        ) as source:
            if len(source["homes"]) != graph.public_features.shape[0]:
                raise RuntimeError(f"layout mismatch: {dataset}")
        for seed in config["seeds"]:
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as source:
                if len(source["train_positive"]) == 0:
                    raise RuntimeError(f"empty train split: {dataset}/{seed}")
    print("R5 preflight PASS; sealed tests were hash-checked but not decrypted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute-frozen-test-once", action="store_true")
    args = parser.parse_args()
    if args.preflight == args.execute_frozen_test_once:
        raise SystemExit("select exactly one R5 execution mode")
    if args.preflight:
        preflight()
        return

    require_clean_worktree()
    if OUTPUT.exists():
        raise SystemExit("R5 output/access state exists; refusing a second test access")
    config, master, manifest, split_audit = load_protocol_state()
    manifest_records = manifest_lookup(manifest)
    verify_sealed_payloads(config, manifest_records)
    commit = git_head()

    OUTPUT.mkdir(parents=True)
    access = {
        "protocol": config["protocol"],
        "accessed_utc": datetime.now(timezone.utc).isoformat(),
        "test_access_count": 1,
        "runner_commit": commit,
        "config_sha256": sha256(CONFIG_PATH),
        "p3_master_sha256": sha256(P3_MASTER_PATH),
        "p3_selection_sha256": sha256(P3_SELECTION_PATH),
        "source_contract_sha256": sha256(SOURCE_CONTRACT_PATH),
        "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
        "split_audit_sha256": sha256(SPLIT_AUDIT_PATH),
    }
    ACCESS.write_text(json.dumps(access, indent=2) + "\n", encoding="utf-8")

    cipher = Fernet((SEALED / "test.key").read_bytes())
    commitment_key = (SEALED / "commitment.key").read_bytes()
    records = []
    all_commitments_verified = True

    for dataset_index, dataset in enumerate(config["datasets"]):
        print(f"[{dataset}] loading frozen graph and encoder", flush=True)
        graph = load_p3_graph(RAW, dataset)
        selected = config["candidate"]["selected_validation_hyperparameters"][
            dataset
        ]
        dimension = selected["projection_dimension"]
        hops = selected["hops"]
        encoded = public_svd_encoder(
            graph.public_features,
            dimension=dimension,
            random_state=20260724 + dimension,
        )
        with np.load(
            PROCESSED / dataset / "public_layout.npz", allow_pickle=False
        ) as source:
            homes = source["homes"]

        for seed_index, seed in enumerate(config["seeds"]):
            print(f"[{dataset}] seed={seed}", flush=True)
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as source:
                train_positive = source["train_positive"]
            test_positive, test_negative = unseal(
                dataset,
                seed,
                manifest_records[(dataset, seed)],
                cipher,
                commitment_key,
            )
            cert_mask = certification_mask(
                test_positive,
                nodes=len(homes),
                dataset=dataset,
                seed=seed,
                salt=config["sealed_holdout_partition"]["assignment_salt"],
                probability=config["sealed_holdout_partition"][
                    "certification_probability"
                ],
            )
            negative_cert_mask = certification_mask(
                test_negative,
                nodes=len(homes),
                dataset=dataset,
                seed=seed,
                salt=config["sealed_holdout_partition"][
                    "negative_evaluation_assignment_salt"
                ],
                probability=config["sealed_holdout_partition"][
                    "certification_probability"
                ],
            )
            q_negative = test_negative[~negative_cert_mask]
            corrupted = corrupted_pairs(
                test_positive,
                nodes=len(homes),
                dataset=dataset,
                seed=seed,
                salt=config["sealed_holdout_partition"]["corruption_salt"],
            )
            all_pairs = np.row_stack([test_positive, corrupted, q_negative])
            public_all = sparse_cosine_scores(graph.public_features, all_pairs)
            n_positive = len(test_positive)
            public_positive = public_all[:n_positive]
            public_corrupted = public_all[n_positive : 2 * n_positive]
            public_q_negative = public_all[2 * n_positive :]
            local_edges = client_owned_edges(
                train_positive, homes, clients=master["clients"]
            )
            adjacency = undirected_adjacency(local_edges, len(homes))

            for training_index, training_epsilon in enumerate(
                config["privacy"]["training_epsilon_grid"]
            ):
                train_calibration = training_calibration(
                    config, training_epsilon, hops
                )
                for visibility in config["privacy"]["visibility_models"]:
                    train_stream = config["rng_streams"][
                        f"training_{visibility}"
                    ]
                    train_rng = np.random.default_rng(
                        np.random.SeedSequence(
                            [
                                train_stream,
                                dataset_index,
                                seed_index,
                                training_index,
                                dimension,
                                hops,
                            ]
                        )
                    )
                    channels = release_private_aggregations(
                        local_edges,
                        encoded,
                        hops=hops,
                        noise_std=train_calibration.noise_std,
                        visibility=visibility,
                        rng=train_rng,
                        adjacency=adjacency,
                    )
                    candidate_all = score_pairs_from_channels(channels, all_pairs)
                    candidate_positive = candidate_all[:n_positive]
                    candidate_corrupted = candidate_all[
                        n_positive : 2 * n_positive
                    ]
                    candidate_q_negative = candidate_all[2 * n_positive :]
                    advantages = ranking_advantage(
                        candidate_positive,
                        candidate_corrupted,
                        public_positive,
                        public_corrupted,
                    )
                    full_advantage = float(np.mean(advantages))
                    cert_values = advantages[cert_mask]
                    q_values = advantages[~cert_mask]
                    cert_edges = test_positive[cert_mask]
                    cert_owners = homes[cert_edges[:, 0]]
                    public_auc = scoped_auc(
                        test_positive[~cert_mask],
                        q_negative,
                        public_positive[~cert_mask],
                        public_q_negative,
                        homes,
                    )
                    candidate_auc = scoped_auc(
                        test_positive[~cert_mask],
                        q_negative,
                        candidate_positive[~cert_mask],
                        candidate_q_negative,
                        homes,
                    )

                    for certification_index, certification_epsilon in enumerate(
                        config["privacy"]["certification_epsilon_grid"]
                    ):
                        cert_calibration = certification_calibration(
                            config, certification_epsilon
                        )
                        cert_stream = config["rng_streams"][
                            f"certification_{visibility}"
                        ]
                        cert_rng = np.random.default_rng(
                            np.random.SeedSequence(
                                [
                                    cert_stream,
                                    dataset_index,
                                    seed_index,
                                    training_index,
                                    certification_index,
                                ]
                            )
                        )
                        noisy_query, coordinate_std, messages = (
                            private_certificate_release(
                                cert_values,
                                cert_owners,
                                clients=master["clients"],
                                calibration=cert_calibration,
                                visibility=visibility,
                                rng=cert_rng,
                            )
                        )
                        allocation = config["certificate"]["failure_allocation"]
                        certificate = certificate_lower_bound(
                            np.asarray([noisy_query[0]]),
                            np.asarray([noisy_query[1]]),
                            coordinate_noise_std=coordinate_std,
                            beta_sum=allocation["sum_noise"],
                            beta_count=allocation["count_noise"],
                            beta_sampling=allocation[
                                "finite_population_sampling"
                            ],
                            dependence_factor=1.0,
                            minimum_count_lower=config["certificate"][
                                "minimum_noisy_count_lower"
                            ],
                        )
                        lower = float(certificate.lower_bound[0])
                        activated = bool(
                            certificate.valid[0]
                            and lower
                            >= config["certificate"]["material_gain_gamma"]
                        )
                        total_privacy = composed_privacy(
                            train_calibration, cert_calibration, config
                        )
                        reproduced, _ = epsilon_from_rdp(
                            np.asarray(total_privacy["orders"]),
                            np.asarray(total_privacy["rdp"]),
                            delta=total_privacy["delta"],
                        )
                        record = {
                            "protocol": config["protocol"],
                            "code_commit": commit,
                            "dataset": dataset,
                            "seed": seed,
                            "training_epsilon_target": training_epsilon,
                            "certification_epsilon_target": certification_epsilon,
                            "visibility": visibility,
                            "confirmatory_primary": False,
                            "test_access_count": 1,
                            "test_tuning": False,
                            "candidate_label": config["candidate"]["label"],
                            "official_reproduction": False,
                            "projection_dimension": dimension,
                            "hops": hops,
                            "client_count": master["clients"],
                            "train_edge_count": len(train_positive),
                            "certification_count": int(np.sum(cert_mask)),
                            "evaluation_positive_count": int(np.sum(~cert_mask)),
                            "evaluation_negative_count": len(q_negative),
                            "training_privacy": asdict(train_calibration),
                            "certification_privacy": asdict(cert_calibration),
                            "composed_privacy": total_privacy,
                            "accountant_reproduced": bool(
                                np.isclose(
                                    reproduced,
                                    total_privacy["epsilon"],
                                    rtol=0.0,
                                    atol=1e-12,
                                )
                            ),
                            "certification_message_count": messages,
                            "certification_coordinate_noise_std": coordinate_std,
                            "certificate_valid": bool(certificate.valid[0]),
                            "certificate_lower_bound": lower,
                            "activated": activated,
                            "certification_empirical_advantage": float(
                                np.mean(cert_values)
                            ),
                            "q5_pairwise_advantage": float(np.mean(q_values)),
                            "full_holdout_pairwise_advantage": full_advantage,
                            "q5_policy_pairwise_gain": (
                                float(np.mean(q_values)) if activated else 0.0
                            ),
                            "finite_population_penalty_audit_only": (
                                finite_population_penalty(
                                    len(cert_values),
                                    len(test_positive),
                                    failure_probability=allocation[
                                        "finite_population_sampling"
                                    ],
                                )
                            ),
                            "roc_auc": {
                                "public": public_auc,
                                "candidate": candidate_auc,
                                "policy": candidate_auc if activated else public_auc,
                                "candidate_gain_over_public": {
                                    scope: candidate_auc[scope] - public_auc[scope]
                                    for scope in ("global", "intra", "cross")
                                },
                            },
                        }
                        record["confirmatory_primary"] = is_primary(record, config)
                        records.append(record)

    provenance = {
        **access,
        "test_access_count": 1,
        "test_tuning": False,
        "all_commitments_verified": all_commitments_verified,
        "split_audit_status": split_audit["status"],
        "record_count": len(records),
    }
    summary = summarize(records, config, provenance)
    write_jsonl(OUTPUT / "records.jsonl", records)
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary["primary"], indent=2), flush=True)
    print(summary["decision"], flush=True)


if __name__ == "__main__":
    main()
