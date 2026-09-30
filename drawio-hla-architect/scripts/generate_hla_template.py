#!/usr/bin/env python3
"""
Universal Enterprise Draw.io HLA Diagram Generator & Blueprint
Generates production-grade, 2-page Draw.io architecture diagrams (.drawio)
following enterprise solution architecture standards across ANY domain
(Fintech, Banking, Retail, E-Commerce, Logistics, Healthcare, Telecom, etc.).

Features:
- Common, domain-agnostic 7-Swimlane spatial architecture
- Optional configurable System/Platform bounding container with anti-overlap clearance
- Official Kubernetes Pod lifecycle styling (New, Enhanced, Reused, External)
- Vector DB icons (PostgreSQL SVG, Redis, Kafka, Kong) with mandatory html=1; escaping
- Arc-jump planar edge routing (zero middle cuts, top/bottom bypass corridors)
- Sequenced API flow labeling (HTTP method + path + step numbering)
- STD lifecycle connection colors (#03CCFF, #92D14F, #BFBFBF, #EF7D30, #FF6A00)
"""

import os
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Dynamic Path Resolution (Portable across any machine / folder)
# ---------------------------------------------------------------------------
def resolve_standard_tab_xml():
    """Dynamically locates standard_icons_tab.xml without hardcoded absolute paths."""
    search_dirs = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources"),
        os.path.join(os.getcwd(), "drawio-hla-architect", "resources"),
        os.path.join(os.getcwd(), "resources"),
    ]
    for d in search_dirs:
        candidate = os.path.join(d, "standard_icons_tab.xml")
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                return f.read().strip()
    return ""

def esc(val):
    """Encodes strings safely for Draw.io XML attributes, transforming newlines to <br>."""
    if not val:
        return ""
    val = val.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')
    val = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', val)
    val = val.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    return val

# ---------------------------------------------------------------------------
# Standard Enterprise XML Styles
# ---------------------------------------------------------------------------
POD_POINTS = "points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];"

STYLES = {
    # Kubernetes Pods (Microservices)
    "pod_new": f"sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#dae8fc;strokeColor=#03CCFF;strokeWidth=2;{POD_POINTS}verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;",
    "pod_enhanced": f"sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#d5e8d4;strokeColor=#92D14F;strokeWidth=2;{POD_POINTS}verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;",
    "pod_existing": f"sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#f5f5f5;strokeColor=#BFBFBF;strokeWidth=1.5;{POD_POINTS}verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;",
    "pod_external": f"sketch=0;html=1;dashed=0;whitespace=wrap;fillColor=#ffe6cc;strokeColor=#EF7D30;strokeWidth=1.5;{POD_POINTS}verticalLabelPosition=bottom;align=center;verticalAlign=top;shape=mxgraph.kubernetes.icon;prIcon=pod;fontSize=10;fontStyle=1;fontColor=#000000;",

    # External System Boxes
    "ext_box": "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#EF7D30;strokeWidth=1.5;fontStyle=1;fontSize=11;align=center;",

    # Standard Infrastructure & Middleware Icons (html=1 strictly required)
    "icon_kong": "shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://seeklogo.com/images/K/kong-logo-30290787E5-seeklogo.com.png;fontSize=10;fontStyle=1;align=center;",
    "icon_kafka": "shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://www.svgrepo.com/show/353951/kafka-icon.svg;fontSize=10;fontStyle=1;align=center;",
    "icon_redis": "shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=https://dashboard.snapcraft.io/site_media/appmedia/2020/08/1529926.png;fontSize=10;fontStyle=1;align=center;strokeWidth=1;fillColor=none;",
    "icon_postgres": "shape=image;html=1;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;whiteSpace=wrap;image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NCIgdmlld0JveD0iMCAwIDI1LjYgMjUuNiIgaGVpZ2h0PSI2NCI+PHN0eWxlPi5Ce3N0cm9rZS1saW5lY2FwOnJvdW5kfS5De3N0cm9rZS1saW5lam9pbjpyb3VuZH0uRHtzdHJva2UtbGluZWpvaW46bWl0ZXJ9LkV7c3Ryb2tlLXdpZHRoOi43MTZ9PC9zdHlsZT48ZyBzdHJva2U9IiNmZmYiIGZpbGw9Im5vbmUiPjxwYXRoIGNsYXNzPSJEIiBzdHJva2Utd2lkdGg9IjIuMTQ5IiBzdHJva2UtbGluZWNhcD0iYnV0dCIgc3Ryb2tlPSIjMDAwIiBmaWxsPSIjMDAwIiBkPSJNMTguOTgzIDE4LjYzNmMuMTYzLTEuMzU3LjExNC0xLjU1NSAxLjEyNC0xLjMzNmwuMjU3LjAyM2MuNzc3LjAzNSAxLjc5My0uMTI1IDIuNC0uNDAyIDEuMjg1LS41OTYgMi4wNDctMS41OTIuNzgtMS4zMy0yLjg5LjU5Ni0zLjEtLjM4My0zLjEtLjM4MyAzLjA1My00LjUzIDQuMzMtMTAuMjggMy4yMjctMTEuNjg3LTMuMDA0LTMuODQtOC4yMDUtMi4wMjQtOC4yOTItMS45NzVsLS4wMjguMDA1Yy0uNTctLjEyLTEuMi0uMTktMS45My0uMi0xLjMwOC0uMDItMi4zLjM0My0zLjA1NC45MTQgMCAwLTkuMjc3LTMuODIyLTguODQ2IDQuODA3LjA5MiAxLjgzNiAyLjYzIDEzLjkgNS42NiAxMC4yNUM4LjI5IDE1Ljk4NyA5LjM2IDE0Ljg2IDkuMzYgMTQuODZjLjUzLjM1MyAxLjE2Ny41MzMgMS44MzQuNDY4bC4wNTItLjA0NGEyLjAxIDIuMDEgMCAwIDAgLjAyMS41MThjLS43OC44NzItLjU1IDEuMDI1LTIuMTEgMS4zNDYtMS41NzguMzI1LS42NS45MDQtLjA0NiAxLjA1Ni43MzQuMTg0IDIuNDMyLjQ0NCAzLjU4LTEuMTYybC0uMDQ2LjE4M2MuMzA2LjI0NS4yODUgMS43Ni4zMyAyLjg0MnMuMTE2IDIuMDkzLjMzNyAyLjY4OC40OCAyLjEzIDIuNTMgMS43YzEuNzEzLS4zNjcgMy4wMjMtLjg5NiAzLjE0My01LjgxIi8+PHBhdGggc3Ryb2tlPSJub25lIiBmaWxsPSIjMzM2NzkxIiBkPSJNMjMuNTM1IDE1LjZjLTIuODkuNTk2LTMuMS0uMzgzLTMuMS0uMzgzIDMuMDUzLTQuNTMgNC4zMy0xMC4yOCAzLjIyOC0xMS42ODctMy4wMDQtMy44NC04LjIwNS0yLjAyMy04LjI5Mi0xLjk3NmwtLjAyOC4wMDVhMTAuMzEgMTAuMzEgMCAwIDAtMS45MjktLjIwMWMtMS4zMDgtLjAyLTIuMy4zNDMtMy4wNTQuOTE0IDAgMC05LjI3OC0zLjgyMi04Ljg0NiA0LjgwNy4wOTIgMS44MzYgMi42MyAxMy45IDUuNjYgMTAuMjVDOC4yOSAxNS45ODcgOS4zNiAxNC44NiA5LjM2IDE0Ljg2Yy41My4zNTMgMS4xNjcuNTMzIDEuODM0LjQ2OGwuMDUyLS4wNDRhMi4wMiAyLjAyIDAgMCAwIC4wMjEuNTE4Yy0uNzguODcyLS41NSAxLjAyNS0yLjExIDEuMzQ2LTEuNTc4LjMyNS0uNjUuOTA0LS4wNDYgMS4wNTYuNzM0LjE4NCAyLjQzMi40NDQgMy41OC0xLjE2MmwtLjA0Ni4xODNjLjMwNi4yNDUuNTIgMS41OTMuNDg0IDIuODE1cy0uMDYgMi4wNi4xOCAyLjcxNi40OCAyLjEzIDIuNTMgMS43YzEuNzEzLS4zNjcgMi42LTEuMzIgMi43MjUtMi45MDYuMDg4LTEuMTI4LjI4Ni0uOTYyLjMtMS45N2wuMTYtLjQ3OGMuMTgzLTEuNTMuMDMtMi4wMjMgMS4wODUtMS43OTNsLjI1Ny4wMjNjLjc3Ny4wMzUgMS43OTQtLjEyNSAyLjM5LS40MDIgMS4yODUtLjU5NiAyLjA0Ny0xLjU5Mi43OC0xLjMzeiIvPjxnIGNsYXNzPSJFIj48ZyBjbGFzcz0iQiI+PHBhdGggY2xhc3M9IkMiIGQ9Ik0xMi44MTQgMTYuNDY3Yy0uMDggMi44NDYuMDIgNS43MTIuMjk4IDYuNHMuODc1IDIuMDUgMi45MjYgMS42MTJjMS43MTMtLjM2NyAyLjMzNy0xLjA3OCAyLjYwNy0yLjY0N2wuNjMzLTUuMDE3TTEwLjM1NiAyLjJTMS4wNzItMS41OTYgMS41MDQgNy4wMzNjLjA5MiAxLjgzNiAyLjYzIDEzLjkgNS42NiAxMC4yNUM4LjI3IDE1Ljk1IDkuMjcgMTQuOTA3IDkuMjcgMTQuOTA3bTYuMS0xMy40Yy0uMzIuMSA1LjE2NC0yLjAwNSA4LjI4MiAxLjk3OCAxLjEgMS40MDctLjE3NSA3LjE1Ny0zLjIyOCAxMS42ODciLz48cGF0aCBzdHJva2UtbGluZWpvaW49ImJldmVsIiBkPSJNMjAuNDI1IDE1LjE3cy4yLjk4IDMuMS4zODJjMS4yNjctLjI2Mi41MDQuNzM0LS43OCAxLjMzLTEuMDU0LjQ5LTMuNDE4LjYxNS0zLjQ1Ny0uMDYtLjEtMS43NDUgMS4yNDQtMS4yMTUgMS4xNDctMS42NTItLjA4OC0uMzk0LS42OS0uNzgtMS4wODYtMS43NDQtLjM0Ny0uODQtNC43Ni03LjI5IDEuMjI0LTYuMzMzLjIyLS4wNDUtMS41Ni01LjctNy4xNi01Ljc4MlM3Ljk5IDguMTk2IDcuOTkgOC4xOTYiLz48L2c+PGcgY2xhc3M9IkMiPjxwYXRoIGQ9Ik0xMS4yNDcgMTUuNzY4Yy0uNzguODcyLS41NSAxLjAyNS0yLjExIDEuMzQ2LTEuNTc4LjMyNS0uNjUuOTA0LS4wNDYgMS4wNTYuNzM0LjE4NCAyLjQzMi40NDQgMy41OC0xLjE2My4zNS0uNDktLjAwMi0xLjI3LS40ODItMS40NjgtLjIzMi0uMDk2LS41NDItLjIxNi0uOTQuMjN6Ii8+PHBhdGggY2xhc3M9IkIiIGQ9Ik0xMS4xOTYgMTUuNzUzYy0uMDgtLjUxMy4xNjgtMS4xMjIuNDMzLTEuODM2LjM5OC0xLjA3IDEuMzE2LTIuMTQuNTgyLTUuNTM3LS41NDctMi41My00LjIyLS41MjctNC4yMi0uMTg0cy4xNjYgMS43NC0uMDYgMy4zNjVjLS4yOTcgMi4xMjIgMS4zNSAzLjkxNiAzLjI0NiAzLjczMyIvPjwvZz48L2c+PGcgY2xhc3M9IkQiIGZpbGw9IiNmZmYiPjxwYXRoIHN0cm9rZS13aWR0aD0iLjIzOSIgZD0iTTEwLjMyMiA4LjE0NWMtLjAxNy4xMTcuMjE1LjQzLjUxNi40NzJzLjU1OC0uMjAyLjU3NS0uMzItLjIxNS0uMjQ2LS41MTYtLjI4OC0uNTYuMDItLjU3NS4xMzZ6Ii8+PHBhdGggc3Ryb2tlLXdpZHRoPSIuMTE5IiBkPSJNMTkuNDg2IDcuOTA2Yy4wMTYuMTE3LS4yMTUuNDMtLjUxNi40NzJzLS41Ni0uMjAyLS41NzUtLjMyLjIxNS0uMjQ2LjUxNi0uMjg4LjU2LjAyLjU3NS4xMzZ6Ii8+PC9nPjxwYXRoIGNsYXNzPSJCIEMgRSIgZD0iTTIwLjU2MiA3LjA5NWMuMDUuOTItLjE5OCAxLjU0NS0uMjMgMi41MjQtLjA0NiAxLjQyMi42NzggMy4wNS0uNDEzIDQuNjgiLz48L2c+PC9zdmc+;fontSize=10;fontStyle=1;align=center;",

    # Database Cylinders (Alternative style)
    "db_new": "shape=cylinder3;html=1;boundedLbl=1;backgroundOutline=1;size=6.5;fillColor=#03CCFF;strokeColor=#000000;fontSize=10;fontStyle=1;align=center;",
    "db_enhanced": "shape=cylinder3;html=1;boundedLbl=1;backgroundOutline=1;size=6.5;fillColor=#92D14F;strokeColor=#000000;fontSize=10;fontStyle=1;align=center;",
    "db_existing": "shape=cylinder3;html=1;boundedLbl=1;backgroundOutline=1;size=6.5;fillColor=#BFBFBF;strokeColor=#000000;fontSize=10;fontStyle=1;align=center;",

    # Callout / Note Boxes
    "note_tbc": "rounded=0;whiteSpace=wrap;html=1;fillColor=#fad7ac;strokeColor=#b46504;fontSize=9.5;fontStyle=0;align=left;spacing=4;",
    "note_cache_schema": "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d6b656;strokeWidth=1;fontSize=9;align=left;spacing=4;fontFamily=Courier New;",

    # Official STD Lifecycle Connection Styles (with mandatory arc jumps)
    # 1. New Connection (#03CCFF)
    "conn_new_sync": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#03CCFF;strokeWidth=2;endArrow=classic;",
    "conn_new_async": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#03CCFF;strokeWidth=2;endArrow=classic;",

    # 2. Enhanced Connection (#92D14F)
    "conn_enhanced_sync": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#92D14F;strokeWidth=2;endArrow=classic;",
    "conn_enhanced_async": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#92D14F;strokeWidth=2;endArrow=classic;",

    # 3. Existing / Reused Connection (#BFBFBF)
    "conn_existing_sync": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#BFBFBF;strokeWidth=2;endArrow=classic;",
    "conn_existing_async": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#BFBFBF;strokeWidth=2;endArrow=classic;",

    # 4. External Connection (#EF7D30)
    "conn_external_sync": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;strokeColor=#EF7D30;strokeWidth=2;endArrow=classic;",
    "conn_external_async": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#EF7D30;strokeWidth=2;endArrow=classic;",

    # 5. Kafka Event Bus Connection (#FF6A00)
    "conn_kafka": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;jumpSize=6;html=1;dashed=1;flowAnimation=1;strokeColor=#FF6A00;strokeWidth=2;endArrow=classic;",

    "edge_label": "edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=9;fontStyle=1;"
}

# ---------------------------------------------------------------------------
# Architecture Blueprint Builder
# ---------------------------------------------------------------------------
class HLADiagramBuilder:
    def __init__(self, title="System High-Level Architecture", page_width=2800, page_height=1080):
        self.title = title
        self.page_width = page_width
        self.page_height = page_height
        self.cells = []
        self.cell_id_counter = 100

    def next_id(self, prefix="c"):
        self.cell_id_counter += 1
        return f"{prefix}_{self.cell_id_counter}"

    def add_swimlane(self, lane_id, title, x, y, width, height, fill_color="#f8f9fa", stroke_color="#4a5568"):
        style = f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={stroke_color};strokeWidth=1.2;verticalAlign=top;fontStyle=1;fontSize=12;align=center;spacingTop=10;opacity=60;"
        cell = f'<mxCell id="{lane_id}" parent="1" style="{style}" value="{esc(title)}" vertex="1">\n'
        cell += f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />\n'
        cell += '</mxCell>'
        self.cells.append(cell)
        return lane_id

    def add_system_container(self, container_id, title, x=485, y=25, width=1305, height=920, fill_color="#f8fafc", stroke_color="#94a3b8"):
        """
        Creates an optional top-level system bounding container enclosing internal microservice tiers.
        Guarantees 55px top clearance before child swimlanes at y=80.
        Can be used for ANY domain (e.g. Retail Core, Banking Platform, Logistics Engine, etc.).
        """
        style = f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={stroke_color};strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=13;align=center;spacingTop=12;opacity=40;"
        cell = f'<mxCell id="{container_id}" parent="1" style="{style}" value="{esc(title)}" vertex="1">\n'
        cell += f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />\n'
        cell += '</mxCell>'
        self.cells.append(cell)
        return container_id

    def create_standard_7_lanes(self, system_container_title=None,
                                client_title="Client & Inbound Rails",
                                gateway_title="Gateway Layer (API Gateway)",
                                bff_title="Channel BFF Layer (bff-*)",
                                orch_title="Orchestration Layer (orch-*)",
                                core_title="Domain Core Layer (core-*)",
                                adaptor_title="Adaptor Layer (adaptor-*)",
                                external_title="Enterprise Platforms & External Rails",
                                y=80, height=870):
        """
        Common Enterprise 7-Swimlane Scaffold.
        Applies mathematical non-overlapping coordinates and clearance to any enterprise system.
        """
        if system_container_title:
            self.add_system_container(
                "box_system_platform",
                system_container_title,
                x=490, y=25, width=1295, height=height + 55,
                fill_color="#f8fafc", stroke_color="#94a3b8"
            )

        self.add_swimlane("lane_client", client_title, 40, y, 240, height, fill_color="#f8f9fa", stroke_color="#4a5568")
        self.add_swimlane("lane_gw", gateway_title, 295, y, 180, height, fill_color="#edf2f7", stroke_color="#4a5568")
        self.add_swimlane("lane_bff", bff_title, 505, y, 220, height, fill_color="#dae8fc", stroke_color="#6c8ebf")
        self.add_swimlane("lane_orch", orch_title, 740, y, 260, height, fill_color="#ffe6cc", stroke_color="#d79b00")
        self.add_swimlane("lane_core", core_title, 1015, y, 485, height, fill_color="#fff2cc", stroke_color="#d6b656")
        self.add_swimlane("lane_adapt", adaptor_title, 1515, y, 260, height, fill_color="#e1d5e7", stroke_color="#9673a6")
        self.add_swimlane("lane_ext", external_title, 1820, y, 520, height, fill_color="#f5f5f5", stroke_color="#b0b0b0")

    def add_pod(self, pod_id, name, lifecycle_type, x, y, width=44, height=44):
        style_key = f"pod_{lifecycle_type.lower()}"
        style = STYLES.get(style_key, STYLES["pod_new"])
        cell = f'<mxCell id="{pod_id}" parent="1" style="{style}" value="{esc(name)}" vertex="1">\n'
        cell += f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />\n'
        cell += '</mxCell>'
        self.cells.append(cell)
        return pod_id

    def add_icon(self, icon_id, label, icon_type, x, y, width=45, height=45):
        style_key = f"icon_{icon_type.lower()}"
        style = STYLES.get(style_key, STYLES["icon_kong"])
        cell = f'<mxCell id="{icon_id}" parent="1" style="{style}" value="{esc(label)}" vertex="1">\n'
        cell += f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />\n'
        cell += '</mxCell>'
        self.cells.append(cell)
        return icon_id

    def add_database(self, db_id, label, db_type, lifecycle, x, y, width=45, height=52):
        if db_type.lower() == "postgres":
            return self.add_icon(db_id, label, "postgres", x, y, width=44, height=44)
        elif db_type.lower() == "redis":
            return self.add_icon(db_id, label, "redis", x, y, width=44, height=44)
        else:
            style_key = f"db_{lifecycle.lower()}"
            style = STYLES.get(style_key, STYLES["db_new"])
            cell = f'<mxCell id="{db_id}" parent="1" style="{style}" value="{esc(label)}" vertex="1">\n'
            cell += f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />\n'
            cell += '</mxCell>'
            self.cells.append(cell)
            return db_id

    def add_note(self, note_id, text, note_type, x, y, width=160, height=50):
        style = STYLES["note_tbc"] if note_type == "tbc" else STYLES["note_cache_schema"]
        cell = f'<mxCell id="{note_id}" parent="1" style="{style}" value="{esc(text)}" vertex="1">\n'
        cell += f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />\n'
        cell += '</mxCell>'
        self.cells.append(cell)
        return note_id

    def add_connection(self, edge_id, source_id, target_id, label="", conn_type="new_sync", waypoints=None):
        ct = conn_type.lower()
        if ct in ["sync", "new", "new_sync"]:
            style_key = "conn_new_sync"
        elif ct in ["enhanced", "enhanced_sync"]:
            style_key = "conn_enhanced_sync"
        elif ct in ["existing", "existing_sync", "reused"]:
            style_key = "conn_existing_sync"
        elif ct in ["external", "external_sync", "3rd_party"]:
            style_key = "conn_external_sync"
        elif ct in ["new_async"]:
            style_key = "conn_new_async"
        elif ct in ["enhanced_async"]:
            style_key = "conn_enhanced_async"
        elif ct in ["existing_async"]:
            style_key = "conn_existing_async"
        elif ct in ["async", "external_async"]:
            style_key = "conn_external_async"
        elif ct in ["kafka", "event"]:
            style_key = "conn_kafka"
        else:
            style_key = f"conn_{ct}" if f"conn_{ct}" in STYLES else "conn_new_sync"

        style = STYLES.get(style_key, STYLES["conn_new_sync"])
        cell = f'<mxCell id="{edge_id}" edge="1" parent="1" source="{source_id}" target="{target_id}" style="{style}" value="{esc(label)}">\n'
        cell += '  <mxGeometry relative="1" as="geometry">\n'
        if waypoints:
            cell += '    <Array as="points">\n'
            for wx, wy in waypoints:
                cell += f'      <mxPoint x="{wx}" y="{wy}" />\n'
            cell += '    </Array>\n'
        cell += '  </mxGeometry>\n'
        cell += '</mxCell>'
        self.cells.append(cell)
        return edge_id


    def build_page_1_xml(self):
        cells_xml = "\n".join(self.cells)
        return f"""  <diagram name="HLA Overview" id="HLA_Overview">
    <mxGraphModel dx="3000" dy="1800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.page_width}" pageHeight="{self.page_height}" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{cells_xml}
      </root>
    </mxGraphModel>
  </diagram>"""

    def export_drawio(self, output_path):
        if output_path.endswith(".drawio.xml"):
            output_path = output_path[:-4]  # Remove trailing .xml to enforce .drawio

        page_1 = self.build_page_1_xml()
        page_2 = resolve_standard_tab_xml()
        if not page_2:
            print("⚠️ Warning: Could not locate standard_icons_tab.xml. Page 2 may be empty.")

        full_xml = f"""<mxfile host="app.diagrams.net" pages="2">
{page_1}
{page_2}
</mxfile>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_xml)

        ET.parse(output_path)
        print(f"✅ Generated 2-Page Draw.io HLA Diagram: {output_path}")

    def export_drawio_xml(self, output_path):
        return self.export_drawio(output_path)

# ---------------------------------------------------------------------------
# Example Demonstration
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    builder = HLADiagramBuilder("CLICX Enterprise Onboarding HLA")

    # 1. Add Dedicated Swimlanes (All start at y=80, with explicit non-overlapping horizontal spacing)
    builder.add_swimlane("lane_client", "Client & Inbound Rails", 50, 80, 230, 875, fill_color="#f8f9fa", stroke_color="#4a5568")
    builder.add_swimlane("lane_gw", "Gateway Layer (Kong)", 300, 80, 165, 875, fill_color="#edf2f7", stroke_color="#4a5568")
    builder.add_swimlane("lane_bff", "Channel BFF (bff-mobile-*)", 505, 80, 215, 875, fill_color="#dae8fc", stroke_color="#6c8ebf")
    builder.add_swimlane("lane_orch", "Orchestration Layer (orch-*)", 740, 80, 260, 875, fill_color="#ffe6cc", stroke_color="#d79b00")
    builder.add_swimlane("lane_core", "Domain Core Layer (core-*)", 1020, 80, 490, 875, fill_color="#fff2cc", stroke_color="#d6b656")
    builder.add_swimlane("lane_adapt", "Adaptor Layer (adaptor-*)", 1530, 80, 250, 875, fill_color="#e1d5e7", stroke_color="#9673a6")
    builder.add_swimlane("lane_ext", "Enterprise Platforms & Core Bank", 1820, 80, 480, 875, fill_color="#f5f5f5", stroke_color="#b0b0b0")


    # 2. Add Components along functional tracks
    # Track 1: Client & Kong Gateway
    builder.add_pod("node_app", "Mobile App\n(iOS/Android)", "existing", 140, 400)
    builder.add_icon("node_kong", "Kong API Gateway\n(JWT Auth)", "kong", 375, 400)

    # Track 2: BFF & Orchestrator
    builder.add_pod("node_bff", "bff-mobile-onboard", "new", 610, 400)
    builder.add_pod("node_orch", "orch-onboard-saga", "new", 880, 400)

    # Track 3: Core & Persistence
    builder.add_pod("node_core", "core-onboard-engine", "new", 1150, 400)
    builder.add_database("node_db", "PostgreSQL\n{onboard_db}", "postgres", "new", 1270, 400)
    builder.add_database("node_redis", "Redis Cache\n{session_cache}", "redis", "new", 1400, 400)

    # Track 4: Adaptor & External Platform
    builder.add_pod("node_adapt", "adaptor-dopa", "existing", 1650, 400)
    builder.add_pod("node_dopa", "DOPA Platform", "external", 1950, 400)

    # 3. Add Edges with Step Sequence & API paths (Styled with STD Connection Types)
    builder.add_connection("e1", "node_app", "node_kong", "1 - POST /v1/onboard/start (NEW)", "new_sync")
    builder.add_connection("e2", "node_kong", "node_bff", "2 - Forward to BFF", "new_sync")
    builder.add_connection("e3", "node_bff", "node_orch", "3 - Start Onboard Saga", "new_sync")
    builder.add_connection("e4", "node_orch", "node_core", "4 - Init Customer Record", "new_sync")
    builder.add_connection("e5", "node_core", "node_db", "5 - Persist State", "new_sync")
    builder.add_connection("e6", "node_core", "node_redis", "6 - Set Idempotency Lock", "new_sync")
    builder.add_connection("e7", "node_orch", "node_adapt", "7 - Verify Citizen LaserID", "enhanced_sync")
    builder.add_connection("e8", "node_adapt", "node_dopa", "8 - Query DOPA Rails (mTLS)", "external_sync")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    output_file = os.path.join(repo_root, "sample_output_hla.drawio")
    builder.export_drawio_xml(output_file)


