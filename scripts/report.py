"""Usage: uv run --project python python scripts/report.py"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "loadtest" / "results", ROOT / "docs"
OUT.mkdir(exist_ok=True)

RTS, SVCS = ["py", "bun"], ["rest", "soap", "gql", "pbuf"]
PAT = re.compile(r"^(py|bun)_(rest|soap|gql|pbuf)_u(\d+)_stats\.csv$")


def label(rt, svc):
    return "node pbuf" if (rt, svc) == ("bun", "pbuf") else f"{rt} {svc}"  # bun pbuf runs on Node


rows = []
for f in RES.glob("*_stats.csv"):
    m = PAT.match(f.name)
    if not m:
        continue
    with f.open(newline="") as fh:
        agg = next((r for r in csv.DictReader(fh) if r["Name"] == "Aggregated"), None)
    if not agg:
        continue
    n, fails = int(agg["Request Count"]), int(agg["Failure Count"])
    rows.append({
        "rt": m[1], "svc": m[2], "users": int(m[3]), "requests": n,
        "rps": float(agg["Requests/s"]),
        "p50": float(agg["50%"]), "p95": float(agg["95%"]), "p99": float(agg["99%"]),
        "fail_pct": 100 * fails / n if n else 0.0,
    })

if not rows:
    raise SystemExit(f"No *_stats.csv files found in {RES}")

rows.sort(key=lambda r: (r["users"], RTS.index(r["rt"]), SVCS.index(r["svc"])))
users_levels = sorted({r["users"] for r in rows})

# CSV and Markdown
cols = ["users", "service", "requests", "rps", "p50_ms", "p95_ms", "p99_ms", "fail_pct"]
table = [[r["users"], label(r["rt"], r["svc"]), r["requests"], f'{r["rps"]:.1f}',
          f'{r["p50"]:.0f}', f'{r["p95"]:.0f}', f'{r["p99"]:.0f}', f'{r["fail_pct"]:.2f}']
         for r in rows]

with (OUT / "results.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(cols)
    w.writerows(table)

md = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
md += ["| " + " | ".join(map(str, t)) + " |" for t in table]
(OUT / "results.md").write_text("\n".join(md) + "\n")
print("\n".join(md))

# Chart
try:
    import matplotlib # type: ignore
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt # type: ignore
except ImportError:
    print("\n(no chart: run `uv add --project python matplotlib` to enable it)")
else:
    colors = {"rest": "tab:blue", "soap": "tab:orange", "gql": "tab:green", "pbuf": "tab:red"}
    panels = [("rps", "Throughput (req/s)", False),
              ("p50", "Median latency (ms)", True),
              ("p95", "p95 latency (ms)", True)]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, (key, title, logy) in zip(axes, panels):
        for rt in RTS:
            for svc in SVCS:
                pts = sorted((r["users"], r[key]) for r in rows
                             if r["rt"] == rt and r["svc"] == svc)
                if pts:
                    ax.plot(*zip(*pts), marker="o", color=colors[svc],
                            linestyle="-" if rt == "py" else "--", label=label(rt, svc))
        ax.set_title(title)
        ax.set_xlabel("concurrent users")
        ax.set_xscale("log")
        ax.set_xticks(users_levels)
        ax.set_xticklabels(users_levels)
        ax.minorticks_off()
        if logy:
            ax.set_yscale("log")
        ax.grid(alpha=0.3)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(OUT / "results.png", dpi=150) # type: ignore
    print(f"\nWrote {OUT / 'results.png'}")