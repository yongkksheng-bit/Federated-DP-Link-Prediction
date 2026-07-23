"""Build publication figures directly from frozen R5 evidence."""

from __future__ import annotations

import json
import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORDS = ROOT / "results/r5_graph_phase_confirmatory/records.jsonl"
SUMMARY = ROOT / "results/r5_graph_phase_confirmatory/summary.json"
OUTPUT = ROOT / "manuscript/figures"

BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#D55E00"
SKY = "#56B4E9"
GRAY = "#6B7280"
LIGHT = "#F5F7FA"
DARK = "#1F2937"


def style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9.5,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.6,
            "savefig.dpi": 320,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUTPUT / f"{name}.pdf",
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    fig.savefig(OUTPUT / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def box(ax, xy, width, height, title, detail, color, *, fill="#FFFFFF"):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        linewidth=1.3,
        edgecolor=color,
        facecolor=fill,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height * 0.64,
        title,
        ha="center",
        va="center",
        color=DARK,
        fontweight="bold",
        fontsize=9,
    )
    ax.text(
        xy[0] + width / 2,
        xy[1] + height * 0.30,
        detail,
        ha="center",
        va="center",
        color=GRAY,
        fontsize=7.5,
    )
    return patch


def arrow(ax, start, end, color=GRAY, *, style="-|>", width=1.2):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=10,
            linewidth=width,
            color=color,
            connectionstyle="arc3,rad=0",
        )
    )


def overview() -> None:
    fig, ax = plt.subplots(figsize=(7.16, 2.85))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box(
        ax,
        (0.02, 0.59),
        0.16,
        0.25,
        "Private train edges",
        r"$E^T_1,\ldots,E^T_K$",
        BLUE,
        fill="#EEF7FC",
    )
    box(
        ax,
        (0.02, 0.16),
        0.16,
        0.25,
        "Public descriptors",
        r"$X,\ h,\ (u,v)$",
        GRAY,
        fill=LIGHT,
    )
    box(
        ax,
        (0.26, 0.59),
        0.20,
        0.25,
        "Edge-DP learner",
        "visible transcript or ideal SecAgg",
        BLUE,
        fill="#EEF7FC",
    )
    box(
        ax,
        (0.26, 0.16),
        0.20,
        0.25,
        "Public branch",
        r"$s_0(u,v)$",
        GRAY,
        fill=LIGHT,
    )
    box(
        ax,
        (0.53, 0.59),
        0.18,
        0.25,
        "Structural branch",
        r"$s_R(u,v)$; no graph reread",
        BLUE,
        fill="#EEF7FC",
    )
    box(
        ax,
        (0.53, 0.16),
        0.18,
        0.25,
        "Private certificate",
        r"$\widetilde{S},\widetilde{n}\ \rightarrow\ L_{\rm pop}$",
        ORANGE,
        fill="#FFF4EC",
    )
    box(
        ax,
        (0.78, 0.37),
        0.19,
        0.30,
        "Certified gate",
        r"$s_R$ if $L_{\rm pop}\geq\gamma$" "\n" r"else $s_0$",
        GREEN,
        fill="#EEF9F5",
    )

    arrow(ax, (0.18, 0.715), (0.26, 0.715), BLUE)
    arrow(ax, (0.18, 0.285), (0.26, 0.285), GRAY)
    arrow(ax, (0.46, 0.715), (0.53, 0.715), BLUE)
    arrow(ax, (0.46, 0.285), (0.53, 0.285), GRAY)
    arrow(ax, (0.71, 0.715), (0.78, 0.59), BLUE)
    arrow(ax, (0.71, 0.285), (0.78, 0.45), ORANGE)
    arrow(ax, (0.46, 0.63), (0.53, 0.38), ORANGE)
    ax.text(
        0.49,
        0.48,
        r"disjoint $E^C$",
        ha="center",
        va="center",
        fontsize=7.3,
        color=ORANGE,
        rotation=-40,
    )
    ax.text(
        0.50,
        0.94,
        "Training and certification are composed in RDP; prediction is post-processing",
        ha="center",
        va="center",
        color=DARK,
        fontsize=8.5,
        fontweight="bold",
    )
    ax.text(
        0.875,
        0.26,
        "No certificate\nmeans safe fallback",
        ha="center",
        va="center",
        color=GREEN,
        fontsize=7.5,
    )
    save(fig, "figure1_certfed_overview")


def load_records() -> list[dict]:
    return [
        json.loads(line)
        for line in RECORDS.read_text(encoding="utf-8").splitlines()
        if line
    ]


def primary_policy(records: list[dict]) -> None:
    primary = [row for row in records if row["confirmatory_primary"]]
    names = [
        ("blogcatalog-v3", "BlogCatalog"),
        ("github-social-snap", "GitHub"),
        ("polblogs-newman", "PolBlogs"),
        ("deezer-europe-snap", "Deezer"),
        ("facebook-musae", "Facebook"),
        ("lastfm-asia-snap", "LastFM"),
    ]
    structural = np.asarray(
        [
            np.mean(
                [
                    row["q5_pairwise_advantage"]
                    for row in primary
                    if row["dataset"] == key
                ]
            )
            for key, _ in names
        ]
    )
    policy = np.asarray(
        [
            np.mean(
                [
                    row["q5_policy_pairwise_gain"]
                    for row in primary
                    if row["dataset"] == key
                ]
            )
            for key, _ in names
        ]
    )
    activated = [
        sum(
            row["activated"]
            for row in primary
            if row["dataset"] == key
        )
        for key, _ in names
    ]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.16, 2.75),
        gridspec_kw={"width_ratios": [2.15, 1]},
    )
    ax = axes[0]
    y = np.arange(len(names))
    height = 0.34
    ax.barh(
        y + height / 2,
        structural,
        height,
        color=BLUE,
        label="Always structural",
    )
    ax.barh(
        y - height / 2,
        policy,
        height,
        color=GREEN,
        label="CertFed-LP",
    )
    ax.axvline(0, color=DARK, linewidth=0.9)
    ax.set_yticks(y, [name for _, name in names])
    ax.invert_yaxis()
    ax.set_xlabel("Mean disjoint-Q5 pairwise gain over public-only")
    ax.set_title("(a) Target-domain decisions")
    ax.grid(axis="x", color="#D1D5DB", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    for index, count in enumerate(activated):
        label_x = policy[index] + 0.006 if count else 0.006
        ax.text(
            label_x,
            index - height / 2,
            f"{count}/5",
            ha="left",
            va="center",
            fontsize=7.2,
            color=GREEN if count else GRAY,
            fontweight="bold" if count else "normal",
        )

    q = np.asarray([row["q5_pairwise_advantage"] for row in primary])
    certified = np.asarray([row["q5_policy_pairwise_gain"] for row in primary])
    pooled = [0.0, q.mean(), certified.mean(), np.maximum(q, 0).mean()]
    labels = ["Public", "Always structural", "CertFed-LP", "Oracle"]
    colors = [GRAY, BLUE, GREEN, ORANGE]
    ax = axes[1]
    positions = np.arange(4)
    ax.barh(positions, pooled, color=colors, height=0.62)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Mean Q5 gain")
    ax.set_title("(b) Pooled policy utility")
    ax.axvline(0, color=DARK, linewidth=0.9)
    ax.grid(axis="x", color="#D1D5DB", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, 0.103)
    for index, value in enumerate(pooled):
        ax.text(
            value + 0.002,
            index,
            f"{value:.3f}",
            ha="left",
            va="center",
            fontsize=7.3,
        )
    fig.subplots_adjust(wspace=0.42)
    save(fig, "figure2_primary_policy")


def phase_diagram() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    eps = [0.5, 1.0, 2.0, 4.0, 8.0]
    fig = plt.figure(figsize=(7.16, 4.7), constrained_layout=True)
    grid = fig.add_gridspec(
        2, 3, width_ratios=[1.0, 1.0, 0.045], wspace=0.12, hspace=0.24
    )
    axes = np.asarray(
        [
            [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])],
            [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])],
        ]
    )
    color_axes = [fig.add_subplot(grid[0, 2]), fig.add_subplot(grid[1, 2])]
    top_image = None
    bottom_image = None
    for column, visibility in enumerate(["visible_messages", "ideal_secagg"]):
        activation = np.zeros((5, 5))
        gain = np.zeros((5, 5))
        for i, train_epsilon in enumerate(eps):
            for j, cert_epsilon in enumerate(eps):
                key = (
                    f"train={train_epsilon}/cert={cert_epsilon}/"
                    f"{visibility}"
                )
                cell = summary["diagnostic_cells"][key]
                activation[i, j] = cell["activated"] / cell["records"]
                gain[i, j] = cell["mean_q5_policy_gain"]
        top_image = axes[0, column].imshow(
            activation,
            origin="lower",
            cmap=mpl.colors.LinearSegmentedColormap.from_list(
                "activation", ["#F7FBFF", SKY, BLUE]
            ),
            vmin=0,
            vmax=1,
            aspect="equal",
        )
        bottom_image = axes[1, column].imshow(
            gain,
            origin="lower",
            cmap=mpl.colors.LinearSegmentedColormap.from_list(
                "gain", ["#F7FCF5", "#74C69D", GREEN]
            ),
            vmin=0,
            vmax=0.12,
            aspect="equal",
        )
        title = "Visible messages" if column == 0 else "Ideal SecAgg"
        axes[0, column].set_title(
            f"({'a' if column == 0 else 'b'}) {title}"
        )
        axes[1, column].set_title(
            f"({'c' if column == 0 else 'd'}) {title}"
        )
        for row in range(5):
            for cell in range(5):
                axes[0, column].text(
                    cell,
                    row,
                    f"{activation[row, cell]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if activation[row, cell] > 0.55 else DARK,
                )
                axes[1, column].text(
                    cell,
                    row,
                    f"{gain[row, cell]:.3f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if gain[row, cell] > 0.075 else DARK,
                )
        for ax in (axes[0, column], axes[1, column]):
            ax.set_xticks(range(5), [str(value) for value in eps])
            ax.set_yticks(range(5), [str(value) for value in eps])
            ax.set_xlabel(r"Certification target $\epsilon_C$")
            if column == 0:
                ax.set_ylabel(r"Training target $\epsilon_T$")
            else:
                ax.set_yticklabels([])
    colorbar = fig.colorbar(top_image, cax=color_axes[0])
    colorbar.set_label("Activation rate", labelpad=5)
    colorbar = fig.colorbar(bottom_image, cax=color_axes[1])
    colorbar.set_label("Mean Q5 gain", labelpad=5)
    save(fig, "figure3_privacy_phase")

def main() -> None:
    style()
    records = load_records()
    overview()
    primary_policy(records)
    phase_diagram()
    print(OUTPUT)


if __name__ == "__main__":
    main()
