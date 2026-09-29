#!/usr/bin/env python3
"""Layout quality gate for HLA draw.io files (stdlib only).

Runs four checks over page 1 of a .drawio.xml and exits non-zero when any
fails, so "clean layout" is a gate rather than an eyeball checkbox (SKILL.md
section 6):

  1. connectivity  -- zero orphan nodes; callback receivers fully wired
  2. node overlap  -- component boxes (incl. their label overflow) collide
  3. label hygiene -- edge labels violate the label law, overlap each other,
                      or sit on top of a node
  4. wire discipline -- crossings beyond budget, or two wires stacked on the
                      same line (parallel collinear overlap)

Usage:
  python3 verify_layout.py diagram.drawio.xml [--max-crossings 0]
"""
import re
import sys
import xml.etree.ElementTree as ET

IGNORE_PREFIXES = ("lane_", "col_", "box_", "title", "leg_", "lbl_")
IGNORE_EXACT = {"icon_dcb_vault", "node_ext_kafka_icon"}
LABEL_MAX_CHARS = 24
LABEL_MAX_LINES = 2
CHAR_W = 0.62          # label width estimate per fontSize unit
TOL = 2.0              # coordinate tolerance (px)


def _style_of(cell):
    return cell.get("style", "") or ""


def _style_val(style, key, default=None):
    m = re.search(rf"(?:^|;){key}=([^;]*)", style)
    return m.group(1) if m else default


def _label_lines(value):
    return [ln for ln in str(value or "").split("<br>")] if value else []


def _label_box(x, y, w, h, style, value):
    """Estimated on-canvas bbox of a node's label (below icons, inside boxes)."""
    lines = _label_lines(value)
    if not lines:
        return None
    fs = float(_style_val(style, "fontSize", 10) or 10)
    lw = max(len(ln) for ln in lines) * CHAR_W * fs + 10
    lh = len(lines) * fs * 1.5 + 4
    if _style_val(style, "verticalLabelPosition") == "bottom":
        return (x + w / 2 - lw / 2, y + h, lw, lh)
    return (x + w / 2 - lw / 2, y + h / 2 - lh / 2, lw, lh)

def _title_band_check(cells, geo):
    """A titled container's own title must not strike through its content.

    The reported defect this catches: a white panel box drawn with
    `verticalAlign=top;spacingTop=8` at fontSize 12 renders its title inside
    the top ~28px of the box, and content placed at `box_top + 12` is drawn
    straight through it. Nothing in a per-element check sees this, because the
    title is not a cell and the first child is not overlapping anything.

    Returns [(container_id, child_id, child_y, band_end)].
    """
    out = []
    titled = []
    for cid, c in cells.items():
        if c.get("vertex") != "1" or not cid:
            continue
        st = _style_of(c)
        if not str(c.get("value") or "").strip():
            continue
        # a container: large enough to hold children, and its text is the
        # caption rather than a component name
        g = geo.get(cid)
        if not g or g[2] < 200 or g[3] < 120:
            continue
        if any(cid.startswith(p) for p in ("lane_", "col_")):
            continue
        fs = float(_style_val(st, "fontSize", 12) or 12)
        if _style_val(st, "verticalAlign") != "top":
            continue
        titled.append((cid, g, fs * 1.5 + float(
            _style_val(st, "spacingTop", 0) or 0)))
    for cid, c in cells.items():
        if c.get("vertex") != "1" or not cid or cid in {t[0] for t in titled}:
            continue
        if not str(c.get("value") or "").strip():
            continue
        g = geo.get(cid)
        if not g:
            continue
        for host, hg, band in titled:
            inside = (hg[0] <= g[0] and g[0] + g[2] <= hg[0] + hg[2]
                      and hg[1] <= g[1])
            if inside and g[1] < hg[1] + band - TOL:
                out.append((host, cid, g[1], hg[1] + band))
    return out


# Source-coordinate patterns. A diagram is read by people who do not have the
# repository open: a file name, a function name or a line number is stale the
# next time the code moves, and it pushes the reader out of the diagram and
# into a search. They are a violation, not a style preference.
CODE_DETAIL_PATTERNS = (
    (re.compile(r"\b[\w-]+\.(go|py|java|kt|ts|js|rb|rs|sql|yaml|yml)\b"),
     "source file name"),
    (re.compile(r"\b\w+\(\)"), "function call"),
    (re.compile(r"(?<![\w/.-])\w[\w.-]*/[\w.-]+/(internal|pkg|cmd|src)/"),
     "package path"),
)


def _code_detail(value):
    """The first source coordinate in a cell value, or None."""
    for pat, what in CODE_DETAIL_PATTERNS:
        m = pat.search(value)
        if m:
            return f"{what} {m.group(0)!r}"
    return None


def _cell_lines(value):
    """Cell text split the way the renderer breaks it: <br> and newlines."""
    out = []
    for chunk in str(value or "").split("<br>"):
        out.extend(chunk.split("\n"))
    return out


def _check_text_fit(cells, geo):
    """Cells whose text cannot fit their own box.

    A cell narrower than its text does not shrink the text, it draws it
    through the neighbouring cell - the table's version of a label overlapping
    a node, and the reason a wrapped route list needs its row to grow.
    """
    out = []
    for cid, c in cells.items():
        if c.get("vertex") != "1" or not cid:
            continue
        val = str(c.get("value") or "")
        if not val.strip():
            continue
        st = _style_of(c)
        if not (st.startswith("text;") or ";text;" in st or "background=#" in st):
            continue
        g = geo.get(cid)
        if not g:
            continue
        fs = float(_style_val(st, "fontSize", 10) or 10)
        lines = _cell_lines(val)
        need_w = max(len(ln) for ln in lines) * CHAR_W * fs + 6
        need_h = len(lines) * fs * 1.5 + 2
        if need_w > g[2] + TOL:
            out.append((cid, f"text needs {need_w:.0f}px, box is {g[2]:.0f}px "
                             f"wide", max(lines, key=len)[:40]))
        if need_h > g[3] + TOL:
            out.append((cid, f"text needs {need_h:.0f}px, box is {g[3]:.0f}px "
                             f"tall ({len(lines)} line(s))", lines[0][:40]))
    return out


def _is_palette(diagram):
    """The Standard Colors and Icons page: a legend, not an architecture page.

    It is a catalog of swatches and icon cells, so wire, orphan and fit rules
    do not apply. Structure rules (frontmatter, page order) still do.
    """
    return "color" in (diagram.get("name") or "").lower() or \
        "icon" in (diagram.get("name") or "").lower()


def _abs_geometry(diagram):
    """id -> absolute (x, y, w, h) for every vertex, walking parent offsets."""
    cells = {c.get("id"): c for c in diagram.findall(".//mxCell")}
    geo = {}
    def resolve(cid, seen):
        if cid in geo:
            return geo[cid]
        c = cells.get(cid)
        if c is None or cid in seen:
            return (0, 0, 0, 0)
        g = c.find("mxGeometry")
        x = float(g.get("x", 0)) if g is not None else 0.0
        y = float(g.get("y", 0)) if g is not None else 0.0
        w = float(g.get("width", 0)) if g is not None else 0.0
        h = float(g.get("height", 0)) if g is not None else 0.0
        seen.add(cid)
        px, py, _pw, _ph = resolve(c.get("parent"), seen)
        seen.discard(cid)
        geo[cid] = (x + px, y + py, w, h)
        return geo[cid]
    for cid in cells:
        resolve(cid, set())
    return cells, geo


def _anchor(node_geo, style, is_source):
    x, y, w, h = node_geo
    if is_source:
        fx = float(_style_val(style, "exitX", 1))
        fy = float(_style_val(style, "exitY", 0.5))
    else:
        fx = float(_style_val(style, "entryX", 0))
        fy = float(_style_val(style, "entryY", 0.5))
    return (x + fx * w, y + fy * h)


def _edge_polyline(edge, cells, geo):
    src, dst = edge.get("source"), edge.get("target")
    style = _style_of(edge)
    pts = []
    if src in geo:
        pts.append(_anchor(geo[src], style, is_source=True))
    g = edge.find("mxGeometry")
    if g is not None:
        for p in g.findall("./Array/mxPoint"):
            pts.append((float(p.get("x", 0)), float(p.get("y", 0))))
    if dst in geo:
        pts.append(_anchor(geo[dst], style, is_source=False))
    return pts


def _segments(pts):
    return list(zip(pts, pts[1:]))


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)



def _seg_intersect(p1, p2, p3, p4):
    """'cross' = proper crossing, 'stack' = collinear overlap, None = clear."""
    d1, d2 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    d3, d4 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    if d1 != d2 and d3 != d4:
        return "cross"
    if d1 == d2 == d3 == d4 == 0:
        # collinear: overlap along the shared axis longer than TOL means
        # stacked parallel wires
        horiz = abs(p2[0] - p1[0]) >= abs(p2[1] - p1[1])
        def axis(p):
            return p[0] if horiz else p[1]
        lo = max(min(axis(p1), axis(p2)), min(axis(p3), axis(p4)))
        hi = min(max(axis(p1), axis(p2)), max(axis(p3), axis(p4)))
        if hi - lo > TOL:
            # shared-endpoint fans (two edges leaving one node) are legal
            shared = any(abs(a[0] - c[0]) < TOL and abs(a[1] - c[1]) < TOL
                         for a in (p1, p2) for c in (p3, p4))
            if not shared:
                return "stack"
    return None


def _seg_hits_rect(p1, p2, rect, pad=2.0):
    """True if a segment passes through a node box (shrunk by `pad`)."""
    rx, ry, rw, rh = rect
    box = (rx + pad, ry + pad, max(rw - 2 * pad, 1), max(rh - 2 * pad, 1))
    if _rects_overlap((min(p1[0], p2[0]), min(p1[1], p2[1]),
                       abs(p2[0] - p1[0]) or 1, abs(p2[1] - p1[1]) or 1),
                      box, pad=0):
        corners = [(box[0], box[1]), (box[0] + box[2], box[1]),
                   (box[0], box[1] + box[3]), (box[0] + box[2], box[1] + box[3])]
        edges = [(corners[0], corners[1]), (corners[0], corners[2]),
                 (corners[1], corners[3]), (corners[2], corners[3])]
        if _rects_overlap((p1[0], p1[1], 1, 1), box, pad=0) or \
           _rects_overlap((p2[0], p2[1], 1, 1), box, pad=0):
            return True
        return any(_seg_intersect(p1, p2, a, b) for a, b in edges)
    return False


def _rects_overlap(a, b, pad=1.0):
    return (a[0] < b[0] + b[2] + pad and b[0] < a[0] + a[2] + pad
            and a[1] < b[1] + b[3] + pad and b[1] < a[1] + a[3] + pad)


def _label_midpoint_box(pts, text, frac, off_y, fs):
    """Estimated bbox of an edge label at frac along the polyline."""
    lines = _label_lines(text)
    if not lines or len(pts) < 2:
        return None
    total = sum(((b[0]-a[0])**2 + (b[1]-a[1])**2) ** 0.5
                for a, b in _segments(pts)) or 1.0
    target = total * frac
    acc = 0.0
    mx, my = pts[0]
    for a, b in _segments(pts):
        seg = ((b[0]-a[0])**2 + (b[1]-a[1])**2) ** 0.5
        if acc + seg >= target:
            t = (target - acc) / seg if seg else 0.0
            mx, my = a[0] + t * (b[0]-a[0]), a[1] + t * (b[1]-a[1])
            break
        acc += seg
    lw = max(len(ln) for ln in lines) * CHAR_W * fs + 10
    lh = len(lines) * fs * 1.5 + 4
    return (mx - lw / 2, my - lh / 2 + off_y, lw, lh)


def verify(xml_file, max_crossings=0, quiet=False, bus_depth=240,
           require_connectivity=True):
    """Check a diagram. `xml_file` is a path or any file-like object.

    Returns (violations, warnings). `quiet` suppresses the report so the
    generator can gate its own output in memory before writing it: an engine
    that can emit a file its own gate rejects is how unreadable diagrams reach
    a reviewer in the first place.

    `require_connectivity` is set False only when checking a FILTERED view
    (design-only or implementation-only), where a component with no wire is
    deliberate - its edges belong to the other source. Connectivity is a
    property of the whole model, so the generator checks it once against the
    complete model and not against each subset.
    """
    tree = ET.parse(xml_file)
    diagrams = tree.getroot().findall("diagram")
    p1 = next((d for d in diagrams if "HLA" in d.get("name", "")), diagrams[0])
    cells, geo = _abs_geometry(p1)

    edges = {cid: c for cid, c in cells.items() if c.get("edge") == "1"}
    # Annotations are text, not components: a title, a legend line or a
    # footnote cannot be wired, so flagging one as an orphan is a false
    # positive that trains the reader to ignore the gate. The same exclusion
    # keeps them out of the overlap and wire-through-node checks, where a text
    # box is not an obstacle either.
    def is_annotation(cid):
        st = _style_of(cells[cid])
        return st.startswith("text;") or ";text;" in st

    components = {
        cid: c for cid, c in cells.items()
        if c.get("vertex") == "1" and cid
        and not any(cid.startswith(p) for p in IGNORE_PREFIXES)
        and cid not in IGNORE_EXACT
        and not (geo[cid][2] >= 400 and geo[cid][3] >= 300)  # containers
        and not is_annotation(cid)
        and c.get("parent") not in edges           # edge label cells
        and not _style_of(c).startswith("edgeLabel")
    }

    def edge_label(eid):
        """(text, distance-fraction, y-offset) -- direct value or child cell."""
        e = edges[eid]
        if e.get("value"):
            return e.get("value"), 0.5, 0.0
        for c in cells.values():
            if c.get("parent") == eid and c.get("vertex") == "1" \
                    and c.get("value"):
                g = c.find("mxGeometry")
                frac, off_y = 0.5, 0.0
                if g is not None:
                    if g.get("x") is not None:
                        frac = (float(g.get("x")) + 1) / 2
                    off = g.find("./mxPoint")
                    if off is not None:
                        off_y = float(off.get("y", 0) or 0)
                return c.get("value"), frac, off_y
        return None, 0.5, 0.0

    violations, warnings = [], []

    # 1 -- connectivity. Skipped for a FILTERED view (design-only or
    # implementation-only), where an unwired component is deliberate: its edges
    # belong to the other source. The generator proves connectivity once
    # against the whole model instead of against each subset.
    srcs = {e.get("source") for e in edges.values()}
    dsts = {e.get("target") for e in edges.values()}
    for cid, c in components.items():
        val = str(c.get("value") or "").lower()
        if not require_connectivity:
            break
        if cid not in srcs and cid not in dsts:
            violations.append(f"orphan node {cid} ({c.get('value')!r})")
        # A microservice that calls something but is never called is drawn
        # unreachable: an adaptor, a consumer or a BFF with no inbound wire.
        # That is a modelling gap, not a style choice - the reader cannot tell
        # where the component is entered from. Client and external-platform
        # kinds are entry points by nature and are exempt.
        elif "prIcon=pod" in _style_of(c) and cid not in dsts:
            violations.append(
                f"microservice {cid} ({c.get('value')!r}) has no incoming "
                f"wire; draw how it is reached or declare it an entry point")
        if "callback" in val and not (cid in srcs and cid in dsts):
            violations.append(f"callback receiver {cid} lacks in+out wiring")

    # 2 -- node/node overlap (node box + its label vs the other)
    boxes = {cid: (geo[cid], _label_box(geo[cid][0], geo[cid][1],
                                        geo[cid][2], geo[cid][3],
                                        _style_of(c), c.get("value")))
             for cid, c in components.items()}
    ids = sorted(boxes)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ga, la = boxes[a]
            gb, lb = boxes[b]
            if _rects_overlap(ga, gb):
                violations.append(f"node overlap: {a} vs {b}")
                continue
            if la and _rects_overlap(la, gb):
                violations.append(f"label of {a} overlaps node {b}")
            if lb and _rects_overlap(lb, ga):
                violations.append(f"label of {b} overlaps node {a}")
            if la and lb and _rects_overlap(la, lb):
                violations.append(f"label collision: {a} vs {b}")

    # 3 + 4 -- labels on edges, wire discipline
    polylines = {eid: _edge_polyline(e, cells, geo)
                 for eid, e in edges.items()}
    label_info = {}  # eid -> (text, box)
    for eid in edges:
        text, frac, off_y = edge_label(eid)
        if not text:
            continue
        lines = _label_lines(text)
        if (len(lines) > LABEL_MAX_LINES
                or any(len(ln) > LABEL_MAX_CHARS for ln in lines)):
            violations.append(
                f"edge {eid}: label {text!r} violates the label law "
                f"(<= {LABEL_MAX_CHARS} chars x {LABEL_MAX_LINES} lines)")
        label_info[eid] = (text, _label_midpoint_box(
            polylines[eid], text, frac, off_y,
            float(_style_val(_style_of(edges[eid]), "fontSize", 9) or 9)))

    edge_ids = sorted(polylines)
    for i, a in enumerate(edge_ids):
        pa = polylines[a]
        for b in edge_ids[i + 1:]:
            pb = polylines[b]
            hits = []
            for s1 in _segments(pa):
                for s2 in _segments(pb):
                    r = _seg_intersect(s1[0], s1[1], s2[0], s2[1])
                    if r:
                        hits.append(r)
            if hits.count("stack"):
                violations.append(f"wires stacked: {a} vs {b}")
            elif hits.count("cross") > max_crossings:
                violations.append(
                    f"wire crossing {a} x {b} "
                    f"({hits.count('cross')}x > budget {max_crossings})")

    # titled containers: a panel's caption must not strike through its first
    # child row. Reported defect, invisible to every per-element rule.
    for host, child, cy, band_end in _title_band_check(cells, geo):
        violations.append(
            f"annotation {child} at y={cy:.0f} sits inside the title band of "
            f"{host} (caption occupies up to y={band_end:.0f})")
    # a cell must be able to show its own text, and must not carry source
    # coordinates: both are reader-facing defects the eye catches and the
    # geometry rules cannot
    for cid, why, snippet in _check_text_fit(cells, geo):
        violations.append(f"cell {cid}: {why} ({snippet!r})")
    for cid, c in cells.items():
        if c.get("vertex") != "1" or not cid:
            continue
        leak = _code_detail(str(c.get("value") or ""))
        if leak:
            violations.append(
                f"cell {cid} carries a source coordinate ({leak}); a diagram "
                f"names behaviour, not code")

    # page-wide text rules: every page, not just the HLA page. A table cell
    # that cannot show its text draws it through the neighbouring cell, and a
    # cell carrying a file name, a line number or a function name is stale the
    # next time the code moves - the diagram is read by people who do not have
    # the repository open.
    for diagram in diagrams:
        if _is_palette(diagram):
            continue
        dcells, dgeo = _abs_geometry(diagram)
        for cid, why, snippet in _check_text_fit(dcells, dgeo):
            violations.append(f"cell {cid}: {why} ({snippet!r})")
        for cid, c in dcells.items():
            if c.get("vertex") != "1" or not cid:
                continue
            leak = _code_detail(str(c.get("value") or ""))
            if leak:
                violations.append(
                    f"cell {cid} carries a source coordinate ({leak}); a "
                    f"diagram names behaviour, not code")

    # wire envelope: a wire must stay on the page and inside the drawing. The
    # gate previously passed a diagram whose wires ran past the lanes and off
    # the canvas, because every individual segment was legal - that is the
    # "lines go to the bottom of the page" defect, which no per-segment rule
    # can see. A bus below the lanes is legitimate (the standard's event-bus
    # rule), so the allowance is a depth budget rather than zero.
    lane_boxes = [geo[cid] for cid, c in cells.items()
                  if c.get("vertex") == "1" and cid
                  and geo[cid][2] >= 200 and geo[cid][3] >= 300]
    page_w = page_h = None
    gm = p1.find("mxGraphModel")
    if gm is not None:
        page_w = float(gm.get("pageWidth", 0) or 0)
        page_h = float(gm.get("pageHeight", 0) or 0)
    if lane_boxes:
        lx0 = min(g[0] for g in lane_boxes)
        lx1 = max(g[0] + g[2] for g in lane_boxes)
        ly0 = min(g[1] for g in lane_boxes)
        ly1 = max(g[1] + g[3] for g in lane_boxes)
        for eid, pts in polylines.items():
            ys = [p[1] for p in pts]
            xs = [p[0] for p in pts]
            if max(ys) > ly1 + bus_depth:
                warnings.append(
                    f"wire {eid} runs {max(ys) - ly1:.0f}px below the lanes "
                    f"(bus depth budget {bus_depth}px; a tidy bus stays near)")
            if min(ys) < ly0 - 120:
                violations.append(
                    f"wire {eid} runs {ly0 - min(ys):.0f}px above the lanes")
            if page_w and page_h and (max(xs) > page_w or min(xs) < 0
                                      or max(ys) > page_h or min(ys) < 0):
                violations.append(
                    f"wire {eid} runs off the page (page "
                    f"{page_w:.0f}x{page_h:.0f})")

    # wire-through-node: no segment may pass over a component it is not
    # sourcing or targeting
    for eid, pts in polylines.items():
        own = {edges[eid].get("source"), edges[eid].get("target")}
        for cid, (g, _lb) in boxes.items():
            if cid in own:
                continue
            for p1, p2 in _segments(pts):
                if _seg_hits_rect(p1, p2, g):
                    violations.append(
                        f"wire {eid} passes through node {cid}")
                    break

    for a, (text, lab_box) in label_info.items():
        if lab_box is None:
            continue
        for b in edge_ids:
            if b == a:
                continue
            for s in _segments(polylines[b]):
                seg_box = (min(s[0][0], s[1][0]), min(s[0][1], s[1][1]),
                           abs(s[1][0] - s[0][0]) or 1,
                           abs(s[1][1] - s[0][1]) or 1)
                if _rects_overlap(lab_box, seg_box, pad=0):
                    warnings.append(
                        f"label of {a} rides wire {b} "
                        "(legible via background; declutter if >2 cases)")
                    break
        for cid, (g, _lb) in boxes.items():
            if cid in {edges[a].get("source"), edges[a].get("target")}:
                continue
            if _rects_overlap(lab_box, g):
                violations.append(f"label of {a} overlaps node {cid}")

    if not quiet:
        print(f"verify_layout: {xml_file}")
        print(f"  components={len(components)} edges={len(edges)}")
        for v in violations:
            print(f"  FAIL {v}")
        seen = set()
        for w in warnings:
            key = w.split(" rides ")[1][:40]
            if key in seen:
                continue
            seen.add(key)
            print(f"  WARN {w}")
        if violations:
            print(f"RESULT: FAIL ({len(violations)} violation(s), "
                  f"{len(warnings)} warning(s))")
        else:
            print(f"RESULT: PASS (0 violations, {len(warnings)} warning(s))")
    return violations, warnings


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    budget = 0
    bus = 240
    for a in sys.argv[1:]:
        if a.startswith("--max-crossings="):
            budget = int(a.split("=")[1])
        if a.startswith("--bus-depth="):
            bus = int(a.split("=")[1])
    if not args:
        raise SystemExit(__doc__)
    violations, _warnings = verify(args[0], budget, bus_depth=bus)
    raise SystemExit(1 if violations else 0)
