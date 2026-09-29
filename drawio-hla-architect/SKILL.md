---
name: drawio-hla-architect
description: >-
  Expert guide for designing and generating enterprise High-Level Architecture (HLA) diagrams
  in draw.io XML format. Enforces KTB/Infinitas/Arise standard colors, standard technology &
  infrastructure icons (PostgreSQL, MySQL, MongoDB, Redis, Kafka, Kong, Apigee, Vault),
  mandatory multi-swimlane separation (Kong Gateway, BFF, Orch, Core, and Adaptor each in their
  own dedicated swimlane), 2-page structure (with 'Standard Colors and Icons' tab in every diagram),
  reachability checks, interval-coloured routing (lines shared by span, verticals in node-free
  lane channels, anchors offset per edge, labels placed clear of nodes and wires), a short edge-label law,
  one declarative model rendered as a design view, an implementation view, or both with the gap marked
  (spec versus implemented, so the two cannot drift), and a mechanical layout verification gate the
  generator runs on its own output and refuses to write past, covering orphans, unreachable
  microservices, wire envelope, cell fit, and source-coordinate leaks.
---

# Draw.io HLA Architecture & Standards Guide

This skill provides comprehensive standards, XML templates, and visual conventions for authoring enterprise **High-Level Architecture (HLA)** diagrams in `draw.io` XML format (`.drawio.xml`), specifically optimized for the **KTB / Infinitas / Arise** digital banking ecosystem. Layout quality is mechanical, not eyeball: build with the declarative engine (`resources/hla_generator.py`) and gate with `resources/verify_layout.py` (§5–§6).

---

## ⚠️ Mandatory Invariants & Rules

1. **Mandatory 2-Page Draw.io Structure:**
   Every generated Draw.io XML HLA diagram **MUST include at least two pages/tabs**:
   * **Page 1 (`HLA Overview`):** The end-to-end multi-swimlane architecture diagram.
   * **Page 2 (`Standard Colors and Icons` / `id="ao9VHCrxs2CTfegMv53f"`):** The complete enterprise standard palette tab, containing the Component Lifecycle Matrix (New, Enhanced, Existing, External), Connection Types (Sync, Async, Kafka, Token), Kubernetes Pod shapes, color-coded Database Cylinders, and official Technology & Infrastructure Icons.
   * *Template Resource:* The standard Page 2 XML is located in `resources/standard_icons_tab.xml`, beside this skill (the layout engine resolves it relative to its own file — never hard-code absolute paths).

2. **Dedicated Swimlane for Every Tier (No Merged Layers):**
   Architectural tiers must **NEVER be combined into a single column**. Each layer must reside in its own dedicated vertical swimlane:
   * **Swimlane 1:** `Client & Inbound Rails` (Mobile App, WebViews, Inbound Webhooks)
   * **Swimlane 2:** `Gateway Layer (Kong API Gateway)` (Dedicated Kong Gateway lane: Kong External, Kong Internal, JWT Auth, Device-Fp Plugin)
   * **Swimlane 3:** `Channel BFF Layer (bff-mobile-*)` (Dedicated BFF lane: Client protocol translation, envelope unwrapping)
   * **Swimlane 4:** `Orchestration Layer (orch-*)` (Dedicated Saga lane: 2PC Saga coordination, readiness checks, domain aggregation)
   * **Swimlane 5:** `Domain Core Layer (core-*)` (Dedicated Core lane: State machine, business rules, persistence, caches)
   * **Swimlane 6:** `Adaptor Layer (adaptor-* / adapter-*)` (Dedicated Adaptor lane: Strictly outbound boundary protocol translators)
   * **Swimlane 7:** `Enterprise Platforms & Core Bank` (Enterprise platforms, government rails, core banking, Kafka bus)

3. **Zero Orphan Nodes Invariant (Strict Flow Connectivity):**
   * Every single microservice placed on an HLA diagram **MUST have complete incoming and outgoing connectivity**.
   * **No Orphan Nodes Allowed:** Placing an isolated microservice (e.g., an asynchronous callback receiver like `orch-ncb-callback`) without an incoming trigger line and an outgoing persistence/downstream call is strictly forbidden.
   * **Async Callback Flow Requirement:** When an asynchronous callback receiver microservice (`orch-*-callback`) is present:
     1. External Platform sends async webhook $\rightarrow$ Inbound Webhook endpoint in Swimlane 1.
     2. Inbound Webhook $\rightarrow$ routes through Gateway/BFF to Orchestrator Callback Receiver (`orch-*-callback`) in Swimlane 4.
     3. Callback Receiver $\rightarrow$ calls Domain Core (`core-*`) in Swimlane 5 to update status, store verification scores, or advance the 2PC saga.

4. **Wire-Crossing Minimization (Interval-Coloured Routing Law):**
   Clean layout comes from the engine, not from hand-tuned coordinates (§5):
   * **Equal Y-Band Rows:** a node's slot fixes its Y; forward edges between adjacent lanes run straight on the row. Each edge's anchor is offset along the node's edge, so two wires on one row are **parallel, never collinear**.
   * **Node-Free Channels:** every vertical leg is allocated in a lane's **node-free side channel** (the strip left of the node column and the strip right of it). A leg pinned to a node's **centre** is inside every node stacked above or below it in that lane, which is the single largest source of `wire passes through node` failures.
   * **Interval Colouring:** a vertical line and a corridor row are **lines wires share, not resources each wire owns**. A line is reused whenever the new span cannot touch a span already on it, so two wires on one line are safe *by construction* and `wires stacked` cannot fire. One line per wire is what exhausts the bands and pushes wires off the bottom of the page.
   * **Bounded Corridors:** forward multi-lane spans dip through the gap band **between slot rows** (offsets measured from the row's top, so `SLOT_H + n` lands in the gap); right-to-left returns take the band **above** the lanes, falling back to the bus below when the top band is full. A wire must never leave the page.
   * **Arc Jump Rendering:** Every edge MUST include `jumpStyle=arc;jumpSize=6;` so that whenever lines do cross, Draw.io renders a clean arc bridge.
   * **Crossing budget:** non-planarity is inherent (a Kafka hub plus a core hub forms a K₃,₃-like subgraph), so the budget is declared, not zero — the engine uses `MAX_CROSSINGS = 2` and every crossing is arc-jumped.

5. **Standard Database Icons (PostgreSQL, MySQL, MongoDB, Redis):**
   Database components **MUST use official Standard Database Icons** (Vector SVG / Image) from the standard palette rather than plain cylinders alone. **Mandatory:** All standard image icons MUST include `html=1;` and `whiteSpace=wrap;` in their style to allow multiline `<br>` labels without raw `<br>` tags leaking onto the canvas:
   * **PostgreSQL:** Official PostgreSQL Elephant SVG icon (`shape=image;html=1;whiteSpace=wrap;...image=data:image/svg+xml,...`).
   * **MySQL:** Official MySQL Dolphin icon (`shape=image;html=1;whiteSpace=wrap;...freepnglogos...`).
   * **MongoDB:** Official MongoDB Leaf icon (`shape=mxgraph.weblogos.mongodb`).
   * **Redis / Valkey:** Official Snapcraft Redis icon (`shape=image;html=1;whiteSpace=wrap;...snapcraft.io...`).

6. **Standard Gateway & Middleware Icons:**
   * **Kong API Gateway:** Official Kong Gateway logo (`shape=image;html=1;whiteSpace=wrap;image=https://seeklogo.com/images/K/kong-logo-30290787E5-seeklogo.com.png;`).
   * **Apache Kafka Event Bus:** Official Kafka broker icon (`shape=image;html=1;whiteSpace=wrap;image=https://www.svgrepo.com/show/353951/kafka-icon.svg;`).
   * **HashiCorp Vault / Core Bank:** Official Vault icon (`shape=image;html=1;whiteSpace=wrap;image=data:image/png,...`).

7. **Edge Label Discipline (Label Law):**
   * Every edge label **MUST** be ≤ 24 characters per line, ≤ 2 lines, and carry `labelBackgroundColor` so text stays readable where it crosses a wire.
   * Full topic names and payload detail **NEVER** go on the canvas: the label is the short verb or trimmed topic; the full name lives in the tooltip or the legend.
   * Labels are **placed, not guessed**: the engine searches `frac` along the wire and a vertical `off` for a position that clears every node box and its label box and rides no other wire (§5). Parallel wires on one row therefore never stack their text at one midpoint.

8. **Layout Quality Gate (Mechanical, and Self-Enforced by the Engine):**
   * `python3 resources/verify_layout.py <file>.drawio.xml` **MUST** exit 0 before publication: zero orphans, zero node overlaps, zero label violations, zero stacked wires, zero wire-through-node, no wire off the page, crossings within budget.
   * **Reachability, not just presence:** a microservice (`prIcon=pod`) that calls something but is **never called** is a violation. Drawn unreachable, the reader cannot tell where it is entered from - which is how an adaptor with no inbound wire ships unnoticed. Clients, external platforms and data stores are entry points or sinks by nature and are exempt.
   * **A cell must show its own text.** A table cell narrower or shorter than its content does not shrink the text; it draws it through the neighbouring cell. Font size is per column (a 9pt bold step cell needs a taller row than an 8pt body cell) and a wrapped row **MUST** grow to fit. This is the table's version of a label overlapping a node.
   * **No source coordinates.** A file name, a package path, a function name or a line number in a cell is a violation: the diagram is read by people without the repository open, and such a coordinate is stale the next time the code moves. Name the behaviour.
   * **Titled containers:** a panel drawn `verticalAlign=top;spacingTop=8` renders its caption inside its own top band; content **MUST** start below it, or the caption strikes through the first child row. Nothing per-element sees this - the caption is not a cell.
   * The generator **gates its own output** and refuses to write a file its checker rejects — a model that cannot route cleanly is a *modelling* problem (too few slots, too many edges on one node, an over-long label), so it fails loudly with the violation list instead of shipping. A refused model leaves no file behind.
   * **Annotations are not components:** text cells (`style="text;..."`) are excluded from the orphan and overlap checks. A title or legend line cannot be wired, so flagging it as an orphan is a false positive that teaches readers to ignore the gate.
   * Fix violations in the declarative model (slots, labels, edge kinds) and regenerate — never by hand-nudging coordinates in the generated XML.

---

## 1. Microservice Layer Taxonomy & Responsibilities

Every microservice in the platform belongs to one of four strict architectural layers. Misplacement of responsibilities violates zero-crossing security and audit invariants.

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             CLIENT & INBOUND RAILS                                                    │
│                       Mobile App (iOS/Android)  │  Inbound WebViews  │  Async Webhook Callbacks                       │
└─────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┘
                                          │ HTTPS / Native JS Bridge
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       GATEWAY LAYER (SWIMLANE 2)                                                      │
│                     Kong API Gateway (External / Internal, JWT Auth, Device-Fp Plugin)                                │
└─────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┘
                                          │ Internal HTTP / REST
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      CHANNEL BFF LAYER (SWIMLANE 3)                                                   │
│                                            bff-mobile-*                                                               │
│                     (Envelope Unwrapping, Session Token Translation, Scoped Tokens for WebViews)                      │
└─────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┘
                                          │ Internal HTTP / REST
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     ORCHESTRATION LAYER (SWIMLANE 4)                                                  │
│                                            orch-*                                                                     │
│                             (2PC Distributed Saga, Readiness Checks, Kafka Producer)                                  │
└─────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┘
                                          │ REST
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     DOMAIN CORE LAYER (SWIMLANE 5)                                                    │
│                                            core-*                                                                     │
│                         (Domain State Machines, Business Rules, PostgreSQL DB, Redis Cache)                           │
└─────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┘
                                          │ REST / mTLS
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      ADAPTOR LAYER (SWIMLANE 6)                                                       │
│                                        adaptor-* / adapter-*                                                          │
│                             (Strictly Outbound Boundary Protocol Translators)                                         │
└─────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┘
                                          │ Protocols / mTLS
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                ENTERPRISE PLATFORMS & CORE BANK (SWIMLANE 7)                                          │
│                             CCD (MDM), DOPA, NDID, eConsent, DCB / TM Vault, Kafka                                    │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Standard Technology & Database Icons (Std Icons)

The following styles represent the official standard technology icons used across all KTB/Infinitas architecture diagrams.

### 2.1. Standard Database Icons (PostgreSQL, MySQL, MongoDB, Redis)

#### 1. PostgreSQL Database Standard Icon:
```xml
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NCIgdmlld0JveD0iMCAwIDI1LjYgMjUuNiIgaGVpZ2h0PSI2NCI+PHN0eWxlPi5Ce3N0cm9rZS1saW5lY2FwOnJvdW5kfS5De3N0cm9rZS1saW5lam9pbjpyb3VuZH0uRHtzdHJva2UtbGluZWpvaW46bWl0ZXJ9LkV7c3Ryb2tlLXdpZHRoOi43MTZ9PC9zdHlsZT48ZyBzdHJva2U9IiNmZmYiIGZpbGw9Im5vbmUiPjxwYXRoIGNsYXNzPSJEIiBzdHJva2Utd2lkdGg9IjIuMTQ5IiBzdHJva2UtbGluZWNhcD0iYnV0dCIgc3Ryb2tlPSIjMDAwIiBmaWxsPSIjMDAwIiBkPSJNMTguOTgzIDE4LjYzNmMuMTYzLTEuMzU3LjExNC0xLjU1NSAxLjEyNC0xLjMzNmwuMjU3LjAyM2MuNzc3LjAzNSAxLjc5My0uMTI1IDIuNC0uNDAyIDEuMjg1LS41OTYgMi4wNDctMS41OTIuNzgtMS4zMy0yLjg5LjU5Ni0zLjEtLjM4My0zLjEtLjM4MyAzLjA1My00LjUzIDQuMzMtMTAuMjggMy4yMjctMTEuNjg3LTMuMDA0LTMuODQtOC4yMDUtMi4wMjQtOC4yOTItMS45NzVsLS4wMjguMDA1Yy0uNTctLjEyLTEuMi0uMTktMS45My0uMi0xLjMwOC0uMDItMi4zLjM0My0zLjA1NC45MTQgMCAwLTkuMjc3LTMuODIyLTguODQ2IDQuODA3LjA5MiAxLjgzNiAyLjYzIDEzLjkgNS42NiAxMC4yNUM4LjI5IDE1Ljk4NyA5LjM2IDE0Ljg2IDkuMzYgMTQuODZjLjUzLjM1MyAxLjE2Ny41MzMgMS44MzQuNDY4bC4wNTItLjA0NGEyLjAxIDIuMDEgMCAwIDAgLjAyMS41MThjLS43OC44NzItLjU1IDEuMDI1LTIuMTEgMS4zNDYtMS41NzguMzI1LS42NS45MDQtLjA0NiAxLjA1Ni43MzQuMTg0IDIuNDMyLjQ0NCAzLjU4LTEuMTYybC0uMDQ2LjE4M2MuMzA2LjI0NS4yODUgMS43Ni4zMyAyLjg0MnMuMTE2IDIuMDkzLjMzNyAyLjY4OC40OCAyLjEzIDIuNTMgMS43YzEuNzEzLS4zNjcgMy4wMjMtLjg5NiAzLjE0My01LjgxIi8+PHBhdGggc3Ryb2tlPSJub25lIiBmaWxsPSIjMzM2NzkxIiBkPSJNMjMuNTM1IDE1LjZjLTIuODkuNTk2LTMuMS0uMzgzLTMuMS0uMzgzIDMuMDUzLTQuNTMgNC4zMy0xMC4yOCAzLjIyOC0xMS42ODctMy4wMDQtMy44NC04LjIwNS0yLjAyMy04LjI5Mi0xLjk3NmwtLjAyOC4wMDVhMTAuMzEgMTAuMzEgMCAwIDAtMS45MjktLjIwMWMtMS4zMDgtLjAyLTIuMy4zNDMtMy4wNTQuOTE0IDAgMC05LjI3OC0zLjgyMi04Ljg0NiA0LjgwNy4wOTIgMS44MzYgMi42MyAxMy45IDUuNjYgMTAuMjVDOC4yOSAxNS45ODcgOS4zNiAxNC44NiA5LjM2IDE0Ljg2Yy41My4zNTMgMS4xNjcuNTMzIDEuODM0LjQ2OGwuMDUyLS4wNDRhMi4wMiAyLjAyIDAgMCAwIC4wMjEuNTE4Yy0uNzguODcyLS41NSAxLjAyNS0yLjExIDEuMzQ2LTEuNTc4LjMyNS0uNjUuOTA0LS4wNDYgMS4wNTYuNzM0LjE4NCAyLjQzMi40NDQgMy41OC0xLjE2MmwtLjA0Ni4xODNjLjMwNi4yNDUuNTIgMS41OTMuNDg0IDIuODE1cy0uMDYgMi4wNi4xOCAyLjcxNi40OCAyLjEzIDIuNTMgMS43YzEuNzEzLS4zNjcgMi42LTEuMzIgMi43MjUtMi45MDYuMDg4LTEuMTI4LjI4Ni0uOTYyLjMtMS45N2wuMTYtLjQ3OGMuMTgzLTEuNTMuMDMtMi4wMjMgMS4wODUtMS43OTNsLjI1Ny4wMjNjLjc3Ny4wMzUgMS43OTQtLjEyNSAyLjM5LS40MDIgMS4yODUtLjU5NiAyLjA0Ny0xLjU5Mi43OC0xLjMzeiIvPjxnIGNsYXNzPSJFIj48ZyBjbGFzcz0iQiI+PHBhdGggY2xhc3M9IkMiIGQ9Ik0xMi44MTQgMTYuNDY3Yy0uMDggMi44NDYuMDIgNS43MTIuMjk4IDYuNHMuODc1IDIuMDUgMi45MjYgMS42MTJjMS43MTMtLjM2NyAyLjMzNy0xLjA3OCAyLjYwNy0yLjY0N2wuNjMzLTUuMDE3TTEwLjM1NiAyLjJTMS4wNzItMS41OTYgMS41MDQgNy4wMzNjLjA5MiAxLjgzNiAyLjYzIDEzLjkgNS42NiAxMC4yNUM4LjI3IDE1Ljk1IDkuMjcgMTQuOTA3IDkuMjcgMTQuOTA3bTYuMS0xMy40Yy0uMzIuMSA1LjE2NC0yLjAwNSA4LjI4MiAxLjk3OCAxLjEgMS40MDctLjE3NSA3LjE1Ny0zLjIyOCAxMS42ODciLz48cGF0aCBzdHJva2UtbGluZWpvaW49ImJldmVsIiBkPSJNMjAuNDI1IDE1LjE3cy4yLjk4IDMuMS4zODJjMS4yNjctLjI2Mi41MDQuNzM0LS43OCAxLjMzLTEuMDU0LjQ5LTMuNDE4LjYxNS0zLjQ1Ny0uMDYtLjEtMS43NDUgMS4yNDQtMS4yMTUgMS4xNDctMS42NTItLjA4OC0uMzk0LS42OS0uNzgtMS4wODYtMS43NDQtLjM0Ny0uODQtNC43Ni03LjI5IDEuMjI0LTYuMzMzLjIyLS4wNDUtMS41Ni01LjctNy4xNi01Ljc4MlM3Ljk5IDguMTk2IDcuOTkgOC4xOTYiLz48L2c+PGcgY2xhc3M9IkMiPjxwYXRoIGQ9Ik0xMS4yNDcgMTUuNzY4Yy0uNzguODcyLS41NSAxLjAyNS0yLjExIDEuMzQ2LTEuNTc4LjMyNS0uNjUuOTA0LS4wNDYgMS4wNTYuNzM0LjE4NCAyLjQzMi40NDQgMy41OC0xLjE2My4zNS0uNDktLjAwMi0xLjI3LS40ODItMS40NjgtLjIzMi0uMDk2LS41NDItLjIxNi0uOTQuMjN6Ii8+PHBhdGggY2xhc3M9IkIiIGQ9Ik0xMS4xOTYgMTUuNzUzYy0uMDgtLjUxMy4xNjgtMS4xMjIuNDMzLTEuODM2LjM5OC0xLjA3IDEuMzE2LTIuMTQuNTgyLTUuNTM3LS41NDctMi41My00LjIyLS41MjctNC4yMi0uMTg0cy4xNjYgMS43NC0uMDYgMy4zNjVjLS4yOTcgMi4xMjIgMS4zNSAzLjkxNiAzLjI0NiAzLjczMyIvPjwvZz48L2c+PGcgY2xhc3M9IkQiIGZpbGw9IiNmZmYiPjxwYXRoIHN0cm9rZS13aWR0aD0iLjIzOSIgZD0iTTEwLjMyMiA4LjE0NWMtLjAxNy4xMTcuMjE1LjQzLjUxNi40NzJzLjU1OC0uMjAyLjU3NS0uMzItLjIxNS0uMjQ2LS41MTYtLjI4OC0uNTYuMDItLjU3NS4xMzZ6Ii8+PHBhdGggc3Ryb2tlLXdpZHRoPSIuMTE5IiBkPSJNMTkuNDg2IDcuOTA2Yy4wMTYuMTE3LS4yMTUuNDMtLjUxNi40NzJzLS41Ni0uMjAyLS41NzUtLjMyLjIxNS0uMjQ2LjUxNi0uMjg4LjU2LjAyLjU3NS4xMzZ6Ii8+PC9nPjxwYXRoIGNsYXNzPSJCIEMgRSIgZD0iTTIwLjU2MiA3LjA5NWMuMDUuOTItLjE5OCAxLjU0NS0uMjMgMi41MjQtLjA0NiAxLjQyMi42NzggMy4wNS0uNDEzIDQuNjgiLz48L2c+PC9zdmc+;fontSize=10;fontStyle=1;align=center;"
```

#### 2. MySQL Database Standard Icon:
```xml
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://www.freepnglogos.com/uploads/logo-mysql-png/logo-mysql-mysql-logo-png-images-are-download-crazypng-21.png;fontSize=10;fontStyle=1;align=center;"
```

#### 3. MongoDB Document Database Standard Icon:
```xml
style="dashed=0;outlineConnect=0;html=1;align=center;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;shape=mxgraph.weblogos.mongodb;aspect=fixed;whiteSpace=wrap;fontSize=10;fontStyle=1;"
```

#### 4. Redis In-Memory Cache Standard Icon:
```xml
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://dashboard.snapcraft.io/site_media/appmedia/2020/08/1529926.png;fontSize=10;fontStyle=1;align=center;strokeWidth=1;fillColor=none;"
```

---

### 2.2. Standard Gateway & Middleware Icons

#### 1. Kong API Gateway Standard Icon:
```xml
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://seeklogo.com/images/K/kong-logo-30290787E5-seeklogo.com.png;fontSize=10;fontStyle=1;align=center;"
```

#### 2. Apache Kafka Event Bus Standard Icon:
```xml
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://www.svgrepo.com/show/353951/kafka-icon.svg;fontSize=10;fontStyle=1;align=center;"
```

#### 3. HashiCorp Vault / Core Bank Ledger Standard Icon:
```xml
style="shape=image;html=1;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;aspect=fixed;whiteSpace=wrap;image=data:image/png,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;fontSize=10;fontStyle=1;align=center;"
```

---

### 2.3. Mandatory `html=1;` and Newline `<br>` Encoding Rule

> [!IMPORTANT]
> **Why `html=1;` is strictly mandatory on all `shape=image;` standard icons:**
> Draw.io defaults to plain text SVG mode (`html=0`), which treats `<br>` as literal text characters (`<br>`) instead of line breaks.
> When labels contain multiline text such as:
> ```
> PostgreSQL<br>{lending_db}<br>[loan_app, limits, audit]
> ```
> or
> ```
> Redis Cache<br>{lending_cache}<br>[idempotency, lock, session]
> ```
> If `html=1;` is omitted from `shape=image;`, Draw.io will render the raw `<br>` tag directly on screen on a single horizontal line, causing wide labels to collide with adjacent nodes.
>
> **Rules for Multiline Labels on Standard Icons:**
> 1. Always append `html=1;whiteSpace=wrap;` to the style string of any standard image icon.
> 2. Use `esc(val)` to safely convert Python newlines (`\n`) into `<br>` (escaped as `&lt;br&gt;` in XML attributes). Draw.io's HTML renderer will cleanly render each line break.

---

## 3. Dedicated 7-Swimlane Architecture Blueprint & Minimal-Crossing Routing

All end-to-end HLA diagrams must use the standardized 7-swimlane spatial layout. Kong Gateway and all microservice layers (BFF, Orch, Core, Adaptor) MUST each occupy their own separate swimlane.

```
Width: ~2200px+ | Height: dynamic (slot count × 90px + bands) | Margin: X=50, lanes top Y=130,
top corridor band above LANE_TOP (reserved for returns), bus below the lanes (reserved for multi-lane spans)

┌────────────┬─────────────┬─────────────┬──────────────┬─────────────┬─────────────┬────────────────────┐
│ Swimlane 1 │ Swimlane 2  │ Swimlane 3  │  Swimlane 4  │ Swimlane 5  │ Swimlane 6  │     Swimlane 7     │
│  Client &  │   Gateway   │   Channel   │ Orchestrator │ Domain Core │   Adaptor   │ Enterprise Plats   │
│  Inbound   │    Layer    │     BFF     │    Layer     │    Layer    │    Layer    │    & Core Bank     │
│   Rails    │(Kong Gateway│(bff-mobile-*│   (orch-*)   │   (core-*)  │ (adaptor-*) │                    │
│ (W: 240px) │ (W: 180px)  │ (W: 240px)  │  (W: 260px)  │ (W: 480px)  │ (W: 240px)  │     (W: 460px)     │
├────────────┼─────────────┼─────────────┼──────────────┼─────────────┼─────────────┼────────────────────┤
│ WebViews   │ Kong API    │ bff-mobile- │ orch-lending │ core-       │ adaptor-ncb │ NCB Bureau         │
│ & Callback │ Gateway     │ lending     │ -saga        │ lending-    │             │                    │
│ Receivers  │ (Std Icon)  │             │              │ engine      │ adaptor-    │ eConsent Platform  │
│            │             │ bff-mobile- │ orch-ncb-    │             │ econsent    │                    │
│ Borrower   │ mTLS & JWT  │ auth        │ callback     │ PostgreSQL  │             │ DCB (TM Vault Core │
│ App        │ Device-Fp   │             │              │ (Std SVG)   │ adaptor-    │ with Vault Icon)   │
│            │             │             │              │             │ dcb-loan    │                    │
│            │             │             │              │ Redis       │             │ Kafka Event Bus    │
│            │             │             │              │ (Std Icon)  │ adaptor-    │ (Kafka Std Icon)   │
│            │             │             │              │             │ promptpay   │                    │
└────────────┴─────────────┴─────────────┴──────────────┴─────────────┴─────────────┴────────────────────┘
```

### 3.1. Slot Assignment Principles (How to Pick the Y-Slot)

The engine fixes every Y from the node's **slot** (§5) — slot assignment is the design decision you make, and it is what keeps wires straight. Assign slots by **functional track**: services that form one end-to-end flow share a row, so the whole chain renders as a single straight horizontal line:

1. **Bureau & Async Callback Track:** webhook rail → Kong → `orch-*-callback` → `core-*-scoring` → `adaptor-*-cb` → bureau, all on the same slot. The webhook return takes its own top-corridor row.
2. **Consent & Contract Track:** saga → `core-loan-contract` → `adaptor-econsent` → eConsent platform.
3. **Deposit & Disbursement Track:** saga → `core-deposit-account` → `adaptor-dcb-loan` → core bank.
4. **Notification & Payout Track:** saga → `core-notification-submit` → `adaptor-promptpay` → platform.
5. **Mainline Journey Track:** mobile app → Kong → BFF → saga → core engine → PostgreSQL/Redis.
6. **Event publication** does not need a slot-aligned target: multi-lane `event` edges ride a corridor row regardless of the row they leave.

One node per `(lane, slot)` — the engine rejects duplicates. When two flows would collide on a row, give the newer one the next free slot; never share a slot to "save space" (that is what produced stacked wires and overlapping labels).

---

## 4. Draw.io Multi-Page XML Requirement

A Draw.io document must be wrapped in `<mxfile host="app.diagrams.net" pages="N">` and contain:
1. `<diagram name="HLA Overview" id="...">`
2. `<diagram name="Standard Colors and Icons" id="ao9VHCrxs2CTfegMv53f">`
3. any further views (a step trace, a legend) after those two, never before.

**A trace page describes behaviour, not code.** When the third page enumerates
steps, its columns are business-facing: step id, business action, actor, call,
target component, tables touched. It **MUST NOT** carry a file name, a function
name or a line number - the page is read by people without the repository open,
and such a coordinate is stale the next time the code moves. A step whose
integration is simulated in-process is **not** an implemented path: leave it off
the trace, or mark it, rather than listing it beside real routes where a reader
cannot tell them apart. The gate enforces the text half of this (`No source
coordinates`, §6); whether a row belongs on the page is a modelling decision.

---

## 5. Layout Engine (Declarative Generator)

Hand-placed coordinates are what produce overlapping wires and stacked labels. Build diagrams with the declarative engine instead: fill three tables — lanes, nodes (lane + slot), edges (kind + short label + status) — and the engine derives every coordinate, routes corridors, and enforces the label law.

**Where labels come from.** An edge label is the short verb or the trimmed topic
("payout", "webhook.recieve"), never the full route or the full topic name - the
full text goes in the tooltip.

**Labels that carry step ids.** A trace diagram puts the flow name on line one
and the step list on line two. Give the edge a 7th tuple element, the steps it
carries, and the engine renders and verifies the label:

```python
EDGES = [
    ("e_saga", "n_bff", "n_orch_saga", "sync", "REST", "impl",
     ("A1", "A2", "A3", "A4", "B1")),          # -> "REST" / "A1-A4,B1"
]
```

* `-` is an exact consecutive range, and the engine **proves** the rendered
  label enumerates exactly the steps the edge carries. Extending a range from
  the previous element instead of tracking its start is a real bug that drops
  ids silently (`A1,A2,A3` rendered as `A2-A3`); the validator refuses it.
* `..` marks a **bracket**: `A2.2..B10.2 (15)`. A list too long for the 24-char
  bound is named by its endpoints and count and enumerated elsewhere (the trace
  page), so the label never claims to name every step.
* Never label a wire with a step the wire does not travel. A step with no wire
  of its own belongs in the trace table, not guessed onto a nearby edge.

```python
# resources/hla_generator.py — edit the tables at the top, then run:
#   python3 hla_generator.py out.drawio.xml
LANES = [  # (id, title, width, fill, stroke) — left to right
    ("lane_client", "Client & Inbound Rails", 240, "#ECECEC", "#4a5568"),
    # ... one lane per tier, never merged (Invariant 2)
]
NODES = [  # (id, lane, slot, label, kind) — one node per (lane, slot)
    ("n_kong", "lane_gw", 3, "Kong API Gateway", "pod_new"),
    ("n_db", "lane_core", 4, "PostgreSQL\n(sample_db)", "pod_reuse"),
]
EDGES = [  # (id, src, dst, kind, label, status) — kind: sync | async | event | view
    ("e_pay", "n_orch_saga", "n_adapt_pay", "sync", "payout", "impl"),
    ("e_kafka", "n_orch_saga", "n_kafka", "event", "loan.events", "impl"),
    ("e_kyc", "n_orch_saga", "n_kyc", "sync", "planned KYC", "spec"),
]
```

**One model, three views (spec and implementation cannot drift).** `status` on a
node or an edge is `impl` (built, the default when omitted) or `spec` (designed,
not built). Rendering is chosen by one flag:

```bash
python3 hla_generator.py out.drawio.xml              # both; spec items grey+dashed
python3 hla_generator.py out.drawio.xml --from impl  # only what is built
python3 hla_generator.py out.drawio.xml --from spec  # only what is designed
```

A `spec` node or edge renders **grey and dashed** so a plan never reads as a
fact. Nodes are never filtered out: a component declared in the model but not
wired in the current view is dimmed, not dropped - dropping it would hide the
service, and dimming says "nothing here yet" without denying it exists. The
title band states which view is on the page and how many edges are built versus
planned. Deriving both views from one table is the point: two hand-maintained
diagrams that disagree about what exists are worse than one that marks the gap.

**Reconciling against code.** Filling `status` is where a design and a
repository are compared: mark `impl` only what you can point at in the code, and
anything you cannot is `spec`. When a component is documented but has **no code
reference anywhere**, leaving it in the model as `spec` is right and drawing it
as built is not - an unreachable service on a "current architecture" page is a
false statement, and the gate's reachability rule will not save you because the
wire can be invented as easily as the node.

**Routing law (implemented in the engine; do not freehand around it):**
* **Rows:** a node's slot fixes its Y. Forward edges between adjacent lanes run straight on the row (equal Y-band).
* **Dips:** a forward edge spanning 2+ lanes over an occupied row dips through the inter-row gap band (below the row's labels, above the next row's nodes), choosing the side (above/below) with fewer same-lane hop conflicts, and exits vertically (`exitX=0.75`) so it never shares a ray with a straight row wire.
* **Event bus:** multi-lane `event` edges route through a corridor row, shared by span (interval colouring), not one row per edge.
* **Returns:** backward (right-to-left) edges take the band above the lane band with explicit waypoints, falling back below the lanes when that band is full — never through lane headers, never off the page.
* **Same-lane hops:** *every* same-lane hop leaves and re-enters through the lane's **node-free side channel**, never the node centre — the centre of one node lies inside every node stacked with it in that lane.
* **Anchors:** each edge's exit/entry is offset along the node's edge, so wires sharing a row are parallel rather than collinear (collinear wires are what the checker calls `stacked`).
* **Waypoint y:** a waypoint's y **MUST** equal its anchor's y. A waypoint on the bare row y with an offset anchor makes the first segment diagonal, and the checker then reports crossings that do not exist.
* **Arc jumps:** every edge style carries `jumpStyle=arc;jumpSize=6;`.
* **Labels obey the label law (Invariant 7)** — the engine rejects over-long labels at generation time, and then **places** each label: it walks the wire and searches a vertical offset for a spot that clears every node box, every node label box, and every other wire. That search is what removes the "label rides wire" warnings instead of merely tolerating them.

The engine resolves `resources/standard_icons_tab.xml` relative to its own file location (no absolute paths), assembles the mandatory 2-page structure (§4), and validates the XML with `ElementTree.parse` before writing.


---

## 6. Layout Verification Gate (Reachability, Fit, and No Code Leaks)

Run the gate on every generated `.drawio.xml` before publication — it exits non-zero on any violation, so clean layout is a check, not an eyeball review:

```bash
python3 resources/verify_layout.py out.drawio.xml              # default: 0-crossing budget
python3 resources/verify_layout.py out.drawio.xml --max-crossings=2
```

Beyond layout, the gate reads the diagram the way a reviewer does and fails on
four defects that geometry alone cannot see (each was a real reported defect):

| Rule | Fails when |
|---|---|
| **Reachability** | a `prIcon=pod` microservice has no incoming wire; clients, external platforms and stores are entry points or sinks and are exempt |
| **Cell fit** | any cell's text cannot fit its own box at its own font size, in either dimension — the table's version of a label overlapping a node |
| **No source coordinates** | a cell carries a file name, a package path, a function name or a line number |
| **Title band** | a titled container's content starts inside its own caption band, so the caption strikes through it |

The last two are the ones a diagram review always catches and a geometry check
never does. A source coordinate is stale the next time the code moves, and the
diagram is read by people without the repository open; a caption struck by its
first row looks like a rendering bug even though every element is legal.

**The gates:**
1. **Connectivity** — zero orphan nodes; `*callback*` receivers must have BOTH an incoming trigger and an outgoing downstream call.
2. **Node overlap** — component boxes (including their below-icon label overflow) must not collide with each other.
3. **Label hygiene** — every edge label obeys the label law (≤ 24 chars × 2 lines); no label may overlap a node.
4. **Wire discipline** — no two wires stacked on the same line; no wire may pass through a node it does not source or target; crossings within the declared budget (every edge is arc-jumped, so a budgeted crossing renders as a clean bridge).
5. **Wire envelope** — no wire leaves the page, and none strays past the lane band horizontally. A bus below the lanes is legitimate (the event-bus rule), so depth is reported as a warning, while leaving the page is a hard failure. This is the "lines go to the bottom of the page" defect: it is invisible to every per-segment rule, because each segment is individually legal.

`RESULT: PASS` with exit 0 is the publication gate. On `FAIL`, fix the declarative model (slot assignments, labels, edge kinds) and regenerate — never hand-nudge coordinates in the XML, because the next regeneration loses them.

The generator calls this module directly (`verify_layout.verify(..., quiet=True)`) and **refuses to write** a file that fails, printing the violations and exiting non-zero. The checker is therefore a sensor the engine cannot forget to run, not a step someone must remember. Annotations (`style="text;..."`) are excluded from the orphan and overlap checks: a title or legend line cannot be wired.

Connectivity is checked against the **whole model**, once, inside `_validate_model`. A filtered render (design-only or implementation-only) legitimately shows unwired components, so `verify(..., require_connectivity=False)` is only for those views - never for the complete diagram.


---

## 7. Pre-Flight Architecture Verification Checklist

Before publishing any Draw.io HLA diagram, verify the following:

- [ ] **Zero Orphan Nodes:** Every single component (especially `orch-*-callback` and background workers) has verified incoming triggers and outgoing downstream calls.
- [ ] **Engine Routing Law:** Rows straight on slot bands; multi-lane spans dip through the inter-row gap bands; returns above the lanes; same-lane hops via the lane's **node-free side channel**; every vertical allocated by interval colouring, never on a node centre (§5).
- [ ] **Wire Envelope:** no wire runs off the page or outside the lane band horizontally — the engine's own gate rejects it, and a refusal leaves no file (§6).
- [ ] **Reachability:** every microservice has an incoming wire; every external platform and store an outgoing one (§6).
- [ ] **Cell fit:** every table cell is sized for its own text at its own font size, and no cell carries a file name, function name or line number (§6).
- [ ] **Provenance stated:** the model's `status` fields say what is built and what is only designed, and the rendered view matches the question being asked (§5).
- [ ] **Labels carry their steps:** a wire labelled with step ids reproduces exactly the steps it carries — the engine proves it, and a range that silently drops an id is refused (§5).
- [ ] **Label Law:** every edge label ≤ 24 chars × 2 lines with `labelBackgroundColor`; full topic names live in tooltips or the legend, never on the canvas.
- [ ] **Layout Gate:** `python3 resources/verify_layout.py <file>` exits 0 — zero orphans, zero overlaps, zero stacking, crossings within budget (§6).
- [ ] **Arc Jumps Configured:** All crossing edges have `jumpStyle=arc;jumpSize=6;` configured.
- [ ] **Dedicated Swimlanes:** Kong Gateway, Channel BFF, Orchestrator, Domain Core, and Adaptor each reside in their own separate swimlane. No tier merging.
- [ ] **Standard Database Icons:** PostgreSQL, MySQL, MongoDB, and Redis use official Standard Icons from the standard palette rather than plain cylinders alone.
- [ ] **Mandatory 2-Page Structure:** The XML has `pages="2"` and contains both `<diagram name="... HLA ...">` and `<diagram name="Standard Colors and Icons" id="ao9VHCrxs2CTfegMv53f">`.
- [ ] **Standard Technology Icons Used:** Redis, Kafka, Kong, Vault, and DBs use official Std icons (`shape=image;...`).
- [ ] **Multiline Label HTML Formatting (`html=1;`):** All `shape=image;` icons with multiline text (`<br>`) have `html=1;whiteSpace=wrap;` in their style string so that raw `<br>` tags never appear on the canvas.
- [ ] **BFF Layer Isolation:** All `bff-mobile-*` services reside exclusively in Swimlane 3 and route directly to Core or Orchestrator. No client connects to Cores directly.
- [ ] **Orchestrator Responsibility:** `orch-*` coordinates sagas, 2PC readiness-checks, and multi-domain inquiries. It does not own persistent domain tables.
- [ ] **Domain Core Integrity:** `core-*` owns its domain entities and PostgreSQL tables. It connects downstream strictly via adaptors.
- [ ] **Adaptor Directionality:** `adaptor-*` / `adapter-*` calls external platforms strictly outbound; no inbound backward calls to Cores.
- [ ] **Lifecycle Color Accuracy:** New components are `#03CCFF`, enhanced are `#92D14F`, reused are `#BFBFBF`, and 3rd-party systems are `#EF7D30`.
- [ ] **Connection Precision:** Synchronous calls are solid lines; callbacks, WebViews, and Kafka events are dashed lines.
- [ ] **XML Well-Formedness:** File parses cleanly with `xml.etree.ElementTree.parse()` without entity or bracket syntax errors.


