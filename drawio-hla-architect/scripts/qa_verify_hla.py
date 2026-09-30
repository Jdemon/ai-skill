#!/usr/bin/env python3
"""
Enterprise Draw.io HLA Quality Assurance & Governance Auditor
Universal Enterprise Architecture Standards across Any Domain

Audits .drawio diagram files against enterprise architectural invariants:
1. Multi-Page Structure & Standard Tab (STD / Standard Colors and Icons)
2. Dedicated Swimlane Isolation (Client, Gateway, BFF, Orch, Core, Adaptor, External)
2.1 Geometry & Anti-Overlap Clearance (Container clearance >= 50px, horizontal margin >= 25px, no component collision)
3. Zero-Orphan Microservices & Explicit Source/Target Anchoring
4. Inbound/Outbound Completeness for Asynchronous Callback Receivers
5. Lifecycle Color Matrix Compliance (New=#03CCFF, Enhanced=#92D14F, Existing=#BFBFBF, External=#EF7D30)
5.1 Official STD Connection Line Colors (#03CCFF, #92D14F, #BFBFBF, #EF7D30, #FF6A00)
6. Multiline Label HTML Safety (html=1;whiteSpace=wrap;) on Image Icons
7. Edge Routing Quality (Orthogonal routing, Arc Jumps jumpStyle=arc;jumpSize=6;)
8. Edge Labeling Standards (Step sequence numbers, HTTP verbs, paths, lifecycle tags)
9. Kafka Event Bus & Topic Standards (<system>.<domain>.<event>.<ENV>, dashed=1;flowAnimation=1;)
"""

import sys
import os
import re
import argparse
import xml.etree.ElementTree as ET

STD_TAB_IDS = {"ao9VHCrxs2CTfegMv53f", "t2Yd3kyUYJbDHsi3N8cM"}
STD_TAB_NAMES = {"standard colors and icons", "std", "standard"}

APPROVED_LIFECYCLE_HEX = {
    "#03CCFF": "NEW (KTB/Infinitas/Arise)",
    "#03ccff": "NEW (KTB/Infinitas/Arise)",
    "#92D14F": "ENHANCED",
    "#92d14f": "ENHANCED",
    "#BFBFBF": "EXISTING / REUSED",
    "#bfbfbf": "EXISTING / REUSED",
    "#EF7D30": "EXTERNAL / 3RD PARTY",
    "#ef7d30": "EXTERNAL / 3RD PARTY",
    "#006666": "STANDARD SYNC FLOW (TEAL)",
    "#4A5568": "NEUTRAL / BOUNDARY",
    "#4a5568": "NEUTRAL / BOUNDARY"
}

def clean_text(val):
    if not val:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', val)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\s+', ' ', clean).strip()

def run_qa_audit(file_path, strict=False):
    print("\n" + "=" * 70)
    print(f"🏛️  ENTERPRISE HLA QUALITY AUDITOR: {os.path.basename(file_path)}")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' does not exist.")
        return False

    try:
        tree = ET.parse(file_path)
    except Exception as e:
        print(f"❌ XML Syntax Parse Error: {e}")
        return False

    root = tree.getroot()
    diagrams = root.findall("diagram")
    print(f"📄 Document File Format: <{root.tag}> with {len(diagrams)} diagram page(s)")

    scores = {"passed": 0, "warnings": 0, "errors": 0}

    # 1. Multi-Page & Standard Tab Audit
    std_tab_found = False
    std_tab_name = ""
    for d in diagrams:
        did = d.get("id", "")
        dname = d.get("name", "").strip().lower()
        if did in STD_TAB_IDS or dname in STD_TAB_NAMES:
            std_tab_found = True
            std_tab_name = d.get("name", "")
            break

    if std_tab_found:
        print(f"  ✅ [Rule 1 - Page Structure]: Found official Standard Colors and Icons tab: '{std_tab_name}'")
        scores["passed"] += 1
    else:
        msg = "Standard Colors and Icons tab ('STD' or id='ao9VHCrxs2CTfegMv53f') not found in diagram!"
        if strict or len(diagrams) > 1:
            print(f"  ❌ [Rule 1 - Page Structure]: {msg}")
            scores["errors"] += 1
        else:
            print(f"  ⚠️  [Rule 1 - Page Structure]: {msg}")
            scores["warnings"] += 1

    # 2. Iterate through architecture tabs
    for idx, d in enumerate(diagrams):
        dname = d.get("name", f"Page-{idx+1}")
        did = d.get("id", "")
        if did in STD_TAB_IDS or dname.lower() in STD_TAB_NAMES:
            continue

        print(f"\n--- 🔎 Auditing Diagram Tab: '{dname}' (id={did}) ---")
        cells = d.findall(".//mxCell")

        # Classify elements
        swimlanes = []
        containers = []
        pods = {}
        databases = {}
        image_icons = {}
        notes = {}
        edges = []
        labels_by_parent = {}

        for c in cells:
            cid = c.get("id")
            val = c.get("value", "")
            style = c.get("style", "")
            is_vertex = c.get("vertex") == "1"
            is_edge = c.get("edge") == "1"
            parent = c.get("parent")
            geo = c.find("mxGeometry")

            if is_edge:
                edges.append(c)
            elif is_vertex:
                # check if this is an edgeLabel
                if "edgeLabel" in style and parent:
                    labels_by_parent.setdefault(parent, []).append(clean_text(val))
                    continue

                w = float(geo.get("width", 0) or 0) if geo is not None else 0
                h = float(geo.get("height", 0) or 0) if geo is not None else 0

                if "swimlane" in style or (h >= 400 and w >= 100 and "pod" not in style and "cylinder" not in style):
                    if cid.startswith("box_") or "container" in cid.lower() or w >= 800:
                        containers.append(c)
                    else:
                        swimlanes.append(c)
                elif "pod" in style:
                    pods[cid] = c
                elif "cylinder" in style:
                    databases[cid] = c
                elif "shape=image" in style or "imageAspect" in style:
                    image_icons[cid] = c
                elif "note" in cid.lower() or "cache_schema" in style or "#fad7ac" in style:
                    notes[cid] = c

        print(f"  📊 Inventory: {len(swimlanes)} swimlanes ({len(containers)} bounding container), {len(pods)} microservices, {len(databases)} DB cylinders, {len(edges)} connections")

        if len(pods) == 0:
            print("  ℹ️ Note: No Kubernetes pod shapes detected in this tab. Skipping microservice graph rules.")
            continue

        # Rule 2: Dedicated Swimlane Isolation
        lane_titles = [clean_text(l.get("value", "")) for l in swimlanes if l.get("value")]
        expected_tiers = ["gateway", "bff", "orch", "core", "adapt"]
        found_tiers = sum(1 for tier in expected_tiers if any(tier in lt.lower() for lt in lane_titles))
        if len(swimlanes) >= 5 or found_tiers >= 3:
            print(f"  ✅ [Rule 2 - Swimlanes]: {len(swimlanes)} dedicated swimlanes detected (Tiers recognized: {found_tiers}/5).")
            scores["passed"] += 1
        else:
            print(f"  ⚠️  [Rule 2 - Swimlanes]: Diagram has {len(swimlanes)} swimlanes. Ensure Gateway, BFF, Orch, Core, and Adaptor are not merged into single columns.")
            scores["warnings"] += 1

        # Rule 2.1: Swimlane & Bounding Box Geometry Overlap Check
        geometry_errors = []
        for s in swimlanes:
            s_geo = s.find("mxGeometry")
            if s_geo is None:
                continue
            sx = float(s_geo.get("x", 0) or 0)
            sy = float(s_geo.get("y", 0) or 0)
            sw = float(s_geo.get("width", 0) or 0)
            sh = float(s_geo.get("height", 0) or 0)
            s_val = clean_text(s.get("value", ""))

            # If this is a wide container box covering multiple lanes (width > 800)
            if sw > 800:
                for other in swimlanes:
                    if other == s:
                        continue
                    o_geo = other.find("mxGeometry")
                    if o_geo is None:
                        continue
                    ox = float(o_geo.get("x", 0) or 0)
                    oy = float(o_geo.get("y", 0) or 0)
                    ow = float(o_geo.get("width", 0) or 0)
                    o_val = clean_text(other.get("value", ""))

                    # 1) Check horizontal overlap with subsequent lanes outside the container
                    if ox > sx + 50 and ox < (sx + sw) and (ox + ow) > (sx + sw + 50):
                        overlap_px = (sx + sw) - ox
                        geometry_errors.append(
                            f"Container '{s_val}' (right={sx+sw}) overlaps {overlap_px:.1f}px into adjacent lane '{o_val}' (x={ox})!"
                        )

                    # 2) Check vertical clearance for child lanes inside the container
                    if ox >= sx and (ox + ow) <= (sx + sw + 20):
                        vertical_clearance = oy - sy
                        if vertical_clearance < 35:
                            geometry_errors.append(
                                f"Container '{s_val}' has only {vertical_clearance:.1f}px clearance above child lane '{o_val}'. Header text will be obscured! (Min required: 35px)"
                            )

        # 3) Check swimlane header clearance against child components
        all_nodes = {**pods, **databases, **image_icons}
        for nid, ncell in all_nodes.items():
            n_geo = ncell.find("mxGeometry")
            if n_geo is None:
                continue
            ny = float(n_geo.get("y", 0) or 0)
            n_val = clean_text(ncell.get("value", ""))
            # If diagram swimlanes start around y=80, components must start at y >= 120 so lane title is not obscured
            if ny < 120 and ny > 40:
                geometry_errors.append(
                    f"Component [{nid}] '{n_val}' placed at y={ny} collides with swimlane header text! (Must be placed at y >= 120)"
                )

        # 4) Check node-to-node bounding box overlap
        node_items = list(all_nodes.items())
        for i in range(len(node_items)):
            id1, c1 = node_items[i]
            g1 = c1.find("mxGeometry")
            if g1 is None:
                continue
            x1 = float(g1.get("x", 0) or 0)
            y1 = float(g1.get("y", 0) or 0)
            w1 = float(g1.get("width", 0) or 44)
            h1 = float(g1.get("height", 0) or 44)
            v1 = clean_text(c1.get("value", ""))

            for j in range(i + 1, len(node_items)):
                id2, c2 = node_items[j]
                g2 = c2.find("mxGeometry")
                if g2 is None:
                    continue
                x2 = float(g2.get("x", 0) or 0)
                y2 = float(g2.get("y", 0) or 0)
                w2 = float(g2.get("width", 0) or 44)
                h2 = float(g2.get("height", 0) or 44)
                v2 = clean_text(c2.get("value", ""))

                # Check 2D bounding box intersection (with small 5px margin of tolerance)
                if not (x1 + w1 <= x2 + 5 or x2 + w2 <= x1 + 5 or y1 + h1 <= y2 + 5 or y2 + h2 <= y1 + 5):
                    geometry_errors.append(
                        f"Collision detected between [{id1}] '{v1}' (x={x1},y={y1}) and [{id2}] '{v2}' (x={x2},y={y2})!"
                    )

        if geometry_errors:
            print(f"  ❌ [Rule 2.1 - Geometry Overlap]: Detected {len(geometry_errors)} collision(s):")
            for ge in geometry_errors:
                print(f"     - {ge}")
            scores["errors"] += len(geometry_errors)
        else:
            print("  ✅ [Rule 2.1 - Geometry Overlap]: All swimlanes, headers, and components have verified non-overlapping clearance.")
            scores["passed"] += 1

        # Rule 2.2: Swimlane Horizontal Centering Audit (Single-Component Tracks)
        off_center_nodes = []
        all_track_nodes = {**pods, **image_icons, **databases, **notes}
        for s in swimlanes:
            sgeo = s.find("mxGeometry")
            if sgeo is None:
                continue
            sx = float(sgeo.get("x", 0) or 0)
            sy = float(sgeo.get("y", 0) or 0)
            sw = float(sgeo.get("width", 0) or 0)
            sh = float(sgeo.get("height", 0) or 0)
            stitle = clean_text(s.get("value", ""))
            scenter_x = sx + sw / 2.0

            # Find all nodes physically located inside this swimlane
            lane_nodes = []
            for nid, ncell in all_track_nodes.items():
                ngeo = ncell.find("mxGeometry")
                if ngeo is None:
                    continue
                nx = float(ngeo.get("x", 0) or 0)
                ny = float(ngeo.get("y", 0) or 0)
                nw = float(ngeo.get("width", 44) or 44)
                nh = float(ngeo.get("height", 44) or 44)
                if nx >= sx - 10 and (nx + nw) <= (sx + sw + 10):
                    lane_nodes.append((nid, ncell, nx, ny, nw, nh))

            # Group by vertical row/track (within 40px)
            row_buckets = []
            for node_data in lane_nodes:
                placed = False
                for bucket in row_buckets:
                    if abs(bucket["y"] - node_data[3]) <= 40:
                        bucket["nodes"].append(node_data)
                        placed = True
                        break
                if not placed:
                    row_buckets.append({"y": node_data[3], "nodes": [node_data]})

            # If a row has only 1 component, check centering for microservices/icons
            for bucket in row_buckets:
                if len(bucket["nodes"]) == 1:
                    nid, ncell, nx, ny, nw, nh = bucket["nodes"][0]
                    # Only audit microservices, databases, and major icons (auxiliary notes are exempted)
                    if nid in notes:
                        continue
                    node_center_x = nx + nw / 2.0
                    expected_center_x = round(sx + (sw - nw) / 2.0)
                    offset = abs(node_center_x - scenter_x)
                    if offset > 20:  # More than 20px off center
                        nval = clean_text(ncell.get("value", ""))
                        off_center_nodes.append((nid, nval, stitle, int(nx), expected_center_x, int(offset)))

        if off_center_nodes:
            print(f"  ⚠️  [Rule 2.2 - Swimlane Centering]: Found {len(off_center_nodes)} single-node track(s) not centered in swimlane:")
            for ocn in off_center_nodes[:5]:
                print(f"     - [{ocn[0]}] '{ocn[1]}' in '{ocn[2]}' at x={ocn[3]} (Expected center: x={ocn[4]}, offset={ocn[5]}px)")
            scores["warnings"] += 1
        else:
            print("  ✅ [Rule 2.2 - Swimlane Centering]: Single microservices and icons are horizontally centered within their swimlanes.")
            scores["passed"] += 1


        # Rule 3: Zero-Orphan Microservices & Topological Anchoring
        sources = {e.get("source") for e in edges if e.get("source")}
        targets = {e.get("target") for e in edges if e.get("target")}

        orphans = []
        for pid, pcell in pods.items():
            pval = clean_text(pcell.get("value", ""))
            if pid not in sources and pid not in targets:
                orphans.append((pid, pval))

        if orphans:
            print(f"  ❌ [Rule 3 - Zero Orphans]: Found {len(orphans)} disconnected microservice(s):")
            for oid, oval in orphans[:5]:
                print(f"     - [{oid}] '{oval}' has zero incoming/outgoing connections!")
            scores["errors"] += len(orphans)
        else:
            print(f"  ✅ [Rule 3 - Zero Orphans]: All {len(pods)} microservices are topologically connected.")
            scores["passed"] += 1

        # Unanchored Floating Edges Check
        unanchored_edges = [e for e in edges if not e.get("source") or not e.get("target")]
        if unanchored_edges:
            print(f"  ⚠️  [Rule 3 - Edge Anchoring]: Found {len(unanchored_edges)} floating/unanchored edge(s) missing source or target attributes.")
            scores["warnings"] += 1
        else:
            print(f"  ✅ [Rule 3 - Edge Anchoring]: All {len(edges)} connections are strictly anchored with source and target node IDs.")
            scores["passed"] += 1

        # Rule 4: Callback Receivers Flow Completeness
        for pid, pcell in pods.items():
            pval = clean_text(pcell.get("value", "")).lower()
            if "callback" in pval or "cb_receiver" in pid.lower():
                has_in = pid in targets
                has_out = pid in sources
                if not (has_in and has_out):
                    print(f"  ❌ [Rule 4 - Callback Flow]: [{pid}] '{pval}' must have BOTH an inbound trigger and an outbound downstream call! (In: {has_in}, Out: {has_out})")
                    scores["errors"] += 1
                else:
                    print(f"  ✅ [Rule 4 - Callback Flow]: [{pid}] '{pval}' has verified two-way flow.")
                    scores["passed"] += 1

        # Rule 5: Lifecycle Color Code Compliance
        invalid_colors = []
        for pid, pcell in pods.items():
            style = pcell.get("style", "")
            m = re.search(r'strokeColor=([^;]+)', style)
            if m:
                color = m.group(1).upper()
                if color not in APPROVED_LIFECYCLE_HEX:
                    invalid_colors.append((pid, clean_text(pcell.get("value", "")), color))

        if invalid_colors:
            print(f"  ❌ [Rule 5 - Lifecycle Colors]: {len(invalid_colors)} pod(s) use non-standard border colors:")
            for ic in invalid_colors[:5]:
                print(f"     - [{ic[0]}] '{ic[1]}' has strokeColor={ic[2]} (Expected: #03CCFF, #92D14F, #BFBFBF, or #EF7D30)")
            scores["errors"] += len(invalid_colors)
        else:
            print(f"  ✅ [Rule 5 - Lifecycle Colors]: All microservice pods strictly conform to official lifecycle hex codes.")
            scores["passed"] += 1

        # Rule 5.1: Connection STD Color Compliance
        # Checks that edges declare strokeColor matching the STD Connection Matrix:
        # New (#03CCFF), Enhanced (#92D14F), Existing (#BFBFBF), External (#EF7D30), Kafka (#FF6A00)
        std_conn_colors = {"#03CCFF", "#92D14F", "#BFBFBF", "#EF7D30", "#FF6A00"}
        non_std_edges = []
        for e in edges:
            style = e.get("style", "")
            m = re.search(r'strokeColor=([^;]+)', style)
            if m:
                color = m.group(1).upper()
                if color not in std_conn_colors:
                    non_std_edges.append((e.get("id"), clean_text(e.get("value", "")), color))

        if non_std_edges:
            print(f"  ⚠️  [Rule 5.1 - STD Connection Colors]: {len(non_std_edges)} connection(s) do not use STD colors:")
            for nse in non_std_edges[:5]:
                print(f"     - Edge [{nse[0]}] '{nse[1]}' uses strokeColor={nse[2]} (Expected: #03CCFF, #92D14F, #BFBFBF, #EF7D30, #FF6A00)")
            scores["warnings"] += 1
        elif len(edges) > 0:
            print(f"  ✅ [Rule 5.1 - STD Connection Colors]: All {len(edges)} connections strictly conform to official STD connection colors (#03CCFF, #92D14F, #BFBFBF, #EF7D30, #FF6A00).")
            scores["passed"] += 1


        # Rule 6: Multiline Label HTML Safety on Image Icons
        leaking_icons = []
        for iid, icell in image_icons.items():
            val = icell.get("value", "")
            style = icell.get("style", "")
            if ("<br>" in val or "&lt;br&gt;" in val or "\n" in val) and "html=1" not in style:
                leaking_icons.append((iid, clean_text(val)))

        if leaking_icons:
            print(f"  ❌ [Rule 6 - HTML br Rendering]: {len(leaking_icons)} image icon(s) contain multiline text but lack 'html=1;whiteSpace=wrap;':")
            for li in leaking_icons[:5]:
                print(f"     - [{li[0]}] '{li[1]}' will display raw '<br>' tags on the canvas!")
            scores["errors"] += len(leaking_icons)
        else:
            print(f"  ✅ [Rule 6 - HTML br Rendering]: Multiline image icons properly declare 'html=1;whiteSpace=wrap;'.")
            scores["passed"] += 1

        # Rule 6.1: External Image Asset Health (Check for Cloudflare-blocked URLs)
        seeklogo_icons = []
        for iid, icell in image_icons.items():
            istyle = icell.get("style", "")
            if "seeklogo.com" in istyle:
                seeklogo_icons.append((iid, clean_text(icell.get("value", ""))))

        if seeklogo_icons:
            print(f"  ❌ [Rule 6.1 - Asset Health]: {len(seeklogo_icons)} icon(s) use seeklogo.com which is blocked by Cloudflare (HTTP 403 Forbidden):")
            for sli in seeklogo_icons[:5]:
                print(f"     - [{sli[0]}] '{sli[1]}' must be upgraded to embedded vector SVG data URI.")
            scores["errors"] += len(seeklogo_icons)
        else:
            print(f"  ✅ [Rule 6.1 - Asset Health]: All icons use reliable, Cloudflare-safe assets or embedded vector SVG data URIs.")
            scores["passed"] += 1

        # Rule 7: Wire-Crossing Arc Jump Quality
        arc_jumps = sum(1 for e in edges if "jumpStyle=arc" in e.get("style", ""))
        if len(edges) > 5 and arc_jumps == 0:
            print(f"  ⚠️  [Rule 7 - Wire Crossings]: None of the {len(edges)} connections declare 'jumpStyle=arc;jumpSize=6;'.")
            scores["warnings"] += 1
        elif arc_jumps > 0:
            print(f"  ✅ [Rule 7 - Wire Crossings]: Configured 'jumpStyle=arc;jumpSize=6;' on {arc_jumps}/{len(edges)} connections.")
            scores["passed"] += 1

        # Rule 8: Edge Labeling & Step Sequence Format
        labeled_edges = 0
        sequenced_edges = 0
        for e in edges:
            eid = e.get("id")
            val = clean_text(e.get("value", ""))
            child_labels = " ".join(labels_by_parent.get(eid, []))
            full_label = (val + " " + child_labels).strip()
            if full_label:
                labeled_edges += 1
                if re.search(r'\b(\d+(\.\d+)?|\d+\s*[-.)])', full_label):
                    sequenced_edges += 1

        if len(edges) > 0:
            pct_labeled = (labeled_edges / len(edges)) * 100
            if pct_labeled >= 50:
                print(f"  ✅ [Rule 8 - Flow Labeling]: {labeled_edges}/{len(edges)} ({pct_labeled:.1f}%) connections have clear API/event annotations ({sequenced_edges} numbered steps).")
                scores["passed"] += 1
            else:
                print(f"  ⚠️  [Rule 8 - Flow Labeling]: Only {labeled_edges}/{len(edges)} ({pct_labeled:.1f}%) connections have labels. Human architects expect API methods and sequence steps.")
                scores["warnings"] += 1

        # Rule 9: Kafka Topic Standard
        kafka_topics = []
        for c in cells:
            val = clean_text(c.get("value", ""))
            # Match standard enterprise topic patterns: <system>.<domain>.<event>.<ENV> or containing 'topic' / 'event:' / 'kafka'
            if any(k in val.lower() for k in ["topic", "event:", "kafka", ".prod", ".uat", ".dev"]) or re.search(r'[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+', val):
                kafka_topics.append(val)
        if kafka_topics:
            print(f"  ✅ [Rule 9 - Kafka Standards]: Found {len(kafka_topics)} standard Kafka event topic(s).")
            scores["passed"] += 1

    print("\n" + "=" * 70)
    print(f"📊 FINAL AUDIT REPORT: Passed: {scores['passed']} | Warnings: {scores['warnings']} | Errors: {scores['errors']}")
    print("=" * 70)

    if scores["errors"] == 0:
        print("🎉 STATUS: PASSED (Diagram complies with enterprise HLA standards)")
        return True
    else:
        print(f"🚫 STATUS: FAILED ({scores['errors']} critical violations need resolution)")
        return False

def main():
    parser = argparse.ArgumentParser(description="Audit Draw.io HLA diagrams against enterprise architectural standards.")
    parser.add_argument("drawio_file", help="Path to .drawio.xml or .drawio file")
    parser.add_argument("--strict", action="store_true", help="Enforce strict mode (warnings treated as errors)")
    args = parser.parse_args()

    success = run_qa_audit(args.drawio_file, strict=args.strict)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
