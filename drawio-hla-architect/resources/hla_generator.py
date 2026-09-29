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

`status` on an edge is "impl" (built, the default) or "spec" (designed but not
built): one model renders the design view, the implementation view, or both
with the gap marked, so a design and its code cannot drift into two diagrams
that disagree about what exists.

Usage: edit the tables in build_model(), then
  python3 hla_generator.py out.drawio.xml                 # both, gap marked
  python3 hla_generator.py out.drawio.xml --from impl     # only what is built
  python3 hla_generator.py out.drawio.xml --from spec     # only what is designed
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- layout pins
PAGE_MARGIN_X = 50
LANE_TOP = 170          # lanes start here; above it sits the title band and
CORRIDOR_TOP_Y = 96     # exclusive top-corridor route (never crosses headers)
TITLE_BAND = 60         # lane-header zone; first slot starts below it
SLOT_H = 90             # one node + its below-icon label per slot row
SLOT_BOTTOM_PAD = 40
CORRIDOR_BOTTOM_GAP = 50
LABEL_MAX_CHARS = 24
LABEL_MAX_LINES = 2
MAX_CROSSINGS = 2       # non-planarity is inherent - Kafka and the core hubs
                        # make a K3,3-like subgraph - and every edge is
                        # arc-jumped, so a budgeted crossing renders as a
                        # bridge rather than a tangle

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
    ("n_kyc", "lane_ext", 6, "KYC Bureau\n(planned)", "ext", "spec"),
]

# (id, src, dst, kind, label, status)
#   status -- where this edge exists:
#     "impl"  implemented in the repository (default; the diagram's subject)
#     "spec"  designed but not built yet
#   Rendering is identical; only the spec/impl summary changes. One model, one
#   picture, so a design and its implementation cannot silently diverge into
#   two diagrams that disagree about what exists. `python3 hla_generator.py
#   out.xml --from spec` renders the full design; `--from impl` renders only
#   what is built; the default renders both and marks the gap in the title.
EDGES = [
    ("e_main", "n_mobile", "n_kong", "sync", "HTTPS", "impl"),
    ("e_bff", "n_kong", "n_bff", "sync", "route", "impl"),
    ("e_saga", "n_bff", "n_orch_saga", "sync", "REST", "impl",
     ("A1", "A2", "A3", "A4", "B1")),
    ("e_core", "n_orch_saga", "n_core", "sync", "domain call", "impl"),
    ("e_db", "n_core", "n_db", "sync", "persist", "impl"),
    ("e_cache", "n_core", "n_redis", "sync", "cache", "impl"),
    ("e_pay", "n_orch_saga", "n_adapt_pay", "sync", "payout", "impl"),
    ("e_bank", "n_adapt_pay", "n_bank", "sync", "mTLS", "impl"),
    ("e_hook_in", "n_bureau", "n_webhook", "async", "webhook", "impl"),
    ("e_hook_route", "n_webhook", "n_orch_cb", "async", "dispatch", "impl"),
    ("e_score", "n_orch_cb", "n_core_cb", "sync", "score", "impl"),
    ("e_adapt_cb", "n_core_cb", "n_adapt_cb", "sync", "notify", "impl"),
    ("e_bureau_cb", "n_adapt_cb", "n_bureau", "async", "confirm", "impl"),
    ("e_kafka", "n_orch_saga", "n_kafka", "event", "loan.events", "impl",
     ("C1", "C2", "C3", "C4", "C5", "D1", "D2", "D3")),
    ("e_kyc", "n_orch_saga", "n_kyc", "sync", "planned KYC", "spec"),
]


def edges_normalize(edges):
    """Accept 5/6/7-tuple edges; absent status means implemented.

    The optional 7th element is a tuple of step ids the wire carries (a trace
    diagram). The label then reads "verb" on line one and the compressed step
    list on line two, and the compression is verified to round-trip: a label
    that names fewer steps than the wire carries is a silent data loss.
    """
    out = []
    for e in edges:
        e = tuple(e)
        if len(e) == 5:
            e = (*e, "impl")
        if len(e) == 6:
            e = (*e, ())
        out.append(e)
    return out


def ranges(ids):
    """Collapse consecutive ids of one flow and depth into a range.

    The running range is tracked by its START and its END. Extending it from
    the previous element alone rewrites the range in place and silently drops
    every id before it (A2, A3, A4 became "A3-A4") - exactly the quiet data
    loss a diagram must never carry.
    """
    out, start_id, end_num, key0 = [], None, None, None
    for sid in ids:
        m = re.fullmatch(r"([A-Z])(\d+)((?:\.\d+)*)", sid)
        if m and start_id is not None and (m.group(1), m.group(3)) == key0 \
                and int(m.group(2)) == end_num + 1:
            end_num = int(m.group(2))
            out[-1] = f"{start_id}-{sid}"
            continue
        out.append(sid)
        start_id = sid
        end_num = int(m.group(2)) if m else None
        key0 = (m.group(1), m.group(3)) if m else None
    return out


def label_ids(lines):
    """Every step id a compressed label enumerates, ranges expanded."""
    ids = []
    for ln in lines:
        for part in ln.split(","):
            r = re.fullmatch(r"([A-Z])(\d+)((?:\.\d+)*)-([A-Z])(\d+)((?:\.\d+)*)",
                             part)
            if r and (r.group(1), r.group(3)) == (r.group(4), r.group(6)):
                ids += [f"{r.group(1)}{n}{r.group(3)}"
                        for n in range(int(r.group(2)), int(r.group(5)) + 1)]
            elif part:
                ids.append(part)
    return ids


def step_label(label, steps, max_chars=LABEL_MAX_CHARS):
    """"verb" + the compressed step list, or the bracket form when too long.

    `..` marks a bracket: a list too long to enumerate is shown as
    "A2.2..B10.2 (15)" and enumerated elsewhere (the trace page), which is
    honest about the fact that the label does not name every step. `-` means an
    exact consecutive range and is verified to round-trip.
    """
    if not steps:
        return label
    clean = [s.strip() for s in steps if s.strip()]
    line = ",".join(ranges(clean))
    if len(line) > max_chars:
        # too long to enumerate: a bracket the trace page expands
        line = f"{clean[0]}..{clean[-1]} ({len(clean)})"
    return f"{label}\n{line}" if label else line


def nodes_normalize(nodes):
    """Accept 5- or 6-tuple nodes; absent status means implemented."""
    return [n if len(n) == 6 else (*n, "impl") for n in nodes]


def build_model():
    """Return (lanes, nodes, edges) for this diagram. Edit tables above."""
    return LANES, NODES, EDGES


# ------------------------------------------------------------- layout engine
def _validate_model(lanes, nodes, edges):
    lane_ids = {l[0] for l in lanes}
    node_ids = set()
    seen_slots = set()
    problems = []
    for nid, lane, slot, label, kind, status in nodes:
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
        if status not in ("impl", "spec"):
            problems.append(
                f"node {nid}: status {status!r} is neither 'impl' (built) "
                f"nor 'spec' (designed)")
        node_ids.add(nid)
    for e in edges:
        eid, src, dst, kind, label, status, steps = e
        for ref in (src, dst):
            if ref not in node_ids:
                problems.append(f"edge {eid}: unknown endpoint {ref}")
        if kind not in EDGE_STYLES:
            problems.append(f"edge {eid}: unknown kind {kind}")
        if status not in ("impl", "spec"):
            problems.append(
                f"edge {eid}: status {status!r} is neither 'impl' (built) "
                f"nor 'spec' (designed)")
        lines = step_label(label, steps).split("\n")
        if len(lines) > LABEL_MAX_LINES or any(
                len(ln) > LABEL_MAX_CHARS for ln in lines):
            problems.append(f"edge {eid}: label violates the label law")
        if steps:
            shown = lines[-1]
            if ".." not in shown and label_ids([shown]) != list(steps):
                problems.append(
                    f"edge {eid}: step label {shown!r} does not reproduce "
                    f"{list(steps)}")
    # connectivity is a property of the MODEL, not of a rendered view: check it
    # here, once, over every edge, so a filtered render need not re-derive it
    srcs = {e[1] for e in edges}
    dsts = {e[2] for e in edges}
    for nid in node_ids:
        if nid not in srcs and nid not in dsts:
            problems.append(f"node {nid}: no edge connects it (orphan)")
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
        for nid, lane, slot, _label, kind, _st in nodes:
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


def _edge_label_cells(edge_id, text, rel_x, off_y):
    """Label as a child cell pinned along the edge (rel_x in [-1, 1])."""
    return (f'        <mxCell id="{edge_id}_lbl" value="{esc(text)}" '
            f'style="edgeLabel;html=1;align=center;verticalAlign=middle;'
            f'resizable=0;points=[];fontSize=9;fontColor=#333333;'
            f'labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" '
            f'parent="{edge_id}">\n'
            f'          <mxGeometry x="{rel_x:.4f}" relative="1" as="geometry">\n'
            f'            <mxPoint as="offset" y="{off_y}" />\n'
            f'          </mxGeometry>\n        </mxCell>')


# ------------------------------------------------------- label placement
CHAR_W = 0.62
LABEL_FS = 9


def _seg_of_poly(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]),
            abs(b[0] - a[0]) or 1, abs(b[1] - a[1]) or 1)


def _hit(a, b):
    return (a[0] < b[0] + b[2] and b[0] < a[0] + a[2]
            and a[1] < b[1] + b[3] and b[1] < a[1] + a[3])


def _polyline_of(style_suffix, pts_xml, geo, src, dst):
    """The polyline the checker will derive, from the emitted geometry."""
    sx, sy, sw, sh, _li, _sc = geo[src]
    tx, ty, tw, th, _tl, _tc = geo[dst]

    def val(key):
        m = re.search(rf"(?:^|;){key}=([^;]*)", style_suffix)
        return float(m.group(1)) if m else None

    ex, ey = val("exitX"), val("exitY")
    nx, ny = val("entryX"), val("entryY")
    pts = []
    if ex is not None and ey is not None:
        pts.append((sx + ex * sw, sy + ey * sh))
    pts += [(float(m.group(1)), float(m.group(2)))
            for m in re.finditer(r'<mxPoint x="(-?[\d.]+)" y="(-?[\d.]+)" />',
                                 pts_xml)]
    if nx is not None and ny is not None:
        pts.append((tx + nx * tw, ty + ny * th))
    return pts


def _label_rect(poly, text, frac, off_y, fs=LABEL_FS):
    lines = text.split("\n")
    lw = max(len(ln) for ln in lines) * CHAR_W * fs + 10
    lh = len(lines) * fs * 1.5 + 4
    segs = [((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            for a, b in zip(poly, poly[1:])]
    total = sum(segs) or 1.0
    target, acc = total * frac, 0.0
    mx, my = poly[0]
    for (a, b), seg in zip(zip(poly, poly[1:]), segs):
        if acc + seg >= target:
            t = (target - acc) / seg if seg else 0.0
            mx, my = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            break
        acc += seg
    return (mx - lw / 2, my - lh / 2 + off_y, lw, lh)


def _place_label(eid, src, dst, text, poly, others, node_boxes, geo):
    """(rel_x, off_y) chosen so the label clears nodes and other wires.

    The checker fails a label overlapping a node and warns when one sits on a
    wire, so the position is searched rather than guessed: `frac` walks the
    wire and `off_y` lifts the text clear. The first collision-free spot wins,
    and the search starts at the midpoint, where a reader looks for it.
    """
    fracs = [0.5] + sorted((i / 40 for i in range(1, 40)),
                           key=lambda f: abs(f - 0.5))
    for off_y in (0, -8, 8, -16, 16):
        for frac in fracs:
            box = _label_rect(poly, text, frac, off_y)
            if any(_hit(box, nb) or (lb and _hit(box, lb))
                   for nid, (nb, lb) in node_boxes.items()
                   if nid not in (src, dst)):
                continue
            if any(_hit(box, _seg_of_poly(a, b))
                   for other, opoly in others.items() if other != eid
                   for a, b in zip(opoly, opoly[1:])):
                continue
            return 2 * frac - 1, off_y
    return 0.0, -8


def _slot_of_row(row_y):
    """Inverse of the slot-center formula: which slot row a Y belongs to."""
    return round((row_y - LANE_TOP - TITLE_BAND - SLOT_H // 2) / SLOT_H)


def _overlap(a, b):
    """True when two spans share more than a point."""
    return not (a[1] <= b[0] or b[1] <= a[0])


class _Channels:
    """Interval-coloured verticals and corridor rows, in node-free space.

    A vertical or a corridor row is a LINE that wires share, not a resource
    each wire owns: a line is reused whenever the new span cannot touch a span
    already on it, so two wires on one line are safe BY CONSTRUCTION and the
    checker's "wires stacked" rule cannot fire. One line per wire is what made
    a 57-node model emit 87 stacked-wire violations.

    Verticals live in a lane's node-free side channel. Nodes are centred in
    their lane, so the strip left of the node column and the strip right of it
    are node-free by construction, and a leg placed there cannot pass through a
    node. Pinning legs to node CENTRES is where the 192 "wire passes through
    node" violations came from: the centre of one node is inside every node
    stacked above or below it in the same lane.
    """

    COL_STEP = 8
    COL_CLEAR = 10
    ROW_CLEAR = 10
    BUS_PITCH = 16

    def __init__(self, lanes, nodes, geo, lane_h):
        self.geo = geo
        self.lane_of = {n[0]: n[1] for n in nodes}
        self.lane_x, x = {}, PAGE_MARGIN_X
        for lid, _t, w, _f, _s in lanes:
            self.lane_x[lid] = x
            x += w
        self.width = {l[0]: l[2] for l in lanes}
        self.rows = []
        self.lane_bottom = LANE_TOP + lane_h
        self.bus_bottom = self.lane_bottom
        self.max_slot = max((n[2] for n in nodes), default=0)
        self.col_lo, self.col_hi = {}, {}
        for lane in self.lane_x:
            xs = [(geo[n[0]][0], geo[n[0]][0] + geo[n[0]][2])
                  for n in nodes if n[1] == lane]
            if xs:
                self.col_lo[lane] = min(a for a, _b in xs)
                self.col_hi[lane] = max(b for _a, b in xs)
        self.left, self.right = {}, {}

    def _bounds(self, lane, side):
        lo = self.lane_x[lane]
        hi = lo + self.width[lane]
        if side == "left":
            return lo + 4, max(lo + 6, self.col_lo.get(lane, lo + 10) - 4)
        return min(hi - 6, self.col_hi.get(lane, hi - 10) + 4), hi - 4

    def col(self, lane, side, lo, hi):
        """A vertical x in `lane`'s `side` channel, clear over y in [lo, hi]."""
        chan = self.left if side == "left" else self.right
        lo_x, hi_x = self._bounds(lane, side)
        if lo > hi:
            lo, hi = hi, lo
        step = self.COL_STEP if side == "right" else -self.COL_STEP
        for i in range(max(int(abs(hi_x - lo_x) // self.COL_STEP) + 1, 1)):
            x = int(hi_x - i * self.COL_STEP) if side == "right" \
                else int(lo_x + i * self.COL_STEP)
            if any(abs(x - u) < self.COL_CLEAR for u in chan):
                continue
            if any(_overlap((lo, hi), sp) for sp in chan.get(x, [])):
                continue
            chan.setdefault(x, []).append((lo, hi))
            return x
        x = int(hi_x if side == "right" else lo_x)
        while any(abs(x - u) < self.COL_CLEAR for u in chan):
            x += step
        chan.setdefault(x, []).append((lo, hi))
        return x

    def corridor(self, lo_x, hi_x, below_slot):
        """A corridor row clear over [lo_x, hi_x], for forward multi-lane wires.

        Preference: the gap band just under the deepest row the wire leaves
        (nearest the boxes, so the wire stays compact), then any later band,
        then the bus below the lanes. A band reuses a row whenever the span is
        clear, so the canvas grows only when the bands are genuinely full.

        Offsets are measured from the TOP of the slot row, so SLOT_H + n lands
        inside the INTER-ROW gap; anything smaller would put the wire inside
        the node row itself.
        """
        def free(y):
            return not any(_overlap((lo_x, hi_x), (a, b))
                           for a, b, yy in self.rows
                           if abs(y - yy) < self.ROW_CLEAR)

        for slot in range(max(below_slot, 0), self.max_slot + 2):
            for off in (SLOT_H + 10, SLOT_H + 22):
                y = LANE_TOP + TITLE_BAND + slot * SLOT_H + off
                if y <= self.lane_bottom - 8 and free(y):
                    self.rows.append((lo_x, hi_x, y))
                    return y
        y = self.lane_bottom + 30
        while not free(y):
            y += self.BUS_PITCH
        self.rows.append((lo_x, hi_x, y))
        self.bus_bottom = max(self.bus_bottom, y)
        return y

    def top_corridor(self, lo_x, hi_x, floor=24):
        """A corridor row above the lanes, for right-to-left returns.

        Bounded by `floor`: a return that would climb past it has left the
        page, which is unreadable and which the checker rejects. Such a wire
        falls back to the bus below the lanes.
        """
        y = CORRIDOR_TOP_Y
        while any(_overlap((lo_x, hi_x), (a, b))
                  for a, b, yy in self.rows if abs(y - yy) < self.ROW_CLEAR):
            y -= self.BUS_PITCH
            if y < floor:
                return None
        self.rows.append((lo_x, hi_x, y))
        return y


# Two wires leaving one side of one node must not share a y, or their first
# legs are collinear and the checker reports them stacked.
OFFSETS = (0, -11, 11, -22, 22, -33, 33, -17, 17)


def _offset(used):
    for o in OFFSETS:
        if o not in used:
            used.add(o)
            return o
    used.add(0)
    return 0


def _route(eid, src, dst, kind, geo, ctx):
    """Exit/entry anchors + waypoints. Returns (style_suffix, points_xml).

    Routing law: forward adjacent spans run straight on the row; multi-lane
    spans dip through a gap band; event wires take a corridor; backward flows
    return above the lanes; far same-lane hops use the lane's side channel.

    Three things make this scale, and they are what the first engine lacked: a
    vertical leg is allocated in the lane's NODE-FREE side channel instead of
    on the node centre (so it cannot pass through a node); each edge's anchor
    is offset along the node's edge (so two legs never share a ray); and
    corridor rows are shared by span, not owned one-per-edge.

    Every waypoint's y is the ANCHOR's y, never the bare row y: a waypoint on
    the row y with an anchor at row y + offset makes the first segment
    diagonal, and the checker then sees crossings that do not exist.
    """
    sx, sy, sw, sh, sli, scy = geo[src]
    tx, ty, tw, th, tli, tcy = geo[dst]
    srow, trow = sy + sh // 2, ty + th // 2
    chan = ctx["chan"]
    lane_s, lane_t = ctx["lane_of"][src], ctx["lane_of"][dst]
    s_dy = _offset(ctx["used_off"].setdefault((src, "right"), set()))
    t_dy = _offset(ctx["used_off"].setdefault((dst, "left"), set()))
    s_ay, t_ay = srow + s_dy, trow + t_dy

    def anchors(side_s, side_t):
        return (f'{"exitX=1" if side_s == "right" else "exitX=0"};'
                f'exitY={0.5 + s_dy / sh:.3f};exitDx=0;exitDy=0;'
                f'{"entryX=0" if side_t == "left" else "entryX=1"};'
                f'entryY={0.5 + t_dy / th:.3f};entryDx=0;entryDy=0;')

    if sli == tli:
        # Same lane. Both cases use the lane's side channel, never the node
        # centre: the centre of one node is inside every node above and below
        # it in the same lane.
        x = chan.col(lane_s, "right", min(s_ay, t_ay), max(s_ay, t_ay))
        pts = (f'<Array as="points">'
               f'<mxPoint x="{x}" y="{s_ay:.0f}" />'
               f'<mxPoint x="{x}" y="{t_ay:.0f}" />'
               f'</Array>')
        return (anchors("right", "right"), pts)

    if tli > sli and (tli - sli == 1 or not any(
            (li, _slot_of_row(srow)) in ctx["occupied"]
            for li in range(sli + 1, tli))):
        # Forward along the row: no corridor, no vertical leg. The per-edge
        # anchor offsets keep two wires on one row parallel, not collinear.
        return (anchors("right", "left"), "")

    if tli > sli:
        below = max(_slot_of_row(srow), _slot_of_row(trow))
        cor = chan.corridor(min(sx, tx), max(sx + sw, tx + tw), below)
        v1 = chan.col(lane_s, "right", s_ay, cor)
        v2 = chan.col(lane_t, "left", t_ay, cor)
        pts = (f'<Array as="points">'
               f'<mxPoint x="{v1}" y="{s_ay:.0f}" />'
               f'<mxPoint x="{v1}" y="{cor}" />'
               f'<mxPoint x="{v2}" y="{cor}" />'
               f'<mxPoint x="{v2}" y="{t_ay:.0f}" />'
               f'</Array>')
        return (anchors("right", "left"), pts)

    # Backward: over the top of the lanes, or under them when the top band is
    # full - a wire must stay on the page.
    cor = chan.top_corridor(min(sx, tx), max(sx + sw, tx + tw))
    if cor is None:
        cor = chan.corridor(min(sx, tx), max(sx + sw, tx + tw),
                            max(_slot_of_row(srow), _slot_of_row(trow)))
    v1 = chan.col(lane_s, "left", s_ay, cor)
    v2 = chan.col(lane_t, "right", t_ay, cor)
    pts = (f'<Array as="points">'
           f'<mxPoint x="{v1}" y="{s_ay:.0f}" />'
           f'<mxPoint x="{v1}" y="{cor}" />'
           f'<mxPoint x="{v2}" y="{cor}" />'
           f'<mxPoint x="{v2}" y="{t_ay:.0f}" />'
           f'</Array>')
    return (anchors("left", "right"), pts)


def generate_drawio_xml(output_path, source="both"):
    """Render the model. `source` is "impl", "spec" or "both" (default).

    "both" draws every edge and marks the unbuilt ones, so one picture answers
    "what is designed" and "what exists"; "impl" draws only built edges (the
    implementation view); "spec" draws only designed edges (the target view).

    Edges are filtered, nodes are not, and the asymmetry is deliberate: a wire
    drawn for something that does not exist is a false claim, while hiding a
    component loses the reader's bearings. A node with no edge in the current
    view is therefore dimmed - "nothing here yet" - instead of deleted.
    """
    lanes, nodes, edges = build_model()
    nodes = nodes_normalize(nodes)
    edges = edges_normalize(edges)
    all_edges = edges
    if source == "impl":
        edges = [e for e in edges if e[5] == "impl"]
    elif source == "spec":
        edges = [e for e in edges if e[5] == "spec"]
    wired = {n for e in edges for n in (e[1], e[2])}
    # validate the WHOLE model: a filtered view must not hide a broken one
    node_ids = _validate_model(lanes, nodes, all_edges)
    geo, page_w, page_h, lane_h = _layout(lanes, nodes)

    # Route before emitting anything: the page must be tall enough for the bus
    # rows the router actually used, and the header carries that height.
    occupied = {(li, slot) for _nid, lane, slot, _l, _k, _st in nodes
                for li, (lid, *_r) in enumerate(lanes) if lid == lane}

    def band_conflicts(band_y, sli, tli):
        """Same-lane local hops whose vertical run crosses this gap band."""
        n = 0
        for _eid, s_, d_, _k, _l, _st, _sp in edges:
            if geo[s_][4] != geo[d_][4] or geo[s_][4] not in range(sli, tli + 1):
                continue
            y1, y2 = sorted((geo[s_][1] + geo[s_][3], geo[d_][1]))
            if y1 < band_y < y2:
                n += 1
        return n

    ctx = {
        "occupied": occupied,
        "band_conflicts": band_conflicts,
        "chan": _Channels(lanes, nodes, geo, lane_h),
        "lane_of": {n[0]: n[1] for n in nodes},
        "used_off": {},
        "lane_bottom": LANE_TOP + lane_h,
    }
    routes = {eid: _route(eid, src, dst, kind, geo, ctx)
              for eid, src, dst, kind, _label, _st, _sp in edges}
    page_h = max(page_h, ctx["chan"].bus_bottom + 60)

    # node boxes and their label boxes, as the checker derives them, so label
    # placement can avoid them
    node_boxes = {}
    for nid, _lane, _slot, label, kind, _st in nodes:
        gx, gy, gw, gh, _li, _sc = geo[nid]
        style = STYLES[kind][0]
        lines = label.split("\n")
        lw = max(len(ln) for ln in lines) * CHAR_W * 9.5 + 10
        lh = len(lines) * 9.5 * 1.5 + 4
        if "verticalLabelPosition=bottom" in style:
            lb = (gx + gw / 2 - lw / 2, gy + gh, lw, lh)
        else:
            lb = (gx + gw / 2 - lw / 2, gy + gh / 2 - lh / 2, lw, lh)
        node_boxes[nid] = ((gx, gy, gw, gh), lb)

    polys = {eid: _polyline_of(sfx, pts, geo, src, dst)
             for eid, src, dst, _k, _l, _st, _sp in edges
             for sfx, pts in [routes[eid]]}

    out = []
    out.append('  <diagram name="HLA Overview" id="HLA_Overview">')
    out.append(f'    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" '
               f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
               f'page="1" pageScale="1" pageWidth="{page_w}" '
               f'pageHeight="{page_h}" math="0" shadow="0">')
    out.append("      <root>")
    out.append('        <mxCell id="0" />')
    out.append('        <mxCell id="1" parent="0" />')
    n_spec = sum(1 for e in all_edges if e[5] == "spec")
    n_impl = len(all_edges) - n_spec
    if source == "impl":
        caption = f"Implementation view - {n_impl} edge(s) built"
    elif source == "spec":
        caption = f"Design view - {n_spec} edge(s) specified"
    else:
        caption = (f"Design and implementation - {n_impl} built"
                   + (f", {n_spec} planned (dashed grey)" if n_spec else ""))
    out.append(
        f'        <mxCell id="title" parent="1" style="text;html=1;'
        f'strokeColor=none;fillColor=none;align=left;verticalAlign=middle;'
        f'whiteSpace=wrap;rounded=0;fontSize=13;fontStyle=1;" '
        f'value="{esc(caption)}" vertex="1">'
        f'<mxGeometry x="{PAGE_MARGIN_X}" y="44" width="900" height="26" '
        f'as="geometry" /></mxCell>')
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

    for nid, _lane, _slot, label, kind, status in nodes:
        style, _w, _h = STYLES[kind]
        if status == "spec":
            # designed, not built: grey and dashed, so a plan never reads as a
            # fact at a glance
            style = (re.sub(r"fillColor=#[0-9A-Fa-f]{6}", "fillColor=#F5F5F5",
                            style)
                     + "dashed=1;"
                     + re.sub(r"strokeColor=#[0-9A-Fa-f]{6}",
                              "strokeColor=#9E9E9E", style))
        if nid not in wired:
            # declared but unwired in this view (its edges are the other
            # source): keep it on the page, visibly inactive
            style = re.sub(r"strokeColor=#[0-9A-Fa-f]{6}",
                           "strokeColor=#BFBFBF", style)
            style = re.sub(r"fillColor=#[0-9A-Fa-f]{6}",
                           "fillColor=#F5F5F5", style)
        gx, gy, gw, gh, _li, _sc = geo[nid]
        out.append(
            f'        <mxCell id="{nid}" parent="1" '
            f'style="{style}" value="{esc(label)}" vertex="1">'
            f'<mxGeometry x="{gx}" y="{gy}" width="{gw}" height="{gh}" '
            f'as="geometry" /></mxCell>')

    for eid, src, dst, kind, label, status, steps in edges:
        label = step_label(label, steps)
        suffix, pts = routes[eid]
        # A planned edge must LOOK planned, or drawing both views is a lie:
        # grey and short-dashed reads as "not built" at a glance.
        style = EDGE_STYLES[kind]
        if status == "spec":
            style = (re.sub(r"strokeColor=#[0-9A-Fa-f]{6}",
                            "strokeColor=#9E9E9E", style)
                     + "dashed=1;dashPattern=4 4;")
        if label:
            rel_x, off_y = _place_label(eid, src, dst, label, polys[eid],
                                        polys, node_boxes, geo)
        else:
            rel_x, off_y = 0.0, 0
        out.append(
            f'        <mxCell id="{eid}" parent="1" target="{dst}" '
            f'source="{src}" edge="1" '
            f'style="{style};{suffix}">'
            f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry>'
            f"</mxCell>")
        if label:
            out.append(_edge_label_cells(eid, label, rel_x, off_y))

    out.append("      </root>")
    out.append("    </mxGraphModel>")
    out.append("  </diagram>")
    page_1 = "\n".join(out)

    page_2 = load_standard_tab_xml()
    full = f'<mxfile host="app.diagrams.net" pages="2">\n{page_1}\n{page_2}\n</mxfile>'

    # Self-gate: the engine must not be able to emit a file its own checker
    # rejects. A model that cannot route cleanly is a MODELLING problem (too
    # many edges on one slot, a label over the law, too few slots), so it stops
    # here with the violations listed instead of being discovered in review.
    import io
    if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import verify_layout
    # connectivity was proven on the whole model above, so the per-view check
    # is off: a filtered view legitimately shows unwired components
    violations, warnings = verify_layout.verify(
        io.StringIO(full), MAX_CROSSINGS, quiet=True,
        require_connectivity=False)
    if violations:
        detail = "\n  ".join(violations[:20])
        raise SystemExit(
            f"generated diagram fails its own layout gate "
            f"({len(violations)} violation(s)):\n  {detail}\n"
            f"fix the model (slots, edge kind, labels), not the XML")
    # written only after the gate passes: a refused model leaves no file behind
    # for someone to open and trust
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full)
    ET.parse(output_path)
    print(f"Generated 2-page HLA draw.io XML: {output_path} "
          f"({len(nodes)} nodes, {len(edges)} edges, "
          f"page {page_w:.0f}x{page_h:.0f}, gate PASS, "
          f"{len(warnings)} warning(s))")


def _parse_args(argv):
    """(output_path, source) from CLI args; `--from impl|spec|both`."""
    source, positional = "both", []
    i = 0
    while i < len(argv):
        if argv[i] == "--from":
            if i + 1 >= len(argv) or argv[i + 1] not in ("impl", "spec", "both"):
                raise SystemExit("--from takes impl, spec or both")
            source = argv[i + 1]
            i += 2
            continue
        positional.append(argv[i])
        i += 1
    if len(positional) != 1:
        raise SystemExit(__doc__)
    return positional[0], source


if __name__ == "__main__":
    out, src = _parse_args(sys.argv[1:])
    generate_drawio_xml(out, src)
