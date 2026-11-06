"""Top-down room plan. Usage: draw_plan.py plan.json out.png
plan.json: {"title":str,"outline":[[x,z],...],"items":[{"name","x0","z0","x1","z1","kind"}],"notes":[str]}
kind: furniture | wall | door | window | unsure. z grows away from the windows."""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

COL = {"furniture": "#c9b48a", "wall": "#555555", "door": "#5b8db8",
       "window": "#8fd0e8", "unsure": "#f2b8b5"}
p = json.load(open(sys.argv[1]))
xs = [c[0] for c in p["outline"]]; zs = [c[1] for c in p["outline"]]
fig, ax = plt.subplots(figsize=(14, 14 * (max(zs) - min(zs) + 2) / (max(xs) - min(xs) + 2)))
ax.add_patch(Polygon(p["outline"], closed=True, fc="#f7f5f0", ec="black", lw=2))
for it in p["items"]:
    w, d = it["x1"] - it["x0"], it["z1"] - it["z0"]
    ax.add_patch(Rectangle((it["x0"], it["z0"]), w, d, fc=COL[it.get("kind", "furniture")],
                           ec="#333333", lw=0.8, ls="--" if it.get("kind") == "unsure" else "-"))
    cx, cz = it["x0"] + w / 2, it["z0"] + d / 2
    if "lx" in it:
        ax.annotate(it["name"], xy=(cx, cz), xytext=(it["lx"], it["lz"]), fontsize=10, ha="center", va="center",
                    arrowprops=dict(arrowstyle="-", color="#333333", lw=0.8))
    else:
        ax.text(cx, cz, it["name"], ha="center", va="center", fontsize=10)
ax.set_xlim(min(xs) - 2.2, max(xs) + 1); ax.set_ylim(max(zs) + 1, min(zs) - 1)
ax.set_aspect("equal"); ax.grid(True, color="#dddddd", lw=0.5)
ax.set_xlabel("metres along the window wall"); ax.set_ylabel("metres into the room")
ax.set_title(p["title"])
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=130)
