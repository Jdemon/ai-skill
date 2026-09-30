---
name: drawio-hla-architect
description: >-
  Enterprise Solution Architecture skill for authoring and QA-auditing High-Level Architecture (HLA)
  diagrams in draw.io format (.drawio). Enforces KTB/Infinitas/Arise/Virtual Bank ecosystem
  standards: dedicated 7-swimlane isolation (Kong Gateway, BFF, Orch, Core, Adaptor, External),
  official Kubernetes Pod styling (New #03CCFF, Enhanced #92D14F, Existing #BFBFBF, External #EF7D30),
  standard technology icons (PostgreSQL, Redis, Kafka, Kong), mandatory multi-page structure with
  Standard Colors & Icons tab (STD), zero-orphan verification, topological edge anchoring, sequence
  step labeling, and automated QA linting via built-in agents. Completely self-contained and portable.
---

# Draw.io Enterprise HLA Architecture & Governance Guide

This skill provides comprehensive standards, XML templates, visual conventions, and automated tooling for authoring and QA-auditing enterprise **High-Level Architecture (HLA)** diagrams in `draw.io` format (`.drawio` without `.xml` suffix). 

The standards are derived directly from real-world human-authored banking architectures in the **KTB / Infinitas / Arise / Virtual Bank (Paotang)** ecosystem (`Onboard_HLD.drawio.xml`, `SQ1-Marketing.drawio.xml`, `SQ1-Marketing-2.drawio.xml`, `SQ4.drawio (1).xml`).

> [!IMPORTANT]
> **Portability Guarantee:**
> This skill directory (`drawio-hla-architect/`) is **100% self-contained**. It contains no hardcoded absolute machine paths. You can copy the entire `drawio-hla-architect/` directory to any folder, device, or cloud environment and it will function immediately.

---

## 👥 Dual Specialized Architecture Agents

This skill defines two specialized agent roles located in the `agents/` directory:

1. **HLA Draw.io Architect ("คนเขียน HLA draw.io")** — [`agents/hla_architect_agent.md`](./agents/hla_architect_agent.md):
   * **Role:** Senior Solution Architect who drafts end-to-end, production-grade 2-page Draw.io HLA diagrams from business requirements, user stories, or PRDs.
   * **Responsibilities:** Multi-tier swimlane layout, planar Y-band track routing, Kubernetes pod styling, sequence numbering on edges (`1 - POST /v1/... (NEW)`), Redis cache schemas, Kafka topic specifications, and Page 2 STD tab embedding.

2. **HLA Draw.io QA Reviewer ("QA ตรวจสอบ HLA draw.io")** — [`agents/hla_qa_reviewer_agent.md`](./agents/hla_qa_reviewer_agent.md):
   * **Role:** Chief Architecture Governance Auditor who validates diagrams against the 9 Enterprise Invariants.
   * **Responsibilities:** Runs automated linter [`scripts/qa_verify_hla.py`](./scripts/qa_verify_hla.py), detects unanchored floating lines, audits zero-orphan connectivity, checks lifecycle hex codes, verifies HTML `<br>` safety, and produces structured pass/fail reports.

---

## 🏛️ 9 Mandatory Architectural Invariants

### 1. Mandatory Multi-Page Draw.io Structure
Every generated Draw.io XML HLA diagram **MUST include at least two pages/tabs**:
* **Page 1 (`HLA Overview`):** The end-to-end multi-swimlane architecture diagram.
* **Page 2 (`Standard Colors and Icons` / `id="ao9VHCrxs2CTfegMv53f"` or `STD` / `id="t2Yd3kyUYJbDHsi3N8cM"`): The complete enterprise standard palette tab, containing the Component Lifecycle Matrix (New, Enhanced, Existing, External), Connection Types (Sync, Async, Kafka, Token), Kubernetes Pod shapes, color-coded Database Cylinders, and official Technology & Infrastructure Icons.
* *Resource Location:* The official Page 2 XML is located in `./resources/standard_icons_tab.xml` relative to this skill.

### 2. Dedicated Swimlane for Every Tier (Universal 7-Tier Standard)
Architectural tiers must **NEVER be combined into a single column**. Each layer must reside in its own dedicated vertical swimlane, applicable to **ANY enterprise domain** (Fintech, Banking, Retail, E-Commerce, Logistics, Healthcare, Telecom, etc.):
* **Swimlane 1:** `Client & Inbound Rails` (Mobile App, Web Portals, POS, Inbound Partner Webhooks)
* **Swimlane 2:** `Gateway Layer (API Gateway)` (Kong API Gateway, Apigee, Envoy, OAuth2/JWT Auth, Rate Limiting)
* **Swimlane 3:** `Channel BFF Layer (bff-*)` (Dedicated BFF lane: `bff-mobile-*`, `bff-web-*`, `bff-merchant-*`, envelope unwrapping)
* **Swimlane 4:** `Orchestration Layer (orch-*)` (Dedicated Saga lane: Distributed 2PC Saga coordination, readiness checks, domain aggregation, Kafka subscribers, async callback receivers)
* **Swimlane 5:** `Domain Core Layer (core-*)` (Dedicated Core lane: State machine, business rules, persistence, caches)
* **Swimlane 6:** `Adaptor Layer (adaptor-* / adapter-*)` (Dedicated Adaptor lane: Strictly outbound boundary protocol translators)
* **Swimlane 7:** `Enterprise Platforms & External Rails` (Enterprise platforms, core engines, partner rails, Kafka event bus, external 3rd-party services)

> [!NOTE]
> **Common Architecture (Not Fixed to "VB Mobile Channel"):**
> The HLA standard is **domain-agnostic**. It is NOT locked to "VB Mobile Channel" or "Virtual Bank".
> Swimlanes 3 to 6 may optionally be enclosed inside a configurable top-level system container representing the scope of the platform:
> * Examples: `<Product> Core Platform`, `Retail & Smart Fulfillment Platform`, `Digital Lending Platform`, `Enterprise CRM Engine`, or omitted entirely when modeling multi-platform enterprise ecosystems.

### 2.1. Comprehensive Geometry Clearance & Anti-Overlap Standards
To prevent text obscuration, title collisions, and crowded components across any system:
* **Outer Container vs Child Swimlanes ($\Delta y \ge 50\text{--}55\text{px}$):** When using an outer grouping container (such as `<System> Core Platform`), place the container at `y = 25` and child swimlanes at `y = 80`. This provides 55px of vertical clearance so the container's title text is never covered by child lane headers.
* **Swimlane Header vs Child Components ($\Delta y \ge 40\text{px}$, components at $y \ge 120$):** Swimlane headers occupy the top band ($y = 80\text{--}115\text{px}$). All microservices, pods, and database icons MUST be placed at $y \ge 120$ (relative to canvas) so component boxes and icons never collide with or cover swimlane title labels.
* **Horizontal Clearance before Adjacent Tiers ($\Delta x \ge 20\text{--}25\text{px}$):** An outer container's right boundary (`x + width`) must strictly terminate before adjacent independent swimlanes. For example, if the container ends at `x = 1790`, the next lane (e.g. `lane_ext`) must start at `x = 1820` (providing a clean 30px whitespace gap).
* **Component-to-Component Clearance ($\Delta x \ge 40\text{px}, \Delta y \ge 50\text{px}$):** Microservices, database cylinders, and note callouts must never overlap each other. Maintain at least 40px horizontal spacing and 50px vertical spacing between adjacent nodes.
* **Edge Label Clearance:** Flow sequence labels on edges must have sufficient offset (`dy = -12` or `dy = 12`) and must not collide with pod borders or database cylinders.

### 2.2. Horizontal Swimlane Centering Rule (Single vs Multi-Microservice)
When a swimlane contains only one microservice (or component) on a given track/row, it **MUST be horizontally centered** within that swimlane:
$$\text{center\_x} = \text{lane\_x} + \frac{\text{lane\_width} - \text{component\_width}}{2}$$

For standard 7-swimlanes (widths: client=240, gw=180, bff=220, orch=260, core=485, adapt=260, ext=520):
* **Client Lane** ($x=40, w=240$): Single component ($w=44$) $\rightarrow x = 40 + (240-44)/2 = \mathbf{138}$
* **Gateway Lane** ($x=295, w=180$): Single component ($w=45$) $\rightarrow x = 295 + (180-45)/2 = \mathbf{363}$
* **Channel BFF Lane** ($x=505, w=220$): Single component ($w=44$) $\rightarrow x = 505 + (220-44)/2 = \mathbf{593}$
* **Orchestration Lane** ($x=740, w=260$): Single component ($w=44$) $\rightarrow x = 740 + (260-44)/2 = \mathbf{848}$
* **Domain Core Lane** ($x=1015, w=485$): Single component ($w=44$) $\rightarrow x = 1015 + (485-44)/2 = \mathbf{1236}$
* **Adaptor Lane** ($x=1515, w=260$): Single component ($w=44$) $\rightarrow x = 1515 + (260-44)/2 = \mathbf{1623}$
* **External Lane** ($x=1820, w=520$): Single component ($w=44$) $\rightarrow x = 1820 + (520-44)/2 = \mathbf{2058}$ (or width 160 box: $x=2000$)

> [!TIP]
> **Automated Centering via Builder:**
> In `HLADiagramBuilder`, simply pass `lane="lane_id"` (e.g. `builder.add_pod("node_bff", "bff-mobile-payment", "enhanced", lane="lane_bff", y=220)`), or use `builder.get_lane_center_x(lane_id, width)` and `builder.get_lane_col_x(lane_id, col, total_cols, width)` for multi-column tracks.

### 3. Zero Orphan Nodes & Strict Topological Edge Anchoring

* Every microservice placed on an HLA diagram **MUST have complete incoming and outgoing connectivity**.
* **Strict Source/Target Binding:** Hand-drawn human diagrams often suffer from floating lines (`source=None` or `target=None`). In this skill, every `<mxCell edge="1">` MUST explicitly specify `source="<source_id>"` and `target="<target_id>"`.
* **Async Callback Flow Requirement:** When an asynchronous callback receiver microservice (`orch-*-callback`) is present:
  1. External Platform sends async webhook $\rightarrow$ Top Corridor (Y < 120px) $\rightarrow$ Inbound Webhook endpoint in Swimlane 1.
  2. Inbound Webhook $\rightarrow$ routes through Gateway to Orchestrator Callback Receiver (`orch-*-callback`) in Swimlane 4.
  3. Callback Receiver $\rightarrow$ calls Domain Core (`core-*`) in Swimlane 5 to update status, store verification scores, or advance the 2PC saga.

### 4. Edge Labeling with Sequence Numbers & API Endpoints
Real-world human architects annotate connections with detailed sequence numbers and endpoint paths. Empty connections without business context are forbidden:
* **Format:** `<step> - <HTTP_METHOD> <path> [(NEW|enhance|opt)]`
* **Real Production Examples from KTB/VB:**
  * `1 - POST /v1/restriction/check (NEW)`
  * `2 - POST /v1/campaign/reserve`
  * `3.1(opt) - POST /v1/campaign/cancel`
  * `4 - POST /v1/campaign/accept`
  * `POST /vb/v1/bff-mobile-deposit-sof/v1/account/inquiry/summary (enhance)`
  * `POST /v1/deposit/account/inquiry`
  * `async event insert/update campaign_quota`
  * `fallback: redis data`

### 5. Wire-Crossing Minimization & Arc Jump Bridges
* **Horizontal Track Alignment (Equal Y-Band):** Group related microservices along the same horizontal track (Y band) so that request $\rightarrow$ response flows travel straight horizontally.
* **Top & Bottom Bypass Corridors:** Long-range return flows that travel backward from right to left (e.g. external async webhooks returning from Column 7 to Column 1, or token handoffs to WebViews) **MUST be routed through dedicated top corridors (Y < 120px) or bottom corridors (Y > 800px)** with explicit orthogonal waypoints (`<Array as="points"><mxPoint x="..." y="..."/></Array>`). They must NEVER cut diagonally across middle tiers!
* **Arc Jump Rendering:** Every edge MUST include `jumpStyle=arc;jumpSize=6;` so that whenever lines do cross, Draw.io automatically renders a clean arc bridge.

### 6. Component Lifecycle Matrix (Standard Colors)
All components must declare their lifecycle state using exact enterprise hex codes:

| Lifecycle State | Pod Stroke Color | Pod Fill Color | Pod Stroke Width | Database / Entity Fill | Edge Stroke Color |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **New (KTB/Infinitas/Arise)** | `#03CCFF` | `#dae8fc` | `2px` | `#03CCFF` | `#03CCFF` |
| **Enhanced Component** | `#92D14F` | `#d5e8d4` | `2px` | `#92D14F` | `#92D14F` |
| **Existing / Reused** | `#BFBFBF` | `#f5f5f5` | `1.5px` | `#BFBFBF` | `#BFBFBF` |
| **External / 3rd Party** | `#EF7D30` | `#ffe6cc` | `1.5px` | `#EF7D30` | `#EF7D30` |
| **Kafka Event Bus** | N/A | N/A | N/A | N/A | `#FF6A00` (dashed, flowAnimation=1) |

### 7. Mandatory `html=1;` and Newline `<br>` Encoding Rule
> [!CAUTION]
> Draw.io defaults to plain text SVG mode (`html=0`), which treats `<br>` as literal text characters (`<br>`) instead of line breaks.
> When labels contain multiline text such as `PostgreSQL<br>{db_name}<br>[tables]`, omitting `html=1;` causes raw `<br>` tags to leak visibly onto the diagram canvas!
> **Rule:** Every image icon and cylinder MUST append `html=1;whiteSpace=wrap;` to its style string.

### 8. Kafka Event Bus & Topic Standards
* **Enterprise Topic Naming Standard:** `<system>.<domain>.<event>.<ENV>`
  * *E-Commerce & Retail:* `ecommerce.logistics.order.fulfilled.PROD`
  * *Digital Lending / Fintech:* `lending.origination.loan.disbursed.DEV`
  * *Banking Rails:* `vb.int.notification.inbox.DEV`, `banking.transfer.completed.PROD`
  * *Supply Chain / IoT:* `iot.telemetry.gateway.heartbeat.UAT`
* **Edge Style:** Dashed line with animated flow:
  `edgeStyle=orthogonalEdgeStyle;dashed=1;flowAnimation=1;strokeColor=#FF6A00;strokeWidth=2;endArrow=classic;`
* **DLQ Callout Notes:** Amber note boxes (`fillColor=#fad7ac;strokeColor=#b46504`) for edge cases: `TBC: DLQ on event processing failure / retry policy`.

### 9. Redis Cache Schemas & Lua Script Notes
In human banking diagrams, architects explicitly document Redis key structures and scripts near the Redis icon:
```text
KEY:     VB_INT_PARTNER::AUTH::{AUTH_CODE}
VALUE:   cifID, ccdID, accessibleData
EXPIRED: 15 min
```
```text
EVAL Lua script: reserve, accept, cancel, timeout_reservation
```

---

## 📐 Enterprise Style Strings Reference

### Kubernetes Pods with Mandatory Connection Points
```xml
<!-- New Microservice (#03CCFF) -->
style="sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#dae8fc;strokeColor=#03CCFF;strokeWidth=2;points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;"

<!-- Enhanced Microservice (#92D14F) -->
style="sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#d5e8d4;strokeColor=#92D14F;strokeWidth=2;points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;"

<!-- Existing / Reused Microservice (#BFBFBF) -->
style="sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#f5f5f5;strokeColor=#BFBFBF;strokeWidth=1.5;points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;"

<!-- External Microservice / 3rd Party (#EF7D30) -->
style="sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#ffe6cc;strokeColor=#EF7D30;strokeWidth=1.5;points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;"
```

### Standard Infrastructure & Vector Database Icons
```xml
<!-- PostgreSQL Vector SVG Icon (Mandatory html=1;) -->
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NCIgdmlld0JveD0iMCAwIDI1LjYgMjUuNiIgaGVpZ2h0PSI2NCI+PHN0eWxlPi5Ce3N0cm9rZS1saW5lY2FwOnJvdW5kfS5De3N0cm9rZS1saW5lam9pbjpyb3VuZH0uRHtzdHJva2UtbGluZWpvaW46bWl0ZXJ9LkV7c3Ryb2tlLXdpZHRoOi43MTZ9PC9zdHlsZT48ZyBzdHJva2U9IiNmZmYiIGZpbGw9Im5vbmUiPjxwYXRoIGNsYXNzPSJEIiBzdHJva2Utd2lkdGg9IjIuMTQ5IiBzdHJva2UtbGluZWNhcD0iYnV0dCIgc3Ryb2tlPSIjMDAwIiBmaWxsPSIjMDAwIiBkPSJNMTguOTgzIDE4LjYzNmMuMTYzLTEuMzU3LjExNC0xLjU1NSAxLjEyNC0xLjMzNmwuMjU3LjAyM2MuNzc3LjAzNSAxLjc5My0uMTI1IDIuNC0uNDAyIDEuMjg1LS41OTYgMi4wNDctMS41OTIuNzgtMS4zMy0yLjg5LjU5Ni0zLjEtLjM4My0zLjEtLjM4MyAzLjA1My00LjUzIDQuMzMtMTAuMjggMy4yMjctMTEuNjg3LTMuMDA0LTMuODQtOC4yMDUtMi4wMjQtOC4yOTItMS45NzVsLS4wMjguMDA1Yy0uNTctLjEyLTEuMi0uMTktMS45My0uMi0xLjMwOC0uMDItMi4zLjM0My0zLjA1NC45MTQgMCAwLTkuMjc3LTMuODIyLTguODQ2IDQuODA3LjA5MiAxLjgzNiAyLjYzIDEzLjkgNS42NiAxMC4yNUM4LjI5IDE1Ljk4NyA5LjM2IDE0Ljg2IDkuMzYgMTQuODZjLjUzLjM1MyAxLjE2Ny41MzMgMS44MzQuNDY4bC4wNTItLjA0NGEyLjAxIDIuMDEgMCAwIDAgLjAyMS41MThjLS43OC44NzItLjU1IDEuMDI1LTIuMTEgMS4zNDYtMS41NzguMzI1LS42NS45MDQtLjA0NiAxLjA1Ni43MzQuMTg0IDIuNDMyLjQ0NCAzLjU4LTEuMTYybC0uMDQ2LjE4M2MuMzA2LjI0NS4yODUgMS43Ni4zMyAyLjg0MnMuMTE2IDIuMDkzLjMzNyAyLjY4OC40OCAyLjEzIDIuNTMgMS43YzEuNzEzLS4zNjcgMy4wMjMtLjg5NiAzLjE0My01LjgxIi8+PHBhdGggc3Ryb2tlPSJub25lIiBmaWxsPSIjMzM2NzkxIiBkPSJNMjMuNTM1IDE1LjZjLTIuODkuNTk2LTMuMS0uMzgzLTMuMS0uMzgzIDMuMDUzLTQuNTMgNC4zMy0xMC4yOCAzLjIyOC0xMS42ODctMy4wMDQtMy44NC04LjIwNS0yLjAyMy04LjI5Mi0xLjk3NmwtLjAyOC4wMDVhMTAuMzEgMTAuMzEgMCAwIDAtMS45MjktLjIwMWMtMS4zMDgtLjAyLTIuMy4zNDMtMy4wNTQuOTE0IDAgMC05LjI3OC0zLjgyMi04Ljg0NiA0LjgwNy4wOTIgMS44MzYgMi42MyAxMy45IDUuNjYgMTAuMjVDOC4yOSAxNS45ODcgOS4zNiAxNC44NiA5LjM2IDE0Ljg2Yy41My4zNTMgMS4xNjcuNTMzIDEuODM0LjQ2OGwuMDUyLS4wNDRhMi4wMiAyLjAyIDAgMCAwIC4wMjEuNTE4Yy0uNzguODcyLS41NSAxLjAyNS0yLjExIDEuMzQ2LTEuNTc4LjMyNS0uNjUuOTA0LS4wNDYgMS4wNTYuNzM0LjE4NCAyLjQzMi40NDQgMy41OC0xLjE2MmwtLjA0Ni4xODNjLjMwNi4yNDUuNTIgMS41OTMuNDg0IDIuODE1cy0uMDYgMi4wNi4xOCAyLjcxNi40OCAyLjEzIDIuNTMgMS43YzEuNzEzLS4zNjcgMi42LTEuMzIgMi43MjUtMi45MDYuMDg4LTEuMTI4LjI4Ni0uOTYyLjMtMS45N2wuMTYtLjQ3OGMuMTgzLTEuNTMuMDMtMi4wMjMgMS4wODUtMS43OTNsLjI1Ny4wMjNjLjc3Ny4wMzUgMS43OTQtLjEyNSAyLjM5LS40MDIgMS4yODUtLjU5NiAyLjA0Ny0xLjU5Mi43OC0xLjMzeiIvPjxnIGNsYXNzPSJFIj48ZyBjbGFzcz0iQiI+PHBhdGggY2xhc3M9IkMiIGQ9Ik0xMi44MTQgMTYuNDY3Yy0uMDggMi44NDYuMDIgNS43MTIuMjk4IDYuNHMuODc1IDIuMDUgMi45MjYgMS42MTJjMS43MTMtLjM2NyAyLjMzNy0xLjA3OCAyLjYwNy0yLjY0N2wuNjMzLTUuMDE3TTEwLjM1NiAyLjJTMS4wNzItMS41OTYgMS41MDQgNy4wMzNjLjA5MiAxLjgzNiAyLjYzIDEzLjkgNS42NiAxMC4yNUM4LjI3IDE1Ljk1IDkuMjcgMTQuOTA3IDkuMjcgMTQuOTA3bTYuMS0xMy40Yy0uMzIuMSA1LjE2NC0yLjAwNSA4LjI4MiAxLjk3OCAxLjEgMS40MDctLjE3NSA3LjE1Ny0zLjIyOCAxMS42ODciLz48cGF0aCBzdHJva2UtbGluZWpvaW49ImJldmVsIiBkPSJNMjAuNDI1IDE1LjE3cy4yLjk4IDMuMS4zODJjMS4yNjctLjI2Mi41MDQuNzM0LS43OCAxLjMzLTEuMDU0LjQ5LTMuNDE4LjYxNS0zLjQ1Ny0uMDYtLjEtMS43NDUgMS4yNDQtMS4yMTUgMS4xNDctMS42NTItLjA4OC0uMzk0LS42OS0uNzgtMS4wODYtMS43NDQtLjM0Ny0uODQtNC43Ni03LjI5IDEuMjI0LTYuMzMzLjIyLS4wNDUtMS41Ni01LjctNy4xNi01Ljc4MlM3Ljk5IDguMTk2IDcuOTkgOC4xOTYiLz48L2c+PGcgY2xhc3M9IkMiPjxwYXRoIGQ9Ik0xMS4yNDcgMTUuNzY4Yy0uNzguODcyLS41NSAxLjAyNS0yLjExIDEuMzQ2LTEuNTc4LjMyNS0uNjUuOTA0LS4wNDYgMS4wNTYuNzM0LjE4NCAyLjQzMi40NDQgMy41OC0xLjE2My4zNS0uNDktLjAwMi0xLjI3LS40ODItMS40NjgtLjIzMi0uMDk2LS41NDItLjIxNi0uOTQuMjN6Ii8+PHBhdGggY2xhc3M9IkIiIGQ9Ik0xMS4xOTYgMTUuNzUzYy0uMDgtLjUxMy4xNjgtMS4xMjIuNDMzLTEuODM2LjM5OC0xLjA3IDEuMzE2LTIuMTQuNTgyLTUuNTM3LS41NDctMi41My00LjIyLS41MjctNC4yMi0uMTg0cy4xNjYgMS43NC0uMDYgMy4zNjVjLS4yOTcgMi4xMjIgMS4zNSAzLjkxNiAzLjI0NiAzLjczMyIvPjwvZz48L2c+PGcgY2xhc3M9IkQiIGZpbGw9IiNmZmYiPjxwYXRoIHN0cm9rZS13aWR0aD0iLjIzOSIgZD0iTTEwLjMyMiA4LjE0NWMtLjAxNy4xMTcuMjE1LjQzLjUxNi40NzJzLjU1OC0uMjAyLjU3NS0uMzItLjIxNS0uMjQ2LS41MTYtLjI4OC0uNTYuMDItLjU3NS4xMzZ6Ii8+PHBhdGggc3Ryb2tlLXdpZHRoPSIuMTE5IiBkPSJNMTkuNDg2IDcuOTA2Yy4wMTYuMTE3LS4yMTUuNDMtLjUxNi40NzJzLS41Ni0uMjAyLS41NzUtLjMyLjIxNS0uMjQ2LjUxNi0uMjg4LjU2LjAyLjU3NS4xMzZ6Ii8+PC9nPjxwYXRoIGNsYXNzPSJCIEMgRSIgZD0iTTIwLjU2MiA3LjA5NWMuMDUuOTItLjE5OCAxLjU0NS0uMjMgMi41MjQtLjA0NiAxLjQyMi42NzggMy4wNS0uNDEzIDQuNjgiLz48L2c+PC9zdmc+;fontSize=10;fontStyle=1;align=center;"

<!-- Redis Cache Snapcraft Icon -->
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://dashboard.snapcraft.io/site_media/appmedia/2020/08/1529926.png;fontSize=10;fontStyle=1;align=center;strokeWidth=1;fillColor=none;"

<!-- Kong API Gateway Icon (Embedded Vector SVG - 100% Offline & Reliable) -->
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNTMgMTM3IiB3aWR0aD0iNjQiIGhlaWdodD0iNjQiPgogIDxwYXRoIGZpbGw9IiMwMDJBM0EiIGQ9Ik01MC41LDExMi45bC0zLjcsNC43LDguNCwxMy4yLS45LDYuMWgzNS42bDIuNS02LjEtMTQuMy0xNy45aC0yNy42WiIvPgogIDxwYXRoIGZpbGw9IiMwMDdBQzIiIGQ9Ik02OS45LDMyLjZsLTEyLjksMjIuNyw2Mi45LDc0LjgtMS44LDYuOWgyOC44bDUuMi0yNC4zTDg0LjksMzIuNWgtMTVaIi8+CiAgPHBhdGggZmlsbD0iIzEyNjRBMyIgZD0iTTc4LjUsMTUuNWwtNi4xLDExLjNoMTUuMmwyNi4xLDMxLjIsMTUuNS0xMi44di04LjFsLTUuNC03LjYsNC00LjJMOTYuNy42bC0xOC4yLDE0LjlaIi8+CiAgPHBhdGggZmlsbD0iIzAwM0I1QyIgZD0iTTMxLjcsNzguN2gtOC41TC44LDEwNy4zdjI5LjZoMjRsNC4yLTUuNSwxOC41LTI0LjFoMjYuOGw4LjMtMTIuNy0yOS4xLTM0LjctMjEuOSwxOC45WiIvPgo8L3N2Zz4=;fontSize=10;fontStyle=1;align=center;"

<!-- Kafka Event Broker Icon -->
style="shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://www.svgrepo.com/show/353951/kafka-icon.svg;fontSize=10;fontStyle=1;align=center;"
```

### Official STD Lifecycle Connectors (Mandatory Arc Jumps & Colors)
Connections must declare exact stroke colors corresponding to the lifecycle state in the STD palette tab:

```xml
<!-- 1. New Connection (#03CCFF) -->
<!-- Sync -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#03CCFF;strokeWidth=2;endArrow=classic;"
<!-- Async (Animated) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#03CCFF;strokeWidth=2;endArrow=classic;"

<!-- 2. Enhanced Connection (#92D14F) -->
<!-- Sync -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#92D14F;strokeWidth=2;endArrow=classic;"
<!-- Async (Animated) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#92D14F;strokeWidth=2;endArrow=classic;"

<!-- 3. Existing / Reused Connection (#BFBFBF) -->
<!-- Sync -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#BFBFBF;strokeWidth=2;endArrow=classic;"
<!-- Async (Animated) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#BFBFBF;strokeWidth=2;endArrow=classic;"

<!-- 4. External Connection (#EF7D30) -->
<!-- Sync -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#EF7D30;strokeWidth=2;endArrow=classic;"
<!-- Async (Animated) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#EF7D30;strokeWidth=2;endArrow=classic;"

<!-- 5. Kafka Event Bus Connection (#FF6A00) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#FF6A00;strokeWidth=2;endArrow=classic;"
```


---

## 🛠️ Portable Automation Scripts (Common Tooling Only)
The skill directory (`drawio-hla-architect/`) contains **ONLY common, generic, and reusable architecture tooling**:
* Specific domain generators (such as one-off campaign, lending, or e-commerce scripts) belong **outside the skill directory** (e.g. in `examples/` or repository root).
* This keeps `drawio-hla-architect/` 100% clean, modular, and instantly transferable to any other project or repository.

The two core common scripts in `./scripts/` are:

### 1. Diagram Generator Blueprint: `scripts/generate_hla_template.py`
Generates a complete 2-page Draw.io diagram file (`.drawio`). Uses dynamic relative path discovery to resolve `./resources/standard_icons_tab.xml` without any machine-specific dependencies. 

> [!TIP]
> **Output Standard (.drawio, No .xml suffix):**
> * All generated HLA diagram files MUST be saved with the `.drawio` extension (e.g. `ecommerce_smart_fulfillment_hla.drawio`, NOT `.drawio.xml` or `.xml`).
> * Diagram files are saved to the **repository root** (outside `drawio-hla-architect/`).

```bash
python3 scripts/generate_hla_template.py
```

### 2. Automated Standards & QA Auditor: `scripts/qa_verify_hla.py`
Audits any `.drawio` diagram file against all enterprise invariants and outputs a comprehensive compliance audit:

```bash
# Standard Audit
python3 scripts/qa_verify_hla.py <path_to_diagram.drawio>

# Strict CI/CD Mode
python3 scripts/qa_verify_hla.py <path_to_diagram.drawio> --strict
```

---

## 📋 Pre-Flight Architecture Sign-Off Checklist

Before delivering any `.drawio` diagram to project stakeholders, verify:

- [ ] **Clean `.drawio` Extension:** File is saved strictly as `<name>.drawio` without `.xml` suffix.
- [ ] **Multi-Page File:** XML root is `<mxfile pages="2">` and contains both the HLA diagram and the standard palette tab (`id="ao9VHCrxs2CTfegMv53f"` or `STD`).
- [ ] **Dedicated Swimlanes:** Gateway, Channel BFF, Orchestrator, Domain Core, and Adaptor each reside in their own column. No tiers merged.
- [ ] **Geometry Clearance & No Overlap:**
  - Outer grouping box starts at `y = 25`, child swimlanes at `y = 80` (55px header clearance).
  - All microservices, pods, and database icons start at `y >= 120` (minimum 40px clearance below swimlane header).
  - Horizontal margin $\ge 25\text{px}$ before adjacent external lanes.
  - Pods/databases do not overlap each other ($\ge 40\text{px}$ horizontal, $\ge 50\text{px}$ vertical).
- [ ] **STD Connection Stroke Colors:**
  - New = `#03CCFF` (strokeWidth=2)
  - Enhanced = `#92D14F` (strokeWidth=2)
  - Existing = `#BFBFBF` (strokeWidth=2)
  - External = `#EF7D30` (strokeWidth=2)
  - Kafka = `#FF6A00` (strokeWidth=2, dashed=1, flowAnimation=1)
- [ ] **Topological Anchoring:** Every edge declares `source="id"` and `target="id"`. No unanchored floating arrows.
- [ ] **Zero Orphans:** Every microservice has at least one inbound trigger and one outbound action/downstream call.
- [ ] **Callback Completeness:** `orch-*-callback` receives external webhook via Top Corridor (Y < 120px) and calls `core-*`.
- [ ] **Step Sequence Labels:** Edges contain step numbers and HTTP verbs/paths: `1 - POST /v1/... (NEW)`.
- [ ] **HTML Safety:** All multiline image icons and cylinders have `html=1;whiteSpace=wrap;` in their style.
- [ ] **Arc Jumps:** All crossing lines declare `jumpStyle=arc;jumpSize=6;`.
- [ ] **Kafka Topics:** Topic names match standard convention with animated dashed lines.
- [ ] **Automated QA Passed:** Ran `python3 scripts/qa_verify_hla.py <file>.drawio --strict` and received `STATUS: PASSED (0 errors)`.
