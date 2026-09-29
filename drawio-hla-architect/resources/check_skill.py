#!/usr/bin/env python3
"""Behavioral regression check for the drawio-hla-architect skill.

It asserts what the skill's own doctrine now claims, so a future edit that
re-breaks the invariants fails here instead of in a reviewer's screenshot:

  1. the shipped model generates and passes its own gate
  2. a large, fully-connected model (50 nodes / 44 edges) generates and passes
  3. a model that cannot route cleanly is REFUSED and leaves no file
  4. an unconnected node is reported as an orphan
  5. a text annotation is NOT reported as an orphan
  6. a wire pushed off the page is reported
  7. the gate CLI exits 0 on a pass and 1 on a failure
"""
import importlib.util
import os
import re
import subprocess
import sys

RES = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RES)


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(RES, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = load("hla_generator")
gate = load("verify_layout")

fails = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(label)


print("drawio-hla-architect regression check")

# 1 -- shipped model
out = "/tmp/_reg_shipped.drawio.xml"
gen.generate_drawio_xml(out)
v, w = gate.verify(out, gen.MAX_CROSSINGS, quiet=True)
check("shipped model passes its own gate", not v, "; ".join(v[:3]))

# 2 -- large connected model
lanes, nodes, edges = gen.build_model()
N, E = list(nodes), list(edges)
for t in range(5):
    # 7+ so the demo's own lane_ext rows (0,3,5,6) are not overwritten
    slot = 7 + t * 2
    N += [(f"n_mob_{t}", "lane_client", slot, f"app-{t}", "ext_plain"),
          (f"n_kg_{t}", "lane_gw", slot, f"kong-{t}", "pod_new"),
          (f"n_bf_{t}", "lane_bff", slot, f"bff-{t}", "pod_new"),
          (f"n_or_{t}", "lane_orch", slot, f"orch-{t}", "pod_new"),
          (f"n_co_{t}", "lane_core", slot, f"core-{t}", "pod_new"),
          (f"n_ad_{t}", "lane_adapt", slot, f"adapter-{t}", "pod_new"),
          (f"n_ex_{t}", "lane_ext", slot, f"platform-{t}", "ext")]
    E += [(f"t{t}_1", f"n_mob_{t}", f"n_kg_{t}", "sync", "HTTPS"),
          (f"t{t}_2", f"n_kg_{t}", f"n_bf_{t}", "sync", "route"),
          (f"t{t}_3", f"n_bf_{t}", f"n_or_{t}", "sync", "REST"),
          (f"t{t}_4", f"n_or_{t}", f"n_co_{t}", "sync", "domain"),
          (f"t{t}_5", f"n_co_{t}", f"n_ad_{t}", "sync", "call"),
          (f"t{t}_6", f"n_ad_{t}", f"n_ex_{t}", "sync", "mTLS")]
gen.build_model = lambda: (lanes, N, E)
big = "/tmp/_reg_big.drawio.xml"
gen.generate_drawio_xml(big)
v, w = gate.verify(big, gen.MAX_CROSSINGS, quiet=True)
check("50-node model passes (no stacked/wire-through-node)", not v,
      "; ".join(v[:3]))

# 3 -- unrouteable model is refused, and writes nothing
gen.build_model = lambda: (lanes, nodes + [(f"n_z{i}", "lane_core", 6, "z", "pod_new")
                                           for i in range(1)],
                           edges)
bad = "/tmp/_reg_bad.drawio.xml"
if os.path.exists(bad):
    os.remove(bad)
gen.NODES = nodes + [("n_orphan_zz", "lane_core", 20, "orphan", "pod_new")]
try:
    gen.generate_drawio_xml(bad)
    check("unrouteable model is refused", False, "engine emitted it")
except SystemExit:
    check("unrouteable model is refused", True)
check("refused model leaves no file", not os.path.exists(bad))
gen.build_model = lambda: (lanes, nodes, edges)
gen.NODES = nodes

# 4/5/6 -- gate semantics on a warm file
src = open(out).read()
def write_and_gate(txt, path, budget=2):
    open(path, "w").write(txt)
    return gate.verify(path, budget, quiet=True)

v, _ = write_and_gate(src.replace('source="n_mobile"', 'source="n_mobile"', 1),
                      "/tmp/_reg_base.drawio.xml")
check("clean file has no violations", not v, "; ".join(v[:2]))

# text annotation must not be an orphan
ann = src.replace('<mxCell id="0" />',
                  '<mxCell id="0" />'
                  '<mxCell id="title_ann" parent="1" '
                  'style="text;html=1;strokeColor=none;fillColor=none;" '
                  'value="Title" vertex="1">'
                  '<mxGeometry x="10" y="10" width="200" height="20" '
                  'as="geometry" /></mxCell>', 1)
v, _ = write_and_gate(ann, "/tmp/_reg_ann.drawio.xml")
check("text annotation is not an orphan",
      not any("title_ann" in x for x in v), "; ".join(v[:2]))

# a real component with no wires must be an orphan
orph = src.replace('<mxCell id="0" />',
                   '<mxCell id="0" />'
                   '<mxCell id="n_orphan_real" parent="1" '
                   'style="rounded=1;html=1;whiteSpace=wrap;" value="lonely" '
                   'vertex="1"><mxGeometry x="10" y="10" width="120" '
                   'height="30" as="geometry" /></mxCell>', 1)
v, _ = write_and_gate(orph, "/tmp/_reg_orph.drawio.xml")
check("unwired component IS an orphan",
      any("n_orphan_real" in x for x in v), "; ".join(v[:2]))

# a wire pushed off the declared page must be reported
off = re.sub(r'pageHeight="\d+"', 'pageHeight="500"', src, count=1)
v, _ = write_and_gate(off, "/tmp/_reg_off.drawio.xml")
check("wire off the page is reported",
      any("off the page" in x for x in v), "; ".join(v[:2]))

# 7 -- CLI exit codes
e0 = subprocess.run([sys.executable, os.path.join(RES, "verify_layout.py"),
                     out, "--max-crossings=2"], capture_output=True).returncode
e1 = subprocess.run([sys.executable, os.path.join(RES, "verify_layout.py"),
                     "/tmp/_reg_off.drawio.xml", "--max-crossings=2"],
                    capture_output=True).returncode
check("gate CLI exits 0 on pass", e0 == 0, f"exit={e0}")
check("gate CLI exits 1 on fail", e1 == 1, f"exit={e1}")

# 8 -- the three views render from one model, and the gap is visible
import subprocess as _sp
_gen = os.path.join(RES, "hla_generator.py")
views = {}
for mode in ("both", "impl", "spec"):
    out_v = f"/tmp/_reg_{mode}.drawio.xml"
    r = _sp.run([sys.executable, _gen, out_v, "--from", mode],
                capture_output=True, text=True)
    views[mode] = (r.returncode, out_v, r.stdout + r.stderr)
check("both/impl/spec views all render",
      all(v[0] == 0 for v in views.values()),
      "; ".join(f"{m}:{v[2].strip().splitlines()[-1][:60]}"
                for m, v in views.items() if v[0]))
check("spec view carries the planned edge",
      "planned KYC" in open(views["spec"][1]).read())
check("impl view excludes the planned edge",
      "planned KYC" not in open(views["impl"][1]).read())
check("both view marks the planned edge as dashed grey",
      "9E9E9E" in open(views["both"][1]).read())
check("CLI rejects a bad --from value",
      _sp.run([sys.executable, _gen, "/tmp/_reg_bad_mode.xml", "--from", "wat"],
              capture_output=True).returncode != 0)

# 9 -- the gate's new rules fire on real defects, not just on clean files
def gate_txt(txt, path):
    open(path, "w").write(txt)
    return gate.verify(path, 2, quiet=True)[0]

base = open(out).read()
leak = base.replace('value="HTTPS"', 'value="handler.go:42"', 1)
check("gate reports a source coordinate",
      any("source coordinate" in v for v in gate_txt(leak, "/tmp/_reg_leak.drawio.xml")))

band = base.replace('<mxCell id="0" />',
                    '<mxCell id="panel_x" parent="1" '
                    'style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;'
                    'verticalAlign=top;spacingTop=8;fontSize=12;" value="Panel" '
                    'vertex="1"><mxGeometry x="2000" y="200" width="600" '
                    'height="400" as="geometry" /></mxCell>'
                    '<mxCell id="panel_c" parent="1" style="text;html=1;" '
                    'value="first row" vertex="1">'
                    '<mxGeometry x="2020" y="206" width="200" height="14" '
                    'as="geometry" /></mxCell>', 1)
check("gate reports content inside a title band",
      any("title band" in v for v in gate_txt(band, "/tmp/_reg_band.drawio.xml")))

fit = base.replace('<mxCell id="0" />',
                   '<mxCell id="note_tiny" parent="1" style="text;html=1;" '
                   'value="this text cannot fit in a 20px box" vertex="1">'
                   '<mxGeometry x="2000" y="600" width="60" height="12" '
                   'as="geometry" /></mxCell>', 1)
check("gate reports a cell too small for its text",
      any("needs" in v and "box is" in v
          for v in gate_txt(fit, "/tmp/_reg_fit.drawio.xml")))

unreach = base.replace('<mxCell id="0" />',
                       '<mxCell id="n_unreached" parent="1" '
                       'style="sketch=0;html=1;whitespace=wrap;'
                       'verticalLabelPosition=bottom;shape=mxgraph.kubernetes.icon;'
                       'prIcon=pod;" value="sink" vertex="1">'
                       '<mxGeometry x="2200" y="60" width="40" height="40" '
                       'as="geometry" /></mxCell>', 1)
check("gate reports an unreachable microservice",
      any("no incoming" in v or "orphan" in v
          for v in gate_txt(unreach, "/tmp/_reg_unreach.drawio.xml")))

# 10 -- model-level connectivity survives a broken model
gen_mod = load("hla_generator")
_l, _n, _e = gen_mod.build_model()
try:
    gen_mod._validate_model(_l, gen_mod.nodes_normalize(_n),
                            gen_mod.edges_normalize(
                                [e for e in _e if e[0] != "e_kafka"]))
    check("model validation catches a node its edges abandoned", False,
          "validator accepted it")
except SystemExit as exc:
    check("model validation catches a node its edges abandoned",
          "n_kafka" in str(exc), str(exc)[:80])

# 11 -- a wire's step label must reproduce every step the wire carries
def _step_roundtrip(label, steps):
    """Recompute a wire's label from its steps, as the engine does."""
    g = load("hla_generator")
    line = g.step_label(label, steps).split("\n")[-1]
    return line, g.label_ids([line])


line, ids = _step_roundtrip("REST", ("A1", "A2", "A3", "A4", "B1"))
check("step label collapses a consecutive range", line == "A1-A4,B1", line)
check("step label round-trips to exactly the ids on the wire",
      ids == ["A1", "A2", "A3", "A4", "B1"], str(ids))
line, ids = _step_roundtrip("x", [f"A2.{i}" for i in range(2, 20)])
check("an over-long step list becomes a counted bracket",
      line.startswith("A2.2..") and line.endswith("(18)"), line)

# the shipped model's own step labels must round-trip
_g = load("hla_generator")
_l, _n, _e = _g.build_model()
_nn = _g.nodes_normalize(_n)
try:
    _g._validate_model(_l, _nn, list(_g.edges_normalize(_e)))
    check("validator accepts the shipped step labels", True)
except SystemExit as exc:
    check("validator accepts the shipped step labels", False, str(exc)[:90])

print(f"\n{len(fails)} failure(s)" if fails else "\nALL CHECKS PASS")
sys.exit(1 if fails else 0)
