#!/usr/bin/env python3
"""Generate website-native SVG research figures from committed data and cited values.

The commodity-regime figures are read from the published CSV outputs. The article
figures use values already disclosed in the accompanying research notes and their
listed primary sources. SVG keeps the charts crisp, responsive and dependency-free.
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "public" / "projects" / "commodity-regime-analysis"
MODEL_OUT = ROOT / "public" / "models"
ARTICLE_OUT = ROOT / "public" / "research-figures"

BG = "#07111b"
PANEL = "#0b1723"
GRID = "#274052"
TEXT = "#eef8f3"
MUTED = "#9db0bd"
GREEN = "#65e3a2"
BLUE = "#8fb7de"
AMBER = "#f4c978"
RED = "#f29a9a"
PURPLE = "#b6a2ff"


def esc(value: object) -> str:
    return html.escape(str(value))


def svg_start(width: int = 1200, height: int = 700, label: str = "") -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">',
        "<defs>",
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="16" flood-color="#000" flood-opacity="0.22"/></filter>',
        '<linearGradient id="greenFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#65e3a2" stop-opacity="0.42"/><stop offset="1" stop-color="#65e3a2" stop-opacity="0.04"/></linearGradient>',
        '<linearGradient id="blueFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fb7de" stop-opacity="0.42"/><stop offset="1" stop-color="#8fb7de" stop-opacity="0.04"/></linearGradient>',
        "</defs>",
        f'<rect width="100%" height="100%" rx="24" fill="{BG}"/>',
        f'<rect x="1" y="1" width="1198" height="698" rx="23" fill="none" stroke="{GRID}"/>',
        '<style>text{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.label{fill:#9db0bd;font-size:18px}.small{fill:#9db0bd;font-size:15px}.value{fill:#eef8f3;font-size:20px;font-weight:650}.axis{stroke:#274052;stroke-width:1}.headline{fill:#eef8f3;font-size:22px;font-weight:650}.note{fill:#9db0bd;font-size:16px}</style>',
    ]


def finish(lines: list[str], path: Path) -> None:
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf8") as handle:
        return list(csv.DictReader(handle))


def grid(lines: list[str], x: float, y: float, w: float, h: float, ticks: Iterable[float], y_min: float, y_max: float) -> None:
    for tick in ticks:
        yy = y + h - (tick - y_min) / (y_max - y_min) * h
        lines.append(f'<line class="axis" x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" opacity="0.55"/>')
        lines.append(f'<text class="small" x="{x-18}" y="{yy+5:.1f}" text-anchor="end">{tick:g}</text>')


def commodity_sensitivity(rows: list[dict[str, str]]) -> None:
    lines = svg_start(label="Commodity-equity return sensitivities in lower and higher inflation regimes")
    x, y, w, h = 110, 95, 1030, 500
    y_min, y_max = -0.1, 0.85
    grid(lines, x, y, w, h, [-0.1, 0, 0.2, 0.4, 0.6, 0.8], y_min, y_max)
    lines += [
        f'<rect x="{x}" y="34" width="18" height="18" rx="3" fill="{BLUE}"/><text class="label" x="{x+30}" y="49">Lower inflation</text>',
        f'<rect x="{x+200}" y="34" width="18" height="18" rx="3" fill="{AMBER}"/><text class="label" x="{x+230}" y="49">High inflation</text>',
    ]
    group_w = w / len(rows)
    bar_w = 72
    for idx, row in enumerate(rows):
        cx = x + group_w * (idx + 0.5)
        lower = float(row["Lower_Inflation_Beta"])
        high = float(row["High_Inflation_Beta"])
        zero_y = y + h - (0 - y_min) / (y_max - y_min) * h
        for offset, value, color in [(-bar_w / 2 - 6, lower, BLUE), (6, high, AMBER)]:
            value_y = y + h - (value - y_min) / (y_max - y_min) * h
            top = min(zero_y, value_y)
            height = abs(value_y - zero_y)
            lines.append(f'<rect x="{cx+offset:.1f}" y="{top:.1f}" width="{bar_w}" height="{height:.1f}" rx="5" fill="{color}"/>')
            label_y = value_y - 12 if value >= 0 else value_y + 28
            lines.append(f'<text class="value" x="{cx+offset+bar_w/2:.1f}" y="{label_y:.1f}" text-anchor="middle">{value:.2f}</text>')
        lines.append(f'<text class="label" x="{cx:.1f}" y="{y+h+45}" text-anchor="middle">{esc(row["Commodity"])}</text>')
    finish(lines, MODEL_OUT / "commodity-regime-sensitivities.svg")


def commodity_differences(rows: list[dict[str, str]]) -> None:
    lines = svg_start(label="Inflation-regime difference estimates and HAC p-values")
    x, y, w, h = 110, 90, 1030, 500
    y_min, y_max = 0, 0.68
    grid(lines, x, y, w, h, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], y_min, y_max)
    colors = {"Brent": GREEN, "Gold": AMBER, "Copper": BLUE}
    group_w = w / len(rows)
    for idx, row in enumerate(rows):
        cx = x + group_w * (idx + 0.5)
        value = float(row["Regime_Difference"])
        p = float(row["Difference_HAC_PValue"])
        value_y = y + h - (value - y_min) / (y_max - y_min) * h
        bar_h = y + h - value_y
        color = colors.get(row["Commodity"], BLUE)
        lines.append(f'<rect x="{cx-58:.1f}" y="{value_y:.1f}" width="116" height="{bar_h:.1f}" rx="7" fill="{color}"/>')
        lines.append(f'<text class="value" x="{cx:.1f}" y="{value_y-16:.1f}" text-anchor="middle">Δ {value:.2f}</text>')
        lines.append(f'<text class="label" x="{cx:.1f}" y="{y+h+42}" text-anchor="middle">{esc(row["Commodity"])}</text>')
        verdict = "p &lt; 0.05" if p < 0.05 else f"p = {p:.3f}"
        lines.append(f'<text class="small" x="{cx:.1f}" y="{y+h+70}" text-anchor="middle">{verdict}</text>')
    finish(lines, MODEL_OUT / "commodity-regime-differences.svg")


def commodity_thresholds(rows: list[dict[str, str]]) -> None:
    lines = svg_start(label="Robustness of inflation-regime effects across CPI thresholds")
    x, y, w, h = 115, 80, 1020, 500
    y_min, y_max = -0.2, 0.85
    grid(lines, x, y, w, h, [-0.2, 0, 0.2, 0.4, 0.6, 0.8], y_min, y_max)
    thresholds = sorted({float(row["Threshold"]) for row in rows})
    commodities = ["Brent", "Gold", "Copper"]
    colors = {"Brent": GREEN, "Gold": AMBER, "Copper": BLUE}
    for idx, threshold in enumerate(thresholds):
        xx = x + idx / (len(thresholds) - 1) * w
        lines.append(f'<text class="label" x="{xx:.1f}" y="{y+h+42}" text-anchor="middle">{threshold:g}%</text>')
    for legend_idx, commodity in enumerate(commodities):
        lx = x + legend_idx * 170
        lines.append(f'<line x1="{lx}" y1="35" x2="{lx+30}" y2="35" stroke="{colors[commodity]}" stroke-width="5" stroke-linecap="round"/>')
        lines.append(f'<text class="label" x="{lx+42}" y="41">{commodity}</text>')
        sub = sorted((row for row in rows if row["Commodity"] == commodity), key=lambda item: float(item["Threshold"]))
        points: list[tuple[float, float]] = []
        for idx, row in enumerate(sub):
            xx = x + idx / (len(sub) - 1) * w
            value = float(row["Regime_Difference"])
            yy = y + h - (value - y_min) / (y_max - y_min) * h
            points.append((xx, yy))
        point_string = " ".join(f"{xx:.1f},{yy:.1f}" for xx, yy in points)
        lines.append(f'<polyline points="{point_string}" fill="none" stroke="{colors[commodity]}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
        for (xx, yy), row in zip(points, sub):
            p = float(row["Difference_HAC_PValue"])
            lines.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="7" fill="{BG}" stroke="{colors[commodity]}" stroke-width="4"/>')
            if commodity == "Brent":
                lines.append(f'<text class="small" x="{xx:.1f}" y="{yy-16:.1f}" text-anchor="middle">p={p:.02f}</text>')
    finish(lines, MODEL_OUT / "commodity-regime-thresholds.svg")


def commodity_audit(summary: dict[str, object]) -> None:
    lines = svg_start(height=430, label="Commodity-regime data audit and final model sample")
    cards = [
        (60, "Prepared sample", f'{summary["raw_rows"]} monthly rows', f'{summary["raw_sample_start"]} to {summary["raw_sample_end"]}'),
        (430, "Excluded artefacts", f'{summary["excluded_artificial_zero_rows"]} zero-return rows', "Forward-filled futures prices"),
        (800, "Final model sample", f'{summary["observations"]} observations', f'{summary["sample_start"]} to {summary["sample_end"]}'),
    ]
    for x, label, value, note in cards:
        lines.append(f'<rect x="{x}" y="90" width="320" height="230" rx="18" fill="{PANEL}" stroke="{GRID}" filter="url(#shadow)"/>')
        lines.append(f'<text class="small" x="{x+28}" y="135" letter-spacing="1.5">{esc(label).upper()}</text>')
        lines.append(f'<text class="headline" x="{x+28}" y="195">{esc(value)}</text>')
        lines.append(f'<text class="note" x="{x+28}" y="235">{esc(note)}</text>')
    for start, end in [(380, 430), (750, 800)]:
        lines.append(f'<line x1="{start}" y1="205" x2="{end-14}" y2="205" stroke="{BLUE}" stroke-width="3"/>')
        lines.append(f'<path d="M {end-20} 197 L {end-8} 205 L {end-20} 213" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    finish(lines, MODEL_OUT / "commodity-regime-audit.svg")


def brent_outlook() -> None:
    lines = svg_start(label="EIA oil inventory balance and Brent price outlook")
    lines.append('<text class="headline" x="70" y="54">Inventory balance</text>')
    lines.append('<text class="small" x="70" y="78">Million barrels per day; draw is negative</text>')
    x, y, w, h = 85, 125, 470, 430
    values = [("2Q26", -5.0), ("3Q26", -2.2), ("4Q26", 2.7), ("2027", 5.0)]
    y_min, y_max = -6, 6
    for tick in [-6, -3, 0, 3, 6]:
        yy = y + h - (tick-y_min)/(y_max-y_min)*h
        lines.append(f'<line class="axis" x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" opacity="0.55"/>')
        lines.append(f'<text class="small" x="{x-15}" y="{yy+5:.1f}" text-anchor="end">{tick:g}</text>')
    zero_y = y + h - (0-y_min)/(y_max-y_min)*h
    group = w / len(values)
    for idx, (label, value) in enumerate(values):
        cx = x + group*(idx+0.5)
        yy = y + h - (value-y_min)/(y_max-y_min)*h
        top = min(yy, zero_y)
        height = abs(yy-zero_y)
        color = GREEN if value > 0 else BLUE
        lines.append(f'<rect x="{cx-34:.1f}" y="{top:.1f}" width="68" height="{height:.1f}" rx="6" fill="{color}"/>')
        label_y = yy-14 if value > 0 else yy+28
        lines.append(f'<text class="value" x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle">{value:+.1f}</text>')
        lines.append(f'<text class="label" x="{cx:.1f}" y="{y+h+38}" text-anchor="middle">{label}</text>')

    lines.append('<line x1="600" y1="90" x2="600" y2="620" stroke="#274052"/>')
    lines.append('<text class="headline" x="650" y="54">Brent price outlook</text>')
    lines.append('<text class="small" x="650" y="78">EIA quarterly averages, US dollars per barrel</text>')
    x2, y2, w2, h2 = 665, 125, 450, 430
    price_values = [("2Q26", 103), ("3Q26", 74), ("4Q26", 70), ("2027", 65)]
    p_min, p_max = 55, 110
    for tick in [60, 70, 80, 90, 100, 110]:
        yy = y2 + h2 - (tick-p_min)/(p_max-p_min)*h2
        lines.append(f'<line class="axis" x1="{x2}" y1="{yy:.1f}" x2="{x2+w2}" y2="{yy:.1f}" opacity="0.55"/>')
        lines.append(f'<text class="small" x="{x2-15}" y="{yy+5:.1f}" text-anchor="end">${tick}</text>')
    points=[]
    for idx, (label, value) in enumerate(price_values):
        xx=x2+idx/(len(price_values)-1)*w2
        yy=y2+h2-(value-p_min)/(p_max-p_min)*h2
        points.append((xx,yy,label,value))
    lines.append('<path d="' + ' '.join((f'M {points[0][0]:.1f} {points[0][1]:.1f}',) + tuple(f'L {xx:.1f} {yy:.1f}' for xx,yy,_,_ in points[1:])) + f'" fill="none" stroke="{AMBER}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
    for xx,yy,label,value in points:
        lines.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="8" fill="{BG}" stroke="{AMBER}" stroke-width="4"/>')
        lines.append(f'<text class="value" x="{xx:.1f}" y="{yy-18:.1f}" text-anchor="middle">${value}</text>')
        lines.append(f'<text class="label" x="{xx:.1f}" y="{y2+h2+38}" text-anchor="middle">{label}</text>')
    finish(lines, ARTICLE_OUT / "brent-balance-and-price-outlook.svg")


def copper_context() -> None:
    lines = svg_start(label="Copper price context, preferred entry band and projected 2035 supply gap")
    lines.append('<text class="headline" x="70" y="54">Price context and entry discipline</text>')
    lines.append('<text class="small" x="70" y="78">US dollars per tonne</text>')
    x, y, w, h = 90, 125, 500, 430
    p_min, p_max = 10000, 15500
    for tick in [10000,11000,12000,13000,14000,15000]:
        yy=y+h-(tick-p_min)/(p_max-p_min)*h
        lines.append(f'<line class="axis" x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" opacity="0.55"/>')
        lines.append(f'<text class="small" x="{x-14}" y="{yy+5:.1f}" text-anchor="end">${tick/1000:.0f}k</text>')
    band_top=y+h-(12500-p_min)/(p_max-p_min)*h
    band_bottom=y+h-(11750-p_min)/(p_max-p_min)*h
    lines.append(f'<rect x="{x}" y="{band_top:.1f}" width="{w}" height="{band_bottom-band_top:.1f}" fill="{GREEN}" opacity="0.18"/>')
    lines.append(f'<text class="small" x="{x+w-8}" y="{band_top-10:.1f}" text-anchor="end">Preferred entry: $11,750–12,500</text>')
    points=[("Dec 2025",12000,BLUE),("Jan high",14500,AMBER),("17 Jul",13526,GREEN)]
    for idx,(label,value,color) in enumerate(points):
        xx=x+w*(idx+0.5)/len(points)
        yy=y+h-(value-p_min)/(p_max-p_min)*h
        lines.append(f'<line x1="{xx:.1f}" y1="{y+h}" x2="{xx:.1f}" y2="{yy:.1f}" stroke="{color}" stroke-width="7" stroke-linecap="round"/>')
        lines.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="9" fill="{BG}" stroke="{color}" stroke-width="4"/>')
        lines.append(f'<text class="value" x="{xx:.1f}" y="{yy-18:.1f}" text-anchor="middle">${value:,.0f}</text>')
        lines.append(f'<text class="label" x="{xx:.1f}" y="{y+h+38}" text-anchor="middle">{label}</text>')

    lines.append('<line x1="625" y1="90" x2="625" y2="620" stroke="#274052"/>')
    lines.append('<text class="headline" x="680" y="54">2035 mine-supply gap</text>')
    lines.append('<text class="small" x="680" y="78">IEA base-case project pipeline; demand indexed to 100</text>')
    bx, by, bw = 700, 220, 390
    lines.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="78" rx="12" fill="#142838"/>')
    lines.append(f'<rect x="{bx}" y="{by}" width="{bw*0.75}" height="78" rx="12" fill="{BLUE}"/>')
    lines.append(f'<rect x="{bx+bw*0.75}" y="{by}" width="{bw*0.25}" height="78" rx="0" fill="{RED}" opacity="0.88"/>')
    lines.append(f'<text class="value" x="{bx+bw*0.375}" y="{by+49}" text-anchor="middle">75 supplied</text>')
    lines.append(f'<text class="value" x="{bx+bw*0.875}" y="{by+49}" text-anchor="middle">25 gap</text>')
    lines.append(f'<text class="headline" x="{bx}" y="{by+150}">Projected deficit: 25%</text>')
    lines.append(f'<text class="note" x="{bx}" y="{by+188}">Structural scarcity supports the long-run case,</text>')
    lines.append(f'<text class="note" x="{bx}" y="{by+216}">but does not eliminate near-term valuation risk.</text>')
    finish(lines, ARTICLE_OUT / "copper-valuation-and-supply-gap.svg")


def gold_reality_check() -> None:
    lines = svg_start(label="Gold real-yield invalidation and official-sector demand")
    lines.append('<text class="headline" x="70" y="54">Real-yield invalidation</text>')
    lines.append('<text class="small" x="70" y="78">US 10-year TIPS yield, selected observations</text>')
    x,y,w,h=90,125,500,430
    y_min,y_max=1.6,2.5
    for tick in [1.6,1.8,2.0,2.2,2.4]:
        yy=y+h-(tick-y_min)/(y_max-y_min)*h
        lines.append(f'<line class="axis" x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" opacity="0.55"/>')
        lines.append(f'<text class="small" x="{x-14}" y="{yy+5:.1f}" text-anchor="end">{tick:.1f}%</text>')
    invalidation=2.15
    inv_y=y+h-(invalidation-y_min)/(y_max-y_min)*h
    lines.append(f'<line x1="{x}" y1="{inv_y:.1f}" x2="{x+w}" y2="{inv_y:.1f}" stroke="{RED}" stroke-width="3" stroke-dasharray="10 9"/>')
    lines.append(f'<text class="small" x="{x+w-5}" y="{inv_y-12:.1f}" text-anchor="end" fill="{RED}">2.15% invalidation</text>')
    observations=[("29 Jan",1.89),("5 Feb",1.89),("16 Jul",2.35)]
    points=[]
    for idx,(label,value) in enumerate(observations):
        xx=x+idx/(len(observations)-1)*w
        yy=y+h-(value-y_min)/(y_max-y_min)*h
        points.append((xx,yy,label,value))
    lines.append('<path d="' + ' '.join((f'M {points[0][0]:.1f} {points[0][1]:.1f}',) + tuple(f'L {xx:.1f} {yy:.1f}' for xx,yy,_,_ in points[1:])) + f'" fill="none" stroke="{AMBER}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
    for xx,yy,label,value in points:
        lines.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="8" fill="{BG}" stroke="{AMBER}" stroke-width="4"/>')
        lines.append(f'<text class="value" x="{xx:.1f}" y="{yy-18:.1f}" text-anchor="middle">{value:.2f}%</text>')
        lines.append(f'<text class="label" x="{xx:.1f}" y="{y+h+38}" text-anchor="middle">{label}</text>')

    lines.append('<line x1="625" y1="90" x2="625" y2="620" stroke="#274052"/>')
    lines.append('<text class="headline" x="680" y="54">Official demand remained strong</text>')
    lines.append('<text class="small" x="680" y="78">Net central-bank purchases, tonnes</text>')
    bars=[("2025 qtr avg",216,GREEN),("Q1 2026",244,BLUE)]
    bx,by,bw,bh=720,150,150,390
    max_v=280
    for idx,(label,value,color) in enumerate(bars):
        xx=bx+idx*220
        height=value/max_v*bh
        yy=by+bh-height
        lines.append(f'<rect x="{xx}" y="{yy:.1f}" width="{bw}" height="{height:.1f}" rx="9" fill="{color}"/>')
        lines.append(f'<text class="value" x="{xx+bw/2}" y="{yy-18:.1f}" text-anchor="middle">{value}t</text>')
        lines.append(f'<text class="label" x="{xx+bw/2}" y="{by+bh+38}" text-anchor="middle">{label}</text>')
    lines.append('<text class="note" x="690" y="615">Strong structural buying persisted, but it did not</text>')
    lines.append('<text class="note" x="690" y="643">prevent the tactical thesis from failing.</text>')
    finish(lines, ARTICLE_OUT / "gold-real-yield-and-official-demand.svg")


def main() -> None:
    primary = read_csv(MODEL_ROOT / "outputs" / "primary_relationship_results.csv")
    robustness = read_csv(MODEL_ROOT / "outputs" / "threshold_robustness.csv")
    summary = json.loads((MODEL_ROOT / "outputs" / "analysis_summary.json").read_text(encoding="utf8"))

    commodity_sensitivity(primary)
    commodity_differences(primary)
    commodity_thresholds(robustness)
    commodity_audit(summary)
    brent_outlook()
    copper_context()
    gold_reality_check()


if __name__ == "__main__":
    main()
