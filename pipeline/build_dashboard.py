"""Build a self-contained HTML dashboard from the Gold outputs.

Run after pipeline/run_pipeline.py:  python pipeline/build_dashboard.py
Writes docs/dashboard.html. Contains aggregates only, no commit-level data.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "output" / "gold"
DQ = ROOT / "data" / "output" / "dq_report.csv"
DEST = ROOT / "docs" / "dashboard.html"

CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#111;background:#f7f7f8}
h1{font-size:22px;margin:0 0 4px}
h2{font-size:16px;margin:24px 0 8px}
.sub{color:#555;margin:0 0 20px;font-size:14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:14px}
.label{font-size:13px;color:#555}
.value{font-size:26px;font-weight:600;margin:4px 0}
.note{font-size:12px;color:#666}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13px}
th,td{border:1px solid #ddd;padding:6px 8px;text-align:left}
.fail{color:#b91c1c;font-weight:600}
.pass{color:#15803d;font-weight:600}
.box{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px}
"""


def card(label, value, note):
    return (
        '<div class="card">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(value)}</div>'
        f'<div class="note">{html.escape(note)}</div>'
        "</div>"
    )


def bar_chart(weekly):
    values = weekly["deployments"].astype(int).tolist()
    labels = [d.strftime("%d %b") for d in weekly.index]
    w, h, pad = 900, 240, 36
    n = len(values)
    peak = max(values) or 1
    slot = (w - 2 * pad) / n
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Deployments per week">']
    parts.append(f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" stroke="#999"/>')
    for i, (v, lab) in enumerate(zip(values, labels)):
        bh = (v / peak) * (h - 2 * pad)
        x = pad + i * slot + slot * 0.15
        y = h - pad - bh
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{slot * 0.7:.1f}" height="{bh:.1f}" fill="#2563eb">'
            f"<title>Week of {lab}: {v} deployments</title></rect>"
        )
        if i % 4 == 0:
            parts.append(
                f'<text x="{x:.1f}" y="{h - pad + 14}" font-size="10" fill="#555">{lab}</text>'
            )
    parts.append(
        f'<text x="{pad}" y="{pad - 12}" font-size="11" fill="#555">Deployments per week (peak {peak})</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def weekly_table(weekly):
    rows = []
    for week, r in weekly.iterrows():
        cfr = "—" if pd.isna(r["change_failure_rate"]) else f"{r['change_failure_rate']:.2%}"
        lead = "—" if pd.isna(r["median_lead_time_hours"]) else f"{r['median_lead_time_hours']:.2f}"
        rows.append(
            "<tr>"
            f"<td>{week.strftime('%Y-%m-%d')}</td>"
            f"<td>{int(r['deployments'])}</td>"
            f"<td>{lead}</td>"
            f"<td>{int(r['incidents'])}</td>"
            f"<td>{int(r['caused_by_deployment'])}</td>"
            f"<td>{cfr}</td>"
            "</tr>"
        )
    head = (
        "<tr><th>Week starting (Mon)</th><th>Deployments</th><th>Median lead time (h)</th>"
        "<th>Incidents</th><th>Caused by deployment</th><th>Change failure rate</th></tr>"
    )
    return f"<table>{head}{''.join(rows)}</table>"


def dq_table(dq):
    rows = []
    for _, r in dq.iterrows():
        cls = "pass" if r["status"] == "PASS" else "fail"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(r['check']))}</td>"
            f"<td>{html.escape(str(r['severity']))}</td>"
            f"<td>{int(r['rows_checked'])}</td>"
            f"<td>{int(r['rows_failed'])}</td>"
            f'<td class="{cls}">{html.escape(str(r["status"]))}</td>'
            f"<td>{html.escape(str(r['failing_ids']))}</td>"
            "</tr>"
        )
    head = "<tr><th>Check</th><th>Severity</th><th>Rows checked</th><th>Rows failed</th><th>Status</th><th>Failing IDs</th></tr>"
    return f"<table>{head}{''.join(rows)}</table>"


def main():
    if not (GOLD / "dora_summary.csv").exists():
        sys.exit("Gold outputs not found. Run pipeline/run_pipeline.py first.")

    summary = pd.read_csv(GOLD / "dora_summary.csv", index_col=0)["value"]
    weekly = pd.read_csv(GOLD / "dora_weekly.csv", index_col=0, parse_dates=True)
    dq = pd.read_csv(DQ)

    linkage = dq.loc[dq["check"].str.startswith("DQ2"), "failing_ids"].iloc[0].split("=")[1]

    cards = "".join([
        card(
            "Deployment frequency",
            f"{summary['deployment_frequency_per_day']:.2f} / day",
            f"{int(summary['deployments_counted'])} builds over {int(summary['window_days'])} days",
        ),
        card(
            "Lead time for changes (median)",
            f"{summary['median_lead_time_hours']:.2f} h",
            f"Partial: linked builds only ({linkage} of builds)",
        ),
        card(
            "Change failure rate",
            f"{summary['change_failure_rate']:.2%}",
            f"{int(summary['incidents_included'])} incidents included, {int(summary['incidents_quarantined'])} quarantined",
        ),
        card(
            "Time to restore (median)",
            f"{summary['median_time_to_restore_hours']:.2f} h",
            "Included incidents; small sample",
        ),
    ])

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DORA metrics baseline</title>
<style>{CSS}</style></head>
<body>
<h1>DORA metrics baseline</h1>
<p class="sub">Local baseline for the case study. Synthetic data. Stand-in for the Fabric Power BI dashboard.</p>
<div class="cards">{cards}</div>
<h2>Deployments per week</h2>
<div class="box">{bar_chart(weekly)}</div>
<h2>Weekly detail</h2>
{weekly_table(weekly)}
<h2>Data-quality checks</h2>
{dq_table(dq)}
<p class="sub">Definitions and assumptions: docs/data-engineering.md</p>
</body></html>
"""
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(page, encoding="utf-8")
    print(f"Wrote {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()