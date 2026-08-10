#!/usr/bin/env python3
"""단일 chamber_params.json에서 ESS 모의 챔버 OBJ/MTL/STL을 생성한다."""

from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_PARAMS = HERE.parent / "drawings" / "chamber_params.json"
OBJ_PATH = HERE / "chamber.obj"
MTL_PATH = HERE / "chamber.mtl"
STL_PATH = HERE / "chamber.stl"

# 아래 값은 치수가 아니라 개념 마커의 상대 배치/표현 비율이다. 실제 치수는 JSON에서만 읽는다.
UPPER_SENSOR_FROM_TOP_RATIO = 0.35
UPPER_SENSOR_X_RATIOS = (0.22, 0.50, 0.78)
MID_LOWER_RATIO = 0.40
UPPER_RATIO = 0.82
CABLE_Y_RATIO = 0.30
MARKER_SIZE_RATIO = 0.025
DISPLAY_OFFSET_RATIO = 0.001
AXIS_LENGTH_RATIO = 0.16
AXIS_WIDTH_RATIO = 0.012

MATERIALS = {
    "outer_shell": (0.68, 0.70, 0.72, 0.38),
    "effective_volume": (0.50, 0.75, 0.95, 0.22),
    "floor_frame": (0.30, 0.32, 0.34, 1.00),
    "pack": (0.08, 0.30, 0.58, 1.00),
    "door": (0.95, 0.65, 0.10, 0.65),
    "window": (0.20, 0.85, 0.95, 0.55),
    "handle": (0.85, 0.45, 0.05, 1.00),
    "inlet_dependent": (0.85, 0.15, 0.15, 1.00),
    "exhaust_dependent": (0.55, 0.20, 0.75, 1.00),
    "cable_dependent": (0.20, 0.20, 0.20, 1.00),
    "sensor_concept": (0.05, 0.65, 0.35, 1.00),
    "electrical_envelope": (0.49, 0.23, 0.93, 0.45),
    "axis_x": (0.90, 0.10, 0.10, 1.00),
    "axis_y": (0.10, 0.70, 0.10, 1.00),
    "axis_z": (0.10, 0.25, 0.90, 1.00),
}


def load_params(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("meta", "pack", "clearance", "enclosure", "floor_frame", "ports", "sensor_points")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"파라미터 섹션 누락: {', '.join(missing)}")
    for section in required[1:]:
        for name, item in data[section].items():
            if not isinstance(item, dict) or not {"value", "unit", "status", "source"} <= item.keys():
                raise ValueError(f"잘못된 파라미터 레코드: {section}.{name}")
            if item["status"] not in ("fixed", "tbc", "dependent"):
                raise ValueError(f"잘못된 상태: {section}.{name}")
    for name in ("wall_thickness", "material", "sealing_grade", "door_opening_width", "door_opening_height",
                 "observation_window_width", "observation_window_height", "door_handle_length", "door_handle_offset"):
        item = data["enclosure"][name]
        assert item["value"] is not None and item["status"] == "fixed", f"확정 전제 위반: enclosure.{name}"
    item = data["floor_frame"]["height"]
    assert item["value"] is not None and item["status"] == "fixed", "확정 전제 위반: floor_frame.height"
    for name in ("common_inlet_diameter", "exhaust_diameter", "cable_entry_diameter"):
        item = data["ports"][name]
        assert item["value"] is None and item["status"] == "dependent", f"종속값 전제 위반: ports.{name}"
    return data


def number(item: dict[str, Any], name: str) -> float:
    value = item["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"숫자 값 필요: {name}")
    return float(value)


def dimensions(p: dict[str, Any]) -> dict[str, float]:
    pack, c = p["pack"], p["clearance"]
    count = number(pack["count"], "pack.count")
    assert count >= 1 and count.is_integer(), "pack.count는 1 이상의 정수여야 함"
    pw = number(pack["width"], "pack.width")
    pd = number(pack["depth"], "pack.depth")
    ph = number(pack["height"], "pack.height")
    values = {
        "pack_w": pw, "pack_d": pd, "pack_h": ph, "count": count,
        "left": number(c["side_left"], "clearance.side_left"),
        "right": number(c["side_right"], "clearance.side_right"),
        "front": number(c["front"], "clearance.front"),
        "rear": number(c["rear"], "clearance.rear"),
        "top": number(c["top"], "clearance.top"),
        "bottom": number(c["bottom"], "clearance.bottom"),
    }
    values["stack_h"] = ph * count
    values["w"] = pw + values["left"] + values["right"]
    values["d"] = pd + values["front"] + values["rear"]
    values["h"] = values["stack_h"] + values["bottom"] + values["top"]
    values["wall"] = number(p["enclosure"]["wall_thickness"], "enclosure.wall_thickness")
    values["frame_h"] = number(p["floor_frame"]["height"], "floor_frame.height")
    assert math.isclose(values["frame_h"], values["bottom"]), "floor_frame.height must equal clearance.bottom"
    return values


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]] = field(default_factory=list)
    faces: list[tuple[str, str, tuple[int, ...]]] = field(default_factory=list)

    def face(self, group: str, material: str, points: list[tuple[float, float, float]]) -> None:
        start = len(self.vertices) + 1
        self.vertices.extend(points)
        self.faces.append((group, material, tuple(range(start, start + len(points)))))

    def quad(self, group: str, material: str, a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float], d: tuple[float, float, float]) -> None:
        self.face(group, material, [a, b, c, d])

    def box(self, group: str, material: str, lo: tuple[float, float, float], hi: tuple[float, float, float]) -> None:
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        self.quad(group, material, (x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0))
        self.quad(group, material, (x0,y0,z1), (x0,y1,z1), (x1,y1,z1), (x1,y0,z1))
        self.quad(group, material, (x0,y0,z0), (x0,y0,z1), (x1,y0,z1), (x1,y0,z0))
        self.quad(group, material, (x1,y1,z0), (x1,y1,z1), (x0,y1,z1), (x0,y1,z0))
        self.quad(group, material, (x0,y1,z0), (x0,y1,z1), (x0,y0,z1), (x0,y0,z0))
        self.quad(group, material, (x1,y0,z0), (x1,y0,z1), (x1,y1,z1), (x1,y1,z0))


def conceptual_layout(p: dict[str, Any], m: dict[str, float]) -> dict[str, Any]:
    px0, py0, pz0 = m["left"], m["front"], m["bottom"]
    px1, py1, pz1 = px0 + m["pack_w"], py0 + m["pack_d"], pz0 + m["stack_h"]
    upper_z = m["h"] - m["top"] * UPPER_SENSOR_FROM_TOP_RATIO
    enclosure = p["enclosure"]
    door_w = number(enclosure["door_opening_width"], "enclosure.door_opening_width")
    door_h = number(enclosure["door_opening_height"], "enclosure.door_opening_height")
    window_w = number(enclosure["observation_window_width"], "enclosure.observation_window_width")
    window_h = number(enclosure["observation_window_height"], "enclosure.observation_window_height")
    door_x = (m["w"] - door_w) / 2
    window_x = (m["w"] - window_w) / 2
    door = (door_x, 0.0, door_x + door_w, door_h)
    window = (window_x, 150.0, window_x + window_w, 150.0 + window_h)  # 2D 승인 배치의 바닥 기준 절대 위치
    handle_length = number(enclosure["door_handle_length"], "enclosure.door_handle_length")
    handle_x = door[2] - number(enclosure["door_handle_offset"], "enclosure.door_handle_offset")
    handle_z = door_h / 2
    scale = min(m["w"], m["d"], m["h"])
    marker_half = scale * MARKER_SIZE_RATIO
    # 마커 외곽과 인접 모서리 사이에 최소 마커 한 변(2 * marker_half)을 둔다.
    edge_center = marker_half * 3
    display_offset = scale * DISPLAY_OFFSET_RATIO
    sensor_zones = {
        "upper-left": (m["w"] * UPPER_SENSOR_X_RATIOS[0], m["d"] * 0.50, upper_z),
        "upper-center": (m["w"] * UPPER_SENSOR_X_RATIOS[1], m["d"] * 0.50, upper_z),
        "upper-right": (m["w"] * UPPER_SENSOR_X_RATIOS[2], m["d"] * 0.50, upper_z),
    }
    points = {name: sensor_zones[item["value"]] for name, item in p["sensor_points"].items()}
    port_zones = {
        "rear-mid-lower": ((m["w"] - display_offset, m["d"] - edge_center, m["h"] * MID_LOWER_RATIO), "yz", "inlet_dependent"),
        "front-upper-opposite": ((display_offset, edge_center, m["h"] * UPPER_RATIO), "yz", "exhaust_dependent"),
        "side-lower-separated": ((m["w"] - display_offset, m["d"] * CABLE_Y_RATIO,
                                  m["frame_h"] + marker_half), "yz", "cable_dependent"),
    }
    ports = {}
    for name, item in p["ports"].items():
        if name.endswith("_diameter"):
            continue
        value = item["value"]
        zone = value["zone"] if isinstance(value, dict) else value
        ports[name] = port_zones[zone]
    return {
        "pack": (px0, py0, pz0, px1, py1, pz1), "door": door, "window": window,
        "handle": (handle_x, handle_z - handle_length / 2, handle_z + handle_length / 2),
        "display_offset": display_offset, "marker_half": marker_half,
        "ports": ports, "sensors": points,
    }


def marker_quad(mesh: Mesh, group: str, material: str, center: tuple[float,float,float], size: float, plane: str) -> None:
    x, y, z = center
    if plane == "xz":
        mesh.quad(group, material, (x-size,y,z-size), (x+size,y,z-size), (x+size,y,z+size), (x-size,y,z+size))
    elif plane == "yz":
        mesh.quad(group, material, (x,y-size,z-size), (x,y+size,z-size), (x,y+size,z+size), (x,y-size,z+size))
    else:
        mesh.quad(group, material, (x-size,y-size,z), (x+size,y-size,z), (x+size,y+size,z), (x-size,y+size,z))


def electrical_envelope(p: dict[str, Any]) -> tuple[float, float, float, float, float, float]:
    """전장 설치 공간의 (x0, y0, z0, x1, y1, z1). 값은 status: proposed 이며 사람 미승인이다."""
    e = p["electrical_envelope"]
    x0 = number(e["left_offset"], "electrical_envelope.left_offset")
    y0 = number(e["front_offset"], "electrical_envelope.front_offset")
    z0 = number(e["bottom_offset"], "electrical_envelope.bottom_offset")
    return (x0, y0, z0,
            x0 + number(e["width"], "electrical_envelope.width"),
            y0 + number(e["depth"], "electrical_envelope.depth"),
            z0 + number(e["height"], "electrical_envelope.height"))


def build(p: dict[str, Any]) -> tuple[Mesh, dict[str, float], dict[str, Any]]:
    m = dimensions(p)
    layout = conceptual_layout(p, m)
    mesh = Mesh()
    wall = m["wall"]
    mesh.box("outer_enclosure_shell", "outer_shell", (-wall,-wall,-wall), (m["w"]+wall,m["d"]+wall,m["h"]+wall))
    mesh.box("internal_effective_volume_surface", "effective_volume", (0.0,0.0,0.0), (m["w"],m["d"],m["h"]))
    # 높이만 승인됐다. 다리·상판 형상은 미정이므로 하부 구간 전체를 표현용 단일 블록으로 표시한다.
    mesh.box("floor_support_frame_concept", "floor_frame", (0.0,0.0,0.0), (m["w"],m["d"],m["frame_h"]))
    x0,y0,z0,x1,y1,_ = layout["pack"]
    for index in range(int(m["count"])):
        lo = (x0, y0, z0 + index*m["pack_h"])
        hi = (x1, y1, lo[2] + m["pack_h"])
        mesh.box(f"pack_{index+1:02d}", "pack", lo, hi)
    ex0,ey0,ez0,ex1,ey1,ez1 = electrical_envelope(p)
    # 제안값이다. 함체 형상이 아니라 확보해야 할 설치 공간의 경계 상자다.
    mesh.box("electrical_envelope_proposed", "electrical_envelope", (ex0,ey0,ez0), (ex1,ey1,ez1))
    dx0,dz0,dx1,dz1 = layout["door"]
    offset = layout["display_offset"]
    mesh.quad("door_opening", "door", (dx0,offset,dz0),(dx1,offset,dz0),(dx1,offset,dz1),(dx0,offset,dz1))
    wx0,wz0,wx1,wz1 = layout["window"]
    mesh.quad("viewing_window_fixed", "window", (wx0,offset,wz0),(wx1,offset,wz0),(wx1,offset,wz1),(wx0,offset,wz1))
    hx,hz0,hz1 = layout["handle"]
    marker = layout["marker_half"]
    handle_half_width = marker * 0.10  # 화면 식별만 위한 표현용 폭이며 손잡이 제작 치수가 아니다.
    mesh.quad("door_handle", "handle", (hx-handle_half_width,offset,hz0),
              (hx+handle_half_width,offset,hz0), (hx+handle_half_width,offset,hz1),
              (hx-handle_half_width,offset,hz1))
    for name, (point, plane, material) in layout["ports"].items():
        marker_quad(mesh, f"{name}_port_diameter_dependent", material, point, marker, plane)
    for name, point in layout["sensors"].items():
        s = marker * 0.55
        x,y,z = point
        mesh.face(f"sensor_{name}_concept", "sensor_concept", [(x-s,y,z),(x,y-s,z),(x+s,y,z),(x,y+s,z)])
    add_axes(mesh, m)
    return mesh, m, layout


def add_axes(mesh: Mesh, m: dict[str,float]) -> None:
    length = min(m["w"],m["d"],m["h"]) * AXIS_LENGTH_RATIO
    width = min(m["w"],m["d"],m["h"]) * AXIS_WIDTH_RATIO
    mesh.box("axis_X_width", "axis_x", (0,0,0), (length,width,width))
    mesh.box("axis_Y_depth", "axis_y", (0,0,0), (width,length,width))
    mesh.box("axis_Z_height", "axis_z", (0,0,0), (width,width,length))


def triangles(mesh: Mesh):
    for group, material, face in mesh.faces:
        for i in range(1, len(face)-1):
            yield group, material, (face[0], face[i], face[i+1])


def write_mtl(path: Path) -> None:
    lines = ["# 지표 3 ESS 모의 챔버 재질/색 정의; 물리 재질 사양이 아님"]
    for name, (r,g,b,a) in MATERIALS.items():
        lines.extend((f"newmtl {name}", f"Kd {r:.3f} {g:.3f} {b:.3f}", f"d {a:.3f}", "illum 2", ""))
    path.write_text("\n".join(lines), encoding="utf-8")


def write_obj(mesh: Mesh, path: Path) -> None:
    lines = ["# 단위 mm, Z-up; 원점은 내부 바닥 도어측 좌측 모서리", "mtllib chamber.mtl"]
    for x,y,z in mesh.vertices:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    current = None
    for group, material, face in mesh.faces:
        key = (group, material)
        if key != current:
            lines.extend((f"g {group}", f"usemtl {material}"))
            current = key
        lines.append("f " + " ".join(str(index) for index in face))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normal(a, b, c):
    u = tuple(b[i]-a[i] for i in range(3)); v = tuple(c[i]-a[i] for i in range(3))
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(sum(value*value for value in n))
    return tuple(value/length for value in n) if length else (0.0,0.0,0.0)


def write_stl(mesh: Mesh, path: Path) -> None:
    lines = ["solid chamber"]
    for _,_,face in triangles(mesh):
        pts = [mesh.vertices[index-1] for index in face]
        n = normal(*pts)
        lines.append(f"  facet normal {n[0]:.9g} {n[1]:.9g} {n[2]:.9g}")
        lines.append("    outer loop")
        lines.extend(f"      vertex {x:.9g} {y:.9g} {z:.9g}" for x,y,z in pts)
        lines.extend(("    endloop", "  endfacet"))
    lines.append("endsolid chamber")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def validate_geometry(p: dict[str,Any], m: dict[str,float], layout: dict[str,Any]) -> None:
    x0,y0,z0,x1,y1,z1 = layout["pack"]
    actual = (x0, m["w"]-x1, y0, m["d"]-y1, z0, m["h"]-z1)
    expected = (m["left"],m["right"],m["front"],m["rear"],m["bottom"],m["top"])
    assert all(math.isclose(a,b) for a,b in zip(actual,expected))
    print("1 Pack containment OK: six clearances match chamber_params.json: " + ", ".join(f"{v:g}" for v in actual) + " mm")
    changed = copy.deepcopy(p); changed["pack"]["count"]["value"] = int(m["count"]) + 1
    cm = dimensions(changed); cl = conceptual_layout(changed, cm)
    assert cm["stack_h"] == m["stack_h"] + m["pack_h"] and cm["h"] == m["h"] + m["pack_h"]
    assert math.isclose(cm["h"]-cl["pack"][5], cm["top"])
    print(f"2 Pack-count recalculation OK: count {int(m['count'])} -> {int(cm['count'])}, stack H {m['stack_h']:g} -> {cm['stack_h']:g}, H_in {m['h']:g} -> {cm['h']:g} mm")
    door, window = layout["door"], layout["window"]
    offset = layout["display_offset"]
    assert 0 < offset < min(m["left"],m["right"],m["front"],m["rear"],m["bottom"],m["top"])
    assert door[0] <= x0 and door[1] <= z0 and door[2] >= x1 and door[3] >= z1
    assert door[0] <= window[0] < window[2] <= door[2] and door[1] <= window[1] < window[3] <= door[3]
    assert max(window[1], z0) < min(window[3], z1), "관찰창과 팩 전면 높이 구간이 겹쳐야 함"
    handle_x, handle_z0, handle_z1 = layout["handle"]
    assert door[0] < handle_x < door[2] and door[1] <= handle_z0 < handle_z1 <= door[3]
    assert handle_x > window[2]
    print(f"3 Door/window/handle placement OK: door {door[2]-door[0]:g} x {door[3]-door[1]:g} mm, window {window[2]-window[0]:g} x {window[3]-window[1]:g} mm inside door, handle x={handle_x:g} mm outside window")
    port_points = {name: spec[0] for name, spec in layout["ports"].items()}
    inlet, exhaust = port_points["common_inlet"], port_points["exhaust"]
    marker_half = layout["marker_half"]
    marker_side = marker_half * 2
    inlet_rear_clearance = m["d"] - (inlet[1] + marker_half)
    exhaust_front_clearance = exhaust[1] - marker_half
    cable_floor_clearance = port_points["cable_entry"][2] - marker_half
    assert math.isclose(inlet[0], m["w"]-offset) and math.isclose(exhaust[0], offset)
    assert inlet[1] > exhaust[1] and inlet[2] < m["h"]*0.5 < exhaust[2]
    assert min(inlet_rear_clearance, exhaust_front_clearance, cable_floor_clearance) >= marker_side
    assert cable_floor_clearance >= m["frame_h"], "케이블 관통 포트 최저점은 프레임 상면 이상이어야 함"
    assert set(port_points) == {name for name in p["ports"] if not name.endswith("_diameter")}
    print(f"4 Airflow/port placement OK: {len(port_points)} parameter-driven markers; wall offset {offset:.3f} mm; nearest-edge clearances inlet {inlet_rear_clearance:.3f}, exhaust {exhaust_front_clearance:.3f}, cable {cable_floor_clearance:.3f} mm >= marker side {marker_side:.3f} mm; cable bottom >= frame top {m['frame_h']:.3f} mm")
    sensors = list(layout["sensors"].values())
    assert all(0 < x < m["w"] and 0 < y < m["d"] and 0 < z < m["h"] for x,y,z in sensors)
    distances = [math.dist(a,b) for i,a in enumerate(sensors) for b in sensors[i+1:]]
    marker_diameter = 2 * min(m["w"],m["d"],m["h"]) * MARKER_SIZE_RATIO
    assert min(distances) >= marker_diameter
    assert set(layout["sensors"]) == set(p["sensor_points"])
    print(f"5 Sensor placement OK: {len(sensors)} parameter-driven points inside; minimum spacing {min(distances):.3f} mm >= conceptual marker diameter {marker_diameter:.3f} mm")


def validate_electrical_envelope(p: dict[str,Any], m: dict[str,float], layout: dict[str,Any]) -> None:
    """검사 9. 전장 설치 공간이 내부 유효 체적 안에 있고 팩과 3차원으로 간섭하지 않는지 본다."""
    e = p["electrical_envelope"]
    assert all(item["status"] == "proposed" for item in e.values()), "전장 설치 공간 값은 전부 status: proposed 여야 한다"
    x0,y0,z0,x1,y1,z1 = electrical_envelope(p)
    assert 0 <= x0 < x1 <= m["w"] and 0 <= y0 < y1 <= m["d"] and 0 <= z0 < z1 <= m["h"], \
        "전장 설치 공간이 내부 유효 체적을 벗어난다"
    px0,py0,pz0,px1,py1,_ = layout["pack"]
    pz1 = pz0 + m["stack_h"]
    overlaps = [x0 < px1 and px0 < x1, y0 < py1 and py0 < y1, z0 < pz1 and pz0 < z1]
    assert not all(overlaps), "전장 설치 공간이 팩과 3차원으로 간섭한다"
    touching = [n for n, ok in (("좌측벽", x0 == 0), ("우측벽", x1 == m["w"]),
                                ("전면", y0 == 0), ("후벽", y1 == m["d"]),
                                ("바닥", z0 == 0), ("상판", z1 == m["h"])) if ok]
    print(f"9 Electrical envelope OK: {x1-x0:.0f} x {y1-y0:.0f} x {z1-z0:.0f} mm at ({x0:.0f}, {y0:.0f}, {z0:.0f}); "
          f"팩과 3차원 간섭 없음; 밀착면 {', '.join(touching) if touching else '없음'}")


def validate_obj(path: Path, mtl_path: Path, expected_groups: int, m: dict[str, float]) -> None:
    vertices: list[tuple[float, float, float]] = []
    groups = set(); used = set(); grouped_faces: list[tuple[str, list[int]]] = []
    current_group = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()
            vertices.append((float(x), float(y), float(z)))
        elif line.startswith("g "):
            current_group = line[2:]
            groups.add(current_group)
        elif line.startswith("usemtl "): used.add(line[7:])
        elif line.startswith("f "):
            grouped_faces.append((current_group, [int(token.split('/')[0]) for token in line[2:].split()]))
    defined = {line[7:] for line in mtl_path.read_text(encoding="utf-8").splitlines() if line.startswith("newmtl ")}
    assert vertices and groups and grouped_faces
    assert all(1 <= i <= len(vertices) for _, face in grouped_faces for i in face) and used <= defined
    assert all(name for name in groups) and len(groups) == expected_groups
    internal_bounds = (m["w"], m["d"], m["h"])
    wall = m["wall"]
    outer_bounds = (m["w"] + wall, m["d"] + wall, m["h"] + wall)
    for group, face in grouped_faces:
        for index in face:
            vertex = vertices[index-1]
            assert all(-wall <= coordinate <= limit for coordinate, limit in zip(vertex, outer_bounds)), (
                f"OBJ vertex outside outer bounds: group={group}, vertex={index}, coordinate={vertex}"
            )
            if group != "outer_enclosure_shell":
                assert all(0.0 <= coordinate <= limit for coordinate, limit in zip(vertex, internal_bounds)), (
                    f"OBJ vertex outside internal bounds: group={group}, vertex={index}, coordinate={vertex}"
                )
    print(f"6 OBJ reparse/bounds OK: {len(vertices)} vertices, {len(grouped_faces)} faces, {len(groups)} groups; internal groups inside 0..W/D/H; all vertices inside -wall..W/D/H+wall")


def validate_volumes(p: dict[str,Any], m: dict[str,float]) -> None:
    chamber = m["w"]*m["d"]*m["h"]/1_000_000_000
    pack = m["pack_w"]*m["pack_d"]*m["stack_h"]/1_000_000_000
    x0,y0,z0,x1,y1,z1 = electrical_envelope(p)
    envelope = (x1-x0)*(y1-y0)*(z1-z0)/1_000_000_000
    free = chamber-pack-envelope
    # 서로 다른 단위 변환 경로를 대조해 mm^3 -> m^3 계산과 자유 공간 차감을 검증한다.
    expected_chamber = (m["w"]/1000) * (m["d"]/1000) * (m["h"]/1000)
    expected_pack = (m["pack_w"]/1000) * (m["pack_d"]/1000) * (m["stack_h"]/1000)
    assert math.isclose(chamber, expected_chamber, abs_tol=1e-12)
    assert math.isclose(pack, expected_pack, abs_tol=1e-12)
    assert math.isclose(free + pack + envelope, chamber, abs_tol=1e-12) and free > 0
    print(f"7 Volume validation OK: internal {chamber:.6f} m3, pack {pack:.6f} m3, 전장 설치 공간(제안) {envelope:.6f} m3, free {free:.6f} m3")


def validate_stl(path: Path, expected: int) -> None:
    lines = path.read_text(encoding="ascii").splitlines()
    facets = sum(line.strip().startswith("facet normal ") for line in lines)
    assert lines[0] == "solid chamber" and lines[-1] == "endsolid chamber"
    assert facets == expected and sum(line.strip() == "endfacet" for line in lines) == expected
    assert sum(line.strip() == "outer loop" for line in lines) == expected and sum(line.strip() == "endloop" for line in lines) == expected
    print(f"8 STL reparse OK: solid/endsolid structure, {facets} triangles")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, default=DEFAULT_PARAMS)
    args = parser.parse_args()
    p = load_params(args.params)
    mesh, m, layout = build(p)
    validate_geometry(p,m,layout)
    write_mtl(MTL_PATH); write_obj(mesh,OBJ_PATH); write_stl(mesh,STL_PATH)
    validate_obj(OBJ_PATH, MTL_PATH, len({group for group, _, _ in mesh.faces}), m)
    validate_volumes(p, m)
    validate_stl(STL_PATH, sum(1 for _ in triangles(mesh)))
    validate_electrical_envelope(p, m, layout)
    print(f"Generated {OBJ_PATH.name}, {MTL_PATH.name}, and {STL_PATH.name}")
    print(f"Fixed dimensions: internal {m['w']:.0f} x {m['d']:.0f} x {m['h']:.0f} mm; outer {m['w']+2*m['wall']:.0f} x {m['d']+2*m['wall']:.0f} x {m['h']+2*m['wall']:.0f} mm")


if __name__ == "__main__":
    main()
