#!/usr/bin/env python3
"""Declarative HLA diagram generator for draw.io (stdlib only).

Why: hand-placed coordinates are what produced overlapping wires and stacked
labels. Agents (or humans) fill in the three tables below -- LANES, NODES,
EDGES -- and every coordinate is derived here: each node occupies a numbered
Y-slot inside its swimlane, forward edges run straight between slot rows,
backward/event edges are pushed through corridors ABOVE/BELOW the lane band
(never through lane headers), and every edge label is short, bounded, and
background-filled so it stays readable where it crosses a wire.

Label law (enforced by _validate_model, see also SKILL.md section 5):
  * value  <= 24 chars per line, <= 2 lines (short verb or trimmed topic)
  * full topic names / payload detail go in `topic=`, rendered as a second
    line ONLY when it still fits the 24-char bound, otherwise drop it
  * every label carries labelBackgroundColor so text never blends into wires

Usage: edit the tables in build_model(), then
  python3 hla_generator.py out.drawio.xml
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- layout pins
PAGE_MARGIN_X = 50
LANE_TOP = 130          # lanes start here; the band above (y < 130) is the
CORRIDOR_TOP_Y = 85     # exclusive top-corridor route (never crosses headers)
TITLE_BAND = 60         # lane-header zone; first slot starts below it
SLOT_H = 90             # one node + its below-icon label per slot row
SLOT_BOTTOM_PAD = 40
CORRIDOR_BOTTOM_GAP = 50
LABEL_MAX_CHARS = 24
LABEL_MAX_LINES = 2

# node kind -> (style, width, height). Icon nodes label below; boxes inside.
STYLES = {
    "pod_new": ("sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#dae8fc;strokeColor=#03CCFF;strokeWidth=2;points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=9.5;fontStyle=1;fontColor=#000000;", 40, 40),
    "pod_reuse": ("sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#f5f5f5;strokeColor=#BFBFBF;strokeWidth=1.5;points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=9.5;fontStyle=1;fontColor=#000000;", 40, 40),
    "ext": ("rounded=1;html=1;whiteSpace=wrap;fillColor=#EF7D30;strokeColor=#B36520;fontColor=#000000;fontSize=9.5;fontStyle=1;align=center;verticalAlign=middle;", 170, 30),
    "ext_plain": ("rounded=1;html=1;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#82B366;fontColor=#000000;fontSize=9.5;fontStyle=1;align=center;verticalAlign=middle;", 170, 30),
}

EDGE_STYLES = {
    # sync call: solid teal. async/callback + webview + event: dashed.
    "sync": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#006666;strokeWidth=2;endArrow=classic;fontSize=9;fontColor=#333333;labelBackgroundColor=#FFFFFF;",
    "async": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#CC6600;strokeWidth=2;dashed=1;endArrow=classic;fontSize=9;fontColor=#333333;labelBackgroundColor=#FFFFFF;",
    "event": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#CC0000;strokeWidth=1.5;dashed=1;endArrow=classic;fontSize=9;fontColor=#333333;labelBackgroundColor=#FFFFFF;",
    "view": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#666666;strokeWidth=1.5;dashed=1;endArrow=open;fontSize=9;fontColor=#333333;labelBackgroundColor=#FFFFFF;",
}


def esc(val):
    if not val:
        return ""
    val = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", val)
    val = val.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return val


def load_standard_tab_xml():
    """The Standard Colors and Icons tab shipped beside this script."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "standard_icons_tab.xml")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


# ------------------------------------------------------------------ the model
# (id, title, width, fill, stroke) -- order = left-to-right swimlanes.
LANES = [
    ("lane_client", "Client & Inbound Rails", 240, "#ECECEC", "#4a5568"),
    ("lane_gw", "Gateway Layer (Kong)", 180, "#f8f9fa", "#4a5568"),
    ("lane_bff", "Channel BFF Layer", 240, "#dae8fc", "#6c8ebf"),
    ("lane_orch", "Orchestration Layer", 260, "#ffe6cc", "#d79b00"),
    ("lane_core", "Domain Core Layer", 480, "#fff2cc", "#d6b656"),
    ("lane_adapt", "Adaptor Layer", 240, "#E6D5DE", "#9673a6"),
    ("lane_ext", "Enterprise Platforms & Core Bank", 460, "#F5DEDF", "#B36520"),
]

# (id, lane, slot, label, kind) -- slot = Y-row inside the lane (0-based).
# One node per (lane, slot); the engine rejects duplicates.
NODES = [
    ("n_mobile", "lane_client", 3, "Mobile App", "ext_plain"),
    ("n_webhook", "lane_client", 0, "Async Webhook", "ext_plain"),
    ("n_kong", "lane_gw", 3, "Kong API Gateway", "pod_new"),
    ("n_bff", "lane_bff", 3, "bff-sample", "pod_new"),
    ("n_orch_saga", "lane_orch", 3, "orch-sample-saga", "pod_new"),
    ("n_orch_cb", "lane_orch", 0, "orch-sample-callback", "pod_new"),
    ("n_core", "lane_core", 3, "core-sample-engine", "pod_new"),
    ("n_core_cb", "lane_core", 0, "core-sample-scoring", "pod_new"),
    ("n_db", "lane_core", 4, "PostgreSQL\n(sample_db)", "pod_reuse"),
    ("n_redis", "lane_core", 5, "Redis Cache\n(sample_cache)", "pod_reuse"),
    ("n_adapt_cb", "lane_adapt", 0, "adaptor-sample-cb", "pod_new"),
    ("n_adapt_pay", "lane_adapt", 3, "adaptor-sample-pay", "pod_new"),
    ("n_bureau", "lane_ext", 0, "External Bureau", "ext"),
    ("n_bank", "lane_ext", 3, "Core Bank (Vault)", "ext"),
    ("n_kafka", "lane_ext", 5, "Kafka Event Bus", "ext"),
]

# (id, src, dst, kind, label) -- label must obey LABEL_MAX_*; corridors are
# chosen automatically: any edge whose target sits LEFT of its source goes
# through the top corridor (returns/callbacks) unless route="bottom".
EDGES = [
    ("e_main", "n_mobile", "n_kong", "sync", "HTTPS"),
    ("e_bff", "n_kong", "n_bff", "sync", "route"),
    ("e_saga", "n_bff", "n_orch_saga", "sync", "REST"),
    ("e_core", "n_orch_saga", "n_core", "sync", "domain call"),
    ("e_db", "n_core", "n_db", "sync", "persist"),
    ("e_cache", "n_core", "n_redis", "sync", "cache"),
    ("e_pay", "n_orch_saga", "n_adapt_pay", "sync", "payout"),
    ("e_bank", "n_adapt_pay", "n_bank", "sync", "mTLS"),
    ("e_hook_in", "n_bureau", "n_webhook", "async", "webhook"),
    ("e_hook_route", "n_webhook", "n_orch_cb", "async", "dispatch"),
    ("e_score", "n_orch_cb", "n_core_cb", "sync", "score"),
    ("e_adapt_cb", "n_core_cb", "n_adapt_cb", "sync", "notify"),
    ("e_bureau_cb", "n_adapt_cb", "n_bureau", "async", "confirm"),
    ("e_kafka", "n_orch_saga", "n_kafka", "event", "loan.events"),
]


def build_model():
    """Return (lanes, nodes, edges) for this diagram. Edit tables above."""
    return LANES, NODES, EDGES


# ------------------------------------------------------------- layout engine
def _validate_model(lanes, nodes, edges):
    lane_ids = {l[0] for l in lanes}
    node_ids = set()
    seen_slots = set()
    problems = []
    for nid, lane, slot, label, kind in nodes:
        if lane not in lane_ids:
            problems.append(f"node {nid}: unknown lane {lane}")
        if (lane, slot) in seen_slots:
            problems.append(f"node {nid}: slot {slot} in {lane} taken")
        seen_slots.add((lane, slot))
        lines = label.split("\n")
        if len(lines) > LABEL_MAX_LINES:
            problems.append(f"node {nid}: label has {len(lines)} lines")
        if any(len(ln) > LABEL_MAX_CHARS for ln in lines):
            problems.append(f"node {nid}: label exceeds {LABEL_MAX_CHARS} chars")
        if kind not in STYLES:
            problems.append(f"node {nid}: unknown kind {kind}")
        node_ids.add(nid)
    for eid, src, dst, kind, label in edges:
        for ref in (src, dst):
            if ref not in node_ids:
                problems.append(f"edge {eid}: unknown endpoint {ref}")
        if kind not in EDGE_STYLES:
            problems.append(f"edge {eid}: unknown kind {kind}")
        lines = label.split("\n")
        if len(lines) > LABEL_MAX_LINES or any(
                len(ln) > LABEL_MAX_CHARS for ln in lines):
            problems.append(f"edge {eid}: label violates the label law")
    if problems:
        raise SystemExit("model validation failed:\n  " + "\n  ".join(problems))
    return node_ids


def _layout(lanes, nodes):
    """Absolute geometry: node id -> (x, y, w, h, lane_index, slot_y_center)."""
    slot_of = {(n[1], n[2]): n[0] for n in nodes}
    max_slot = max((n[2] for n in nodes), default=0)
    lane_h = TITLE_BAND + (max_slot + 1) * SLOT_H + SLOT_BOTTOM_PAD
    geo = {}
    x = PAGE_MARGIN_X
    for li, (lane_id, _t, w, _f, _s) in enumerate(lanes):
        for nid, lane, slot, _label, kind in nodes:
            if lane != lane_id:
                continue
            _style, nw, nh = STYLES[kind]
            slot_center = (LANE_TOP + TITLE_BAND + slot * SLOT_H
                           + SLOT_H // 2)
            geo[nid] = (x + (w - nw) // 2, slot_center - nh // 2,
                        nw, nh, li, slot_center)
        x += w
    page_w = x + PAGE_MARGIN_X
    page_h = LANE_TOP + lane_h + CORRIDOR_BOTTOM_GAP + 70
    return geo, page_w, page_h, lane_h


def _edge_label_cells(edge_id, text, rel_x):
    """Label as a child cell pinned along the edge (rel_x in [-1, 1])."""
    return (f'        <mxCell id="{edge_id}_lbl" value="{esc(text)}" '
            f'style="edgeLabel;html=1;align=center;verticalAlign=middle;'
            f'resizable=0;points=[];fontSize=9;fontColor=#333333;'
            f'labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" '
            f'parent="{edge_id}">\n'
            f'          <mxGeometry x="{rel_x}" relative="1" as="geometry">\n'
            f'            <mxPoint as="offset" y="{"-8" if rel_x else "0"}" />\n'
            f'          </mxGeometry>\n        </mxCell>')


def _slot_of_row(row_y):
    """Inverse of the slot-center formula: which slot row a Y belongs to."""
    return round((row_y - LANE_TOP - TITLE_BAND - SLOT_H // 2) / SLOT_H)


def _route(eid, src, dst, kind, geo, ctx):
    """Exit/entry anchors + waypoints. Returns (style_suffix, points_xml).

    Routing law: forward adjacent spans run straight on the row; multi-lane
    spans dip through the inter-row gap band with fewer same-lane hop
    conflicts, exiting vertically so they never share a ray with a straight
    row wire; event busines go through the bottom corridor (the standard's
    own Kafka rule); backward flows get their own top-corridor row; far
    same-lane hops use the lane's inner gutter.
    """
    sx, sy, sw, sh, sli, scy = geo[src]
    tx, ty, tw, th, tli, tcy = geo[dst]
    srow = sy + sh // 2
    trow = ty + th // 2
    if sli == tli:  # same lane
        if abs(scy - tcy) <= SLOT_H:  # adjacent rows: short hop bottom->top
            return ("exitX=0.5;exitY=1;exitDx=0;exitDy=0;"
                    "entryX=0.5;entryY=0;entryDx=0;entryDy=0;", "")
        # further apart: down the lane's inner gutter, never through the
        # node that sits between the two slots
        gx = sx + sw + 22
        pts = (f'<Array as="points">'
               f'<mxPoint x="{gx}" y="{srow}" />'
               f'<mxPoint x="{gx}" y="{trow}" />'
               f'</Array>')
        return ("exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
                "entryX=1;entryY=0.5;entryDx=0;entryDy=0;", pts)
    if tli > sli:   # forward
        occupied = ctx["occupied"]
        if tli - sli == 1 or not any(
                (li, _slot_of_row(srow)) in occupied
                for li in range(sli + 1, tli)):
            return ("exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
                    "entryX=0;entryY=0.5;entryDx=0;entryDy=0;", "")
        if kind == "event":
            # event busines: bottom corridor, one row per edge
            cor = (ctx["lane_bottom"] + CORRIDOR_BOTTOM_GAP
                   + 18 * len(ctx["corridors_bottom"]))
            ctx["corridors_bottom"][eid] = cor
            pts = (f'<Array as="points">'
                   f'<mxPoint x="{sx + sw // 2}" y="{cor}" />'
                   f'<mxPoint x="{tx + tw // 2}" y="{cor}" />'
                   f'</Array>')
            return ("exitX=0.5;exitY=1;exitDx=0;exitDy=0;"
                    "entryX=0.5;entryY=1;entryDx=0;entryDy=0;", pts)
        # dip through an inter-row gap band; pick the side with fewer
        # same-lane hop conflicts; exit vertically so the dip never shares
        # a ray with a straight row wire
        gap_up, gap_down = srow - 60, srow + 60
        up = (ctx["band_conflicts"](gap_up, sli, tli)
              <= ctx["band_conflicts"](gap_down, sli, tli))
        gap = gap_up if up else gap_down
        ex = sx + int(sw * 0.75)
        pts = (f'<Array as="points">'
               f'<mxPoint x="{ex}" y="{gap}" />'
               f'<mxPoint x="{tx - 16}" y="{gap}" />'
               f'</Array>')
        if up:
            return ("exitX=0.75;exitY=0;exitDx=0;exitDy=0;"
                    "entryX=0;entryY=0.5;entryDx=0;entryDy=0;", pts)
        return ("exitX=0.75;exitY=1;exitDx=0;exitDy=0;"
                "entryX=0;entryY=0.5;entryDx=0;entryDy=0;", pts)
    # backward: top corridor. Every backward wire gets its own corridor row
    # so two return flows never share a Y (the checker re-derives and gates).
    corridors_top = ctx["corridors_top"]
    cy = corridors_top.get((src, dst))
    if cy is None:
        cy = CORRIDOR_TOP_Y + 18 * len(corridors_top)
        corridors_top[(src, dst)] = cy
    pts = (f'<Array as="points">'
           f'<mxPoint x="{sx + sw // 2}" y="{cy}" />'
           f'<mxPoint x="{tx + tw // 2}" y="{cy}" />'
           f'</Array>')
    return ("exitX=0.5;exitY=0;exitDx=0;exitDy=0;"
            "entryX=0.5;entryY=0;entryDx=0;entryDy=0;", pts)


def generate_drawio_xml(output_path):
    lanes, nodes, edges = build_model()
    node_ids = _validate_model(lanes, nodes, edges)
    geo, page_w, page_h, lane_h = _layout(lanes, nodes)

    out = []
    out.append('  <diagram name="HLA Overview" id="HLA_Overview">')
    out.append(f'    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" '
               f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
               f'page="1" pageScale="1" pageWidth="{page_w}" '
               f'pageHeight="{page_h}" math="0" shadow="0">')
    out.append("      <root>")
    out.append('        <mxCell id="0" />')
    out.append('        <mxCell id="1" parent="0" />')

    x = PAGE_MARGIN_X
    for lane_id, title, w, fill, stroke in lanes:
        out.append(
            f'        <mxCell id="{lane_id}" parent="1" '
            f'style="rounded=0;whiteSpace=wrap;html=1;fillColor={fill};'
            f'strokeColor={stroke};strokeWidth=1.5;verticalAlign=top;'
            f'fontStyle=1;fontSize=12;align=center;spacingTop=8;" '
            f'value="{esc(title)}" vertex="1">'
            f'<mxGeometry x="{x}" y="{LANE_TOP}" width="{w}" '
            f'height="{lane_h}" as="geometry" /></mxCell>')
        x += w

    for nid, _lane, _slot, label, kind in nodes:
        style, _w, _h = STYLES[kind]
        gx, gy, gw, gh, _li, _sc = geo[nid]
        out.append(
            f'        <mxCell id="{nid}" parent="1" '
            f'style="{style}" value="{esc(label)}" vertex="1">'
            f'<mxGeometry x="{gx}" y="{gy}" width="{gw}" height="{gh}" '
            f'as="geometry" /></mxCell>')

    # label bundling: alternate pinned positions so co-linear wires never
    # stack label text at the same midpoint.
    occupied = {(li, slot) for _nid, lane, slot, _l, _k in nodes
                for li, (lid, *_r) in enumerate(lanes) if lid == lane}

    def band_conflicts(band_y, sli, tli):
        """Same-lane local hops whose vertical run crosses this gap band."""
        n = 0
        for _eid, s, d, _k, _l in edges:
            if geo[s][4] != geo[d][4] or geo[s][4] not in range(sli, tli + 1):
                continue
            y1, y2 = sorted((geo[s][1] + geo[s][3], geo[d][1]))
            if y1 < band_y < y2:
                n += 1
        return n

    ctx = {
        "occupied": occupied,
        "band_conflicts": band_conflicts,
        "corridors_top": {},
        "corridors_bottom": {},
        "lane_bottom": LANE_TOP + lane_h,
    }

    row_seen = {}
    for eid, src, dst, kind, label in edges:
        suffix, pts = _route(eid, src, dst, kind, geo, ctx)
        sli, tli = geo[src][4], geo[dst][4]
        key = (sli, tli, geo[src][5])
        nth = row_seen.get(key, 0)
        row_seen[key] = nth + 1
        rel_x = (-0.6 + 0.35 * (nth % 3)) if nth else 0
        out.append(
            f'        <mxCell id="{eid}" parent="1" target="{dst}" '
            f'source="{src}" edge="1" '
            f'style="{EDGE_STYLES[kind]};{suffix}">'
            f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry>'
            f"</mxCell>")
        if label:
            out.append(_edge_label_cells(eid, label, rel_x))

    out.append("      </root>")
    out.append("    </mxGraphModel>")
    out.append("  </diagram>")
    page_1 = "\n".join(out)

    page_2 = load_standard_tab_xml()
    full = f'<mxfile host="app.diagrams.net" pages="2">\n{page_1}\n{page_2}\n</mxfile>'
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full)
    ET.parse(output_path)
    print(f"Generated 2-page HLA draw.io XML: {output_path} "
          f"({len(nodes)} nodes, {len(edges)} edges, page {page_w}x{page_h})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    generate_drawio_xml(sys.argv[1])
