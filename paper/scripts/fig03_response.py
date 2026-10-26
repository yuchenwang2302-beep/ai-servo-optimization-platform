"""Paper figure: run via plot.py. Inputs in data/, exports in output/."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FormatStrFormatter

from common import DATA as SOURCE, OUTPUT

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "path",
    "axes.linewidth": 0.65,
    "lines.linewidth": 1.15,
    "path.simplify": False,
})

data = np.genfromtxt(SOURCE / "single_objective.csv", delimiter=",", names=True)
time = data["time_s"]
reference = data["reference_pu"]
responses = [
    (data["midpoint"], "#9b9b9b", "Midpoint"),
    (data["all_upper"], "#ba7135", "All upper"),
    (data["pso"], "#225d87", "PSO"),
]

assert len(time) == 10001
assert np.all(np.diff(time) > 0)
for response, _, _ in responses:
    assert response.shape == time.shape
    assert np.all(np.isfinite(response))

zoom_x = (0.55, 0.66)
zoom_y = (0.40, 0.54)
fig, axes = plt.subplots(2, 1, figsize=(3.42, 3.05), layout="constrained")
for ax in axes:
    ax.plot(time, reference, color="black", linestyle="--", label="Reference", zorder=3)
    for response, color, label in responses:
        ax.plot(time, response, color=color, label=label, zorder=4)
    ax.set(xlabel="Time (s)", ylabel="Position (p.u.)")
    ax.grid(alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)

axes[0].set(xlim=(0, 1), ylim=(-0.025, 0.56))
axes[0].set_xticks(np.arange(0, 1.01, 0.2))
axes[0].set_yticks([0, 0.2, 0.4])
axes[0].legend(frameon=False, loc="upper left", handlelength=2.1, labelspacing=0.3)
axes[0].add_patch(Rectangle(
    (zoom_x[0], zoom_y[0]), zoom_x[1] - zoom_x[0], zoom_y[1] - zoom_y[0],
    fill=False, edgecolor="#626b75", linewidth=0.8,
    linestyle=(0, (2.5, 2)), zorder=5,
))
axes[1].set(xlim=zoom_x, ylim=zoom_y)
axes[1].set_xticks([0.55, 0.58, 0.61, 0.64, 0.66])
axes[1].set_yticks([0.40, 0.44, 0.48, 0.52])
axes[1].xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
axes[1].yaxis.set_major_formatter(FormatStrFormatter("%.2f"))

for label, ax in zip(("(a)", "(b)"), axes):
    ax.text(0.94, 0.12, label, transform=ax.transAxes, ha="right", va="bottom")

fig.savefig(OUTPUT / "ui_case_response.pdf", metadata={key: None for key in
    ("Title", "Author", "Subject", "Keywords", "Creator", "Producer", "CreationDate", "ModDate", "Trapped")})
fig.savefig(OUTPUT / "ui_case_response.svg", metadata={"Creator": None, "Date": None})
fig.savefig(OUTPUT / "ui_case_response.png", dpi=400, metadata={"Software": None})
plt.close(fig)
print(json.dumps({"samples_per_curve": len(time), "zoom_time_s": zoom_x,
                  "zoom_position_pu": zoom_y, "output": str(OUTPUT)}, indent=2))
