import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_p5fc_registry_excludes_labels_and_upstream_roles():
    registry = json.loads(
        (ROOT / "data/p5fc_source_registry.json").read_text(encoding="utf-8")
    )
    assert {item["id"] for item in registry["datasets"]} == {
        "flickr-graphsaint",
        "reddit2-graphsaint",
    }
    for dataset in registry["datasets"]:
        assert {item["path"] for item in dataset["files"]} == {
            "adj_full.npz",
            "feats.npy",
        }
        allowlisted = {item["google_drive_id"] for item in dataset["files"]}
        assert allowlisted.isdisjoint(dataset["prohibited_google_drive_ids"])
