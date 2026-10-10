"""Dumbbell chart (inline SVG) of tokens per suite run before and after each self-repair round.

One row per round: a dot before, a dot after, joined by a line. Kept rounds use a filled dot and a
solid line; reverted rounds a hollow dot and a dashed line, plus a text label, so the result never
depends on color alone (green/red fail the deutan check). Native <title> tooltips give the exact
numbers on hover; the table under the chart is the accessible view.
"""

import html

OK, BAD, INK, MUTE, GRID = "#16794a", "#b83a3a", "#0f0f0d", "#5d5d55", "#cbcbbf"


def dumbbell(rounds: list[dict]) -> str:
    rows = [r for r in rounds if not r.get("rejected") and r.get("before_tokens")]
    if not rows:
        return ""
    w, left, right, row_h, top = 760, 150, 40, 46, 34
    h = top + row_h * len(rows) + 30
    hi = max(max(r["before_tokens"], r["after_tokens"]) for r in rows) * 1.08
    x = lambda v: left + (w - left - right) * v / hi  # noqa: E731
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Tokens per suite run before and after each self-repair round" '
             f'style="width:100%;min-width:620px;height:auto;font:13px Inter,sans-serif">']
    for t in range(0, int(hi) + 1, 250_000):  # recessive grid
        parts.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 10}" y2="{h - 26}" stroke="{GRID}" stroke-width="1"/>'
                     f'<text x="{x(t):.1f}" y="{h - 8}" fill="{MUTE}" text-anchor="middle">{t // 1000:,}k</text>')
    for i, r in enumerate(rows):
        y = top + row_h * i + row_h / 2
        kept = r["kept"]
        color = OK if kept else BAD
        b, a = x(r["before_tokens"]), x(r["after_tokens"])
        pct = (r["after_tokens"] - r["before_tokens"]) / r["before_tokens"] * 100
        tip = html.escape(f"Round {i + 1}: {r['before_tokens']:,} -> {r['after_tokens']:,} tokens ({pct:+.1f}%), "
                          f"{r['before_passed']} -> {r['after_passed']}/{r['total']} solved, {'kept' if kept else 'reverted'}")
        dash = "" if kept else ' stroke-dasharray="5 4"'
        parts.append(f'<g><title>{tip}</title>'
                     f'<rect x="0" y="{y - row_h / 2:.1f}" width="{w}" height="{row_h}" fill="transparent"/>'
                     f'<text x="0" y="{y + 4:.1f}" fill="{INK}" font-weight="600">Round {i + 1}</text>'
                     f'<text x="66" y="{y + 4:.1f}" fill="{MUTE}">{"kept" if kept else "reverted"}</text>'
                     f'<line x1="{b:.1f}" x2="{a:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="2"{dash}/>'
                     f'<circle cx="{b:.1f}" cy="{y:.1f}" r="5" fill="#f4f4ee" stroke="{MUTE}" stroke-width="2"/>'
                     f'<circle cx="{a:.1f}" cy="{y:.1f}" r="6" fill="{color if kept else "#f4f4ee"}" stroke="{color}" stroke-width="2"/>'
                     f'<text x="{max(a, b) + 12:.1f}" y="{y + 4:.1f}" fill="{INK}">{pct:+.1f}%</text></g>')
    parts.append(f'<text x="0" y="14" fill="{MUTE}">Tokens per suite run. Grey: before. Colored: after '
                 f'(filled = kept, hollow = reverted).</text></svg>')
    return "".join(parts)
