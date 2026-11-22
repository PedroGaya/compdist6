"""Usage: uv run --project python python scripts/report.py [--duration 60s]

Reads  results/<run>/{params.txt, locust_stats.csv, locust_failures.csv, locust_history.csv}
Writes results/reports/*.csv   and   results/figures/*.png
"""
import argparse
import csv
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
REPORTS, FIGS = RES / "reports", RES / "figures"
REPORTS.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

RTS, SVCS = ["py", "bun"], ["rest", "soap", "gql", "pbuf"]
COLORS = {"rest": "tab:blue", "soap": "tab:orange", "gql": "tab:green", "pbuf": "tab:red"}
NAN = float("nan")


def label(rt, svc):
    return "node pbuf" if (rt, svc) == ("bun", "pbuf") else f"{rt} {svc}"  # bun pbuf runs on Node


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return NAN


def secs(d):
    return float(d.rstrip("s")) if d.endswith("s") else NAN


def med(xs):
    xs = [x for x in xs if not math.isnan(x)]
    return st.median(xs) if xs else NAN


def write_csv(name, header, rows):
    with (REPORTS / name).open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows([[f"{v:.3f}" if isinstance(v, float) else v for v in r] for r in rows])
    print(f"  results/reports/{name}  ({len(rows)} rows)")


# ---------------------------------------------------------------- load
ap = argparse.ArgumentParser()
ap.add_argument("--duration", help="only include runs with this duration (default: the longest found)")
args = ap.parse_args()

runs = []
for d in sorted(p for p in RES.iterdir() if p.is_dir() and p.name not in ("reports", "figures")):
    pf, sf = d / "params.txt", d / "locust_stats.csv"
    if not (pf.exists() and sf.exists()):
        continue
    params = dict(l.strip().split("=", 1) for l in pf.read_text().splitlines() if "=" in l)
    with sf.open(newline="") as fh:
        stats = list(csv.DictReader(fh))
    agg = next((r for r in stats if r["Name"] == "Aggregated"), None)
    if not agg or not int(agg["Request Count"]):
        continue
    runs.append({"dir": d, "rt": params["runtime"], "svc": params["service"],
                 "users": int(params["users"]), "duration": params["duration"],
                 "stats": stats, "agg": agg})

if not runs:
    raise SystemExit(f"No complete runs found in {RES}")

durations = sorted({r["duration"] for r in runs}, key=secs)
chosen = args.duration or durations[-1]
skipped = [r for r in runs if r["duration"] != chosen]
runs = [r for r in runs if r["duration"] == chosen]
print(f"Duration filter: {chosen} (found {durations}); using {len(runs)} runs, skipping {len(skipped)}")

for r in runs:
    a = r["agg"]
    n, f = int(a["Request Count"]), int(a["Failure Count"])
    r.update(requests=n, fails=f, fail_pct=100 * f / n, rps=num(a["Requests/s"]),
             avg=num(a["Average Response Time"]), p50=num(a["50%"]), p95=num(a["95%"]),
             p99=num(a["99%"]), pmax=num(a["Max Response Time"]))

groups = defaultdict(list)
for r in runs:
    groups[(r["rt"], r["svc"], r["users"])].append(r)
USERS = sorted({k[2] for k in groups})
order = lambda k: (k[2], RTS.index(k[0]), SVCS.index(k[1]))
keys = sorted(groups, key=order)

# ---------------------------------------------------------------- CSV reports
print("Writing reports:")

# 1. every individual run
write_csv("runs.csv",
          ["run", "runtime", "service", "users", "duration", "requests", "failures", "fail_pct",
           "rps", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms"],
          [[r["dir"].name, r["rt"], label(r["rt"], r["svc"]), r["users"], r["duration"],
            r["requests"], r["fails"], r["fail_pct"], r["rps"], r["avg"], r["p50"],
            r["p95"], r["p99"], r["pmax"]] for r in sorted(runs, key=lambda r: (order((r["rt"], r["svc"], r["users"])), r["dir"].name))])

# 2. grouped summary (median across repeated runs, with spread)
S = {}
for k in keys:
    g = groups[k]
    col = lambda f: [r[f] for r in g] # type: ignore
    S[k] = {"n": len(g), "requests": med(col("requests")), "rps": med(col("rps")),
            "rps_min": min(col("rps")), "rps_max": max(col("rps")),
            "avg": med(col("avg")), "p50": med(col("p50")), "p95": med(col("p95")),
            "p99": med(col("p99")), "max": max(col("pmax")),
            "fail_pct": max(col("fail_pct"))}
write_csv("summary.csv",
          ["users", "service", "n_runs", "requests_median", "rps_median", "rps_min", "rps_max",
           "rps_spread_pct", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms", "max_fail_pct"],
          [[k[2], label(k[0], k[1]), s["n"], s["requests"], s["rps"], s["rps_min"], s["rps_max"],
            100 * (s["rps_max"] - s["rps_min"]) / s["rps"] if s["rps"] else NAN,
            s["avg"], s["p50"], s["p95"], s["p99"], s["max"], s["fail_pct"]]
           for k, s in S.items()])

# 3. per-operation stats (median across repeated runs)
ops = defaultdict(lambda: defaultdict(list))
for r in runs:
    for row in r["stats"]:
        if row["Name"] != "Aggregated":
            ops[(r["rt"], r["svc"], r["users"], row["Name"])]["row"].append(row)
OPS = {}
for k in sorted(ops, key=lambda k: (order(k[:3]), k[3])):
    rows = ops[k]["row"]
    c = lambda f: med([num(x[f]) for x in rows])
    OPS[k] = {"requests": c("Request Count"), "fails": c("Failure Count"), "rps": c("Requests/s"),
              "avg": c("Average Response Time"), "p50": c("50%"), "p95": c("95%"),
              "p99": c("99%"), "max": max(num(x["Max Response Time"]) for x in rows)}
write_csv("operations.csv",
          ["users", "service", "operation", "requests", "failures", "rps", "avg_ms", "p50_ms",
           "p95_ms", "p99_ms", "max_ms"],
          [[k[2], label(k[0], k[1]), k[3], v["requests"], v["fails"], v["rps"], v["avg"], v["p50"],
            v["p95"], v["p99"], v["max"]] for k, v in OPS.items()])

# 4. failures with their error text
fail_rows = []
for r in runs:
    ff = r["dir"] / "locust_failures.csv"
    if ff.exists():
        with ff.open(newline="") as fh:
            for row in csv.DictReader(fh):
                fail_rows.append([r["dir"].name, label(r["rt"], r["svc"]), r["users"],
                                  row["Name"], int(row["Occurrences"]), row["Error"][:300]])
write_csv("failures.csv", ["run", "service", "users", "operation", "occurrences", "error"], fail_rows)

# 5. runtime comparison: bun(node) / python, per protocol and load
rc = []
for svc in SVCS:
    for u in USERS:
        p, b = S.get(("py", svc, u)), S.get(("bun", svc, u))
        if p and b:
            rc.append([u, svc, p["rps"], b["rps"], b["rps"] / p["rps"], p["p50"], b["p50"],
                       b["p50"] / p["p50"] if p["p50"] else NAN, p["p95"], b["p95"],
                       b["p95"] / p["p95"] if p["p95"] else NAN])
write_csv("runtime_comparison.csv",
          ["users", "protocol", "py_rps", "bun_rps", "rps_ratio_bun_over_py", "py_p50_ms", "bun_p50_ms",
           "p50_ratio_bun_over_py", "py_p95_ms", "bun_p95_ms", "p95_ratio_bun_over_py"], rc)

# 6. protocol comparison: each protocol relative to REST within the same runtime
pc = []
for rt in RTS:
    for u in USERS:
        base = S.get((rt, "rest", u))
        for svc in SVCS:
            s = S.get((rt, svc, u))
            if s and base:
                pc.append([rt, u, svc, s["rps"], s["rps"] / base["rps"], s["p50"],
                           s["p50"] / base["p50"] if base["p50"] else NAN, s["p95"],
                           s["p95"] / base["p95"] if base["p95"] else NAN])
write_csv("protocol_comparison.csv",
          ["runtime", "users", "protocol", "rps", "rps_vs_rest", "p50_ms", "p50_vs_rest", "p95_ms", "p95_vs_rest"], pc)

# ---------------------------------------------------------------- figures
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    raise SystemExit("No figures: run `uv add --project python matplotlib`")

print("Writing figures:")


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name, dpi=150)
    plt.close(fig)
    print(f"  results/figures/{name}")

def series(rt, svc, field):
    pts = [(u, S[(rt, svc, u)][field]) for u in USERS if (rt, svc, u) in S]
    return ([p[0] for p in pts], [p[1] for p in pts])


def style(ax, title, ylabel, logy=False):
    ax.set_title(title)
    ax.set_xlabel("concurrent users")
    ax.set_ylabel(ylabel)
    ax.set_xscale("log")
    ax.set_xticks(USERS)
    ax.set_xticklabels(USERS)
    ax.minorticks_off()
    if logy:
        ax.set_yscale("log")
    ax.grid(alpha=0.3)


def legend_below(fig, ax, ncol=2, loc="best"):
    ax.legend(ncol=ncol, loc=loc, fontsize=8, frameon=True, framealpha=0.85)

def lines(ax, field, errbars=False):
    for rt in RTS:
        for svc in SVCS:
            x, y = series(rt, svc, field)
            if not x:
                continue
            kw = dict(marker="o", color=COLORS[svc], linestyle="-" if rt == "py" else "--", label=label(rt, svc))
            if errbars:
                lo = [S[(rt, svc, u)]["rps"] - S[(rt, svc, u)]["rps_min"] for u in x]
                hi = [S[(rt, svc, u)]["rps_max"] - S[(rt, svc, u)]["rps"] for u in x]
                ax.errorbar(x, y, yerr=[lo, hi], capsize=3, **kw)
            else:
                ax.plot(x, y, **kw)


# 1. throughput vs users (error bars = min/max across repeated runs)
fig, ax = plt.subplots(figsize=(8, 5.5))
lines(ax, "rps", errbars=True)
style(ax, "Throughput vs load (bars: min/max across runs)", "requests / s")
legend_below(fig, ax)
save(fig, "throughput_vs_users.png")

# 2. latency vs users: p50, p95, p99
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
for ax, (f, t) in zip(axes, [("p50", "Median latency"), ("p95", "p95 latency"), ("p99", "p99 latency")]):
    lines(ax, f)
    style(ax, t, "ms (log)", logy=True)
legend_below(fig, axes[0])
save(fig, "latency_vs_users.png")

# 3. grouped bars at each load: throughput and p95
def grouped_bars(field, title, ylabel, fname, logy=False):
    fig, axes = plt.subplots(1, len(USERS), figsize=(5.5 * len(USERS), 5), sharey=True)
    axes = [axes] if len(USERS) == 1 else axes
    w = 0.38
    for ax, u in zip(axes, USERS):
        for i, rt in enumerate(RTS):
            vals = [S[(rt, s, u)][field] if (rt, s, u) in S else 0 for s in SVCS]
            bars = ax.bar([j + (i - 0.5) * w for j in range(len(SVCS))], vals, w,
                          color=[COLORS[s] for s in SVCS], alpha=1.0 if rt == "py" else 0.55,
                          hatch="" if rt == "py" else "//", edgecolor="black", linewidth=0.5)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center", va="bottom", fontsize=7)
        ax.set_xticks(range(len(SVCS)))
        ax.set_xticklabels(SVCS)
        ax.set_title(f"{u} users")
        ax.grid(axis="y", alpha=0.3)
        if logy:
            ax.set_yscale("log")
    axes[0].set_ylabel(ylabel)
    fig.suptitle(title + "  (solid = Python, hatched = Bun/Node; gRPC on Bun is Node)")
    save(fig, fname)


grouped_bars("rps", "Throughput by protocol", "requests / s", "throughput_bars.png")
grouped_bars("p95", "p95 latency by protocol", "ms (log)", "p95_bars.png", logy=True)

# 4. latency percentile profile per load level
fig, axes = plt.subplots(1, len(USERS), figsize=(5.5 * len(USERS), 5), sharey=True)
axes = [axes] if len(USERS) == 1 else axes
combos = [(rt, s) for rt in RTS for s in SVCS]
for ax, u in zip(axes, USERS):
    w = 0.27
    for i, (f, hatch) in enumerate([("p50", ""), ("p95", "//"), ("p99", "xx")]):
        vals = [S[(rt, s, u)][f] if (rt, s, u) in S else 0 for rt, s in combos]
        ax.bar([j + (i - 1) * w for j in range(len(combos))], vals, w, hatch=hatch,
               color=[COLORS[s] for _, s in combos], edgecolor="black", linewidth=0.5,
               label=f if True else None)
    ax.set_xticks(range(len(combos)))
    ax.set_xticklabels([label(*c) for c in combos], rotation=60, ha="right", fontsize=8)
    ax.set_yscale("log")
    ax.set_title(f"{u} users")
    ax.grid(axis="y", alpha=0.3)
axes[0].set_ylabel("ms (log)")
fig.suptitle("Latency percentiles (plain = p50, // = p95, xx = p99)")
save(fig, "latency_percentiles.png")

# 5. heatmaps: throughput and p95 (service x load)
def heatmap(field, title, fname, fmt="{:.0f}"):
    rows = [(rt, s) for rt in RTS for s in SVCS]
    data = [[S[(rt, s, u)][field] if (rt, s, u) in S else NAN for u in USERS] for rt, s in rows]
    fig, ax = plt.subplots(figsize=(1.8 + 1.4 * len(USERS), 5))
    im = ax.imshow(data, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(USERS)))
    ax.set_xticklabels(USERS)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([label(*r) for r in rows])
    ax.set_xlabel("concurrent users")
    ax.set_title(title)
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            if not math.isnan(v):
                ax.text(j, i, fmt.format(v), ha="center", va="center", color="white", fontsize=9)
    fig.colorbar(im, ax=ax)
    save(fig, fname)


heatmap("rps", "Throughput (req/s)", "heatmap_throughput.png")
heatmap("p95", "p95 latency (ms)", "heatmap_p95.png")

# 6. failure rate
fig, ax = plt.subplots(figsize=(9, 4.5))
w = 0.8 / len(USERS)
for i, u in enumerate(USERS):
    vals = [S[(rt, s, u)]["fail_pct"] if (rt, s, u) in S else 0 for rt, s in combos]
    ax.bar([j + (i - (len(USERS) - 1) / 2) * w for j in range(len(combos))], vals, w, label=f"{u} users")
ax.set_xticks(range(len(combos)))
ax.set_xticklabels([label(*c) for c in combos], rotation=45, ha="right")
ax.set_ylabel("failures (%), worst run")
ax.set_title("Failure rate")
ax.legend()
ax.grid(axis="y", alpha=0.3)
save(fig, "failure_rate.png")

# 7. runtime ratio (bun/node over python)
if rc:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for ax, (idx, t) in zip(axes, [(4, "Throughput ratio (Bun/Node ÷ Python), >1 = Bun faster"),
                                   (10, "p95 latency ratio (Bun/Node ÷ Python), <1 = Bun faster")]):
        w = 0.8 / len(SVCS)
        for i, svc in enumerate(SVCS):
            vals = [next((r[idx] for r in rc if r[0] == u and r[1] == svc), NAN) for u in USERS]
            ax.bar([j + (i - 1.5) * w for j in range(len(USERS))], vals, w, color=COLORS[svc], label=svc)
        ax.axhline(1, color="black", linewidth=1)
        ax.set_xticks(range(len(USERS)))
        ax.set_xticklabels(USERS)
        ax.set_xlabel("concurrent users")
        ax.set_title(t, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend()
    save(fig, "runtime_ratio.png")

# 8. protocol cost relative to REST, per runtime
fig, axes = plt.subplots(1, len(RTS), figsize=(6.5 * len(RTS), 4.8), sharey=True)
for ax, rt in zip(axes, RTS):
    w = 0.8 / len(SVCS)
    for i, svc in enumerate(SVCS):
        vals = [next((r[4] for r in pc if r[0] == rt and r[1] == u and r[2] == svc), NAN) for u in USERS]
        ax.bar([j + (i - 1.5) * w for j in range(len(USERS))], vals, w, color=COLORS[svc], label=svc)
    ax.axhline(1, color="black", linewidth=1)
    ax.set_xticks(range(len(USERS)))
    ax.set_xticklabels(USERS)
    ax.set_xlabel("concurrent users")
    ax.set_title(f"{rt}: throughput relative to REST")
    ax.grid(axis="y", alpha=0.3)
axes[0].legend()
save(fig, "protocol_vs_rest.png")

# 9. per-operation p95 at the highest load (one panel per service)
top = USERS[-1]
fig, axes = plt.subplots(2, 4, figsize=(20, 9))
for ax, (rt, svc) in zip(axes.flat, combos):
    items = [(k[3], v["p95"]) for k, v in OPS.items() if k[:3] == (rt, svc, top)]
    items.sort(key=lambda t: t[1])
    if items:
        ax.barh([n.replace("SOAP ", "").replace("GQL ", "") for n, _ in items],
                [v for _, v in items], color=COLORS[svc])
    ax.set_title(f"{label(rt, svc)} @ {top} users: p95 (ms)", fontsize=10)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="x", alpha=0.3)
save(fig, f"operation_p95_u{top}.png")

# 10. throughput over time, one figure per load level (first run of each combination)
for u in USERS:
    fig, ax = plt.subplots(figsize=(9, 5))
    drawn = False
    for rt, svc in combos:
        g = groups.get((rt, svc, u))
        hf = g[0]["dir"] / "locust_stats_history.csv" if g else None
        if not (hf and hf.exists()):
            hf = g[0]["dir"] / "locust_history.csv" if g else None
        if not (hf and hf.exists()):
            continue
        with hf.open(newline="") as fh:
            hist = [r for r in csv.DictReader(fh) if r.get("Name") == "Aggregated"]
        if not hist:
            continue
        t0 = num(hist[0]["Timestamp"])
        ax.plot([num(r["Timestamp"]) - t0 for r in hist], [num(r["Requests/s"]) for r in hist],
                color=COLORS[svc], linestyle="-" if rt == "py" else "--", label=label(rt, svc))
        drawn = True
    if drawn:
        ax.axvspan(0, 13, color="grey", alpha=0.15)
        ax.text(0.5, 0.97, "ramp-up + stats reset (not representative)", transform=ax.transAxes,
                fontsize=8, va="top")
        ax.set_title(f"Throughput over time @ {u} users")
        ax.set_xlabel("seconds since start")
        ax.set_ylabel("requests / s")
        ax.grid(alpha=0.3)
        legend_below(fig, ax)
        save(fig, f"timeseries_rps_u{u}.png")
    else:
        plt.close(fig)

# 11. run-to-run variability (only meaningful with repeated runs)
if any(s["n"] > 1 for s in S.values()):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ks = [k for k in keys if S[k]["n"] > 1]
    ax.bar(range(len(ks)), [100 * (S[k]["rps_max"] - S[k]["rps_min"]) / S[k]["rps"] for k in ks],
           color=[COLORS[k[1]] for k in ks])
    ax.set_xticks(range(len(ks)))
    ax.set_xticklabels([f"{label(k[0], k[1])} u{k[2]}" for k in ks], rotation=70, ha="right", fontsize=7)
    ax.set_ylabel("(max - min) / median throughput (%)")
    ax.set_title("Run-to-run variability")
    ax.grid(axis="y", alpha=0.3)
    save(fig, "run_variability.png")

print("Done.")