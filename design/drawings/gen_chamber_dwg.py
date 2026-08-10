#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a parametric chamber three-view drawing as UTF-8 DXF R2007 and SVG.

Only the Python standard library is used. Design values live in
chamber_params.json; rendering constants below affect sheet layout only and are
not physical dimensions.
"""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any
import unicodedata
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
DEFAULT_PARAMS = ROOT / "chamber_params.json"
DXF_PATH = ROOT / "chamber.dxf"
SVG_PATH = ROOT / "chamber.svg"

LAYER_STYLES: dict[str, tuple[str, int, float, str | None]] = {
    # layer: (DXF linetype, DXF lineweight 1/100 mm, SVG width, SVG dash)
    "EFFECTIVE": ("CONTINUOUS", 18, 2.0, None),
    "DOOR": ("CONTINUOUS", 18, 2.0, None),
    "WINDOW": ("CONTINUOUS", 18, 2.0, None),
    "PACK": ("CONTINUOUS", 35, 3.0, None),
    "FRAME": ("CONTINUOUS", 30, 2.5, None),
    "OUTLINE": ("CONTINUOUS", 25, 2.5, None),
    "HANDLE": ("CONTINUOUS", 30, 3.0, None),
    "SEN55": ("CONTINUOUS", 25, 2.5, None),
    "DIM": ("CONTINUOUS", 18, 2.0, None),
    "LEADER": ("CONTINUOUS", 18, 2.0, None),
}


def load_params(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("meta", "pack", "clearance", "enclosure", "floor_frame", "electrical_envelope", "ports", "sensor_points")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"missing parameter sections: {', '.join(missing)}")
    for section in ("pack", "clearance", "enclosure", "floor_frame", "electrical_envelope", "ports", "sensor_points"):
        for name, item in data[section].items():
            if not isinstance(item, dict) or not {"value", "unit", "status", "source"} <= item.keys():
                raise ValueError(f"invalid parameter record: {section}.{name}")
            if item["status"] not in {"fixed", "dependent", "proposed"}:
                raise ValueError(f"invalid status: {section}.{name}")
            if item["status"] == "fixed" and item["value"] is None:
                raise ValueError(f"fixed value cannot be null: {section}.{name}")
            if item["status"] == "dependent":
                if item["value"] is not None:
                    raise ValueError(f"dependent value must be null: {section}.{name}")
                if not isinstance(item.get("depends_on"), str) or not item["depends_on"].strip():
                    raise ValueError(f"dependent value requires depends_on: {section}.{name}")
    if number(data["floor_frame"]["height"], "floor_frame.height") != number(data["clearance"]["bottom"], "clearance.bottom"):
        raise ValueError("floor_frame.height must equal clearance.bottom")
    return data


def number(item: dict[str, Any], name: str) -> float:
    value = item["value"]
    if not isinstance(value, (int, float)):
        raise ValueError(f"numeric value required: {name}")
    return float(value)


def dependent_parameters(data: dict[str, Any]) -> list[str]:
    return [
        f"{section}.{name}: {item['depends_on']}"
        for section, records in data.items()
        if isinstance(records, dict)
        for name, item in records.items()
        if isinstance(item, dict) and item.get("status") == "dependent"
    ]


def dimensions(p: dict[str, Any]) -> dict[str, float]:
    pack = p["pack"]
    c = p["clearance"]
    pw = number(pack["width"], "pack.width")
    pd = number(pack["depth"], "pack.depth")
    ph = number(pack["height"], "pack.height")
    count = number(pack["count"], "pack.count")
    stack_h = ph * count
    return {
        "pack_w": pw,
        "pack_d": pd,
        "pack_h": ph,
        "stack_h": stack_h,
        "w": pw + number(c["side_left"], "clearance.side_left") + number(c["side_right"], "clearance.side_right"),
        "d": pd + number(c["front"], "clearance.front") + number(c["rear"], "clearance.rear"),
        "h": stack_h + number(c["bottom"], "clearance.bottom") + number(c["top"], "clearance.top"),
        "left": number(c["side_left"], "clearance.side_left"),
        "right": number(c["side_right"], "clearance.side_right"),
        "front": number(c["front"], "clearance.front"),
        "rear": number(c["rear"], "clearance.rear"),
        "top": number(c["top"], "clearance.top"),
        "bottom": number(c["bottom"], "clearance.bottom"),
        "wall": number(p["enclosure"]["wall_thickness"], "enclosure.wall_thickness"),
    }


class Drawing:
    def __init__(self) -> None:
        self.entities: list[tuple[str, tuple[Any, ...]]] = []
        self.regions: dict[str, tuple[float, float, float, float]] = {}
        self.text_boxes: list[tuple[str, tuple[float, float, float, float]]] = []
        self.leaders: list[dict[str, Any]] = []

    def line(self, x1: float, y1: float, x2: float, y2: float, layer: str = "OBJECT") -> None:
        self.entities.append(("LINE", (x1, y1, x2, y2, layer)))

    def rect(self, x: float, y: float, w: float, h: float, layer: str = "OBJECT") -> None:
        self.line(x, y, x + w, y, layer)
        self.line(x + w, y, x + w, y + h, layer)
        self.line(x + w, y + h, x, y + h, layer)
        self.line(x, y + h, x, y, layer)

    def circle(self, x: float, y: float, r: float, layer: str = "PORT") -> None:
        self.entities.append(("CIRCLE", (x, y, r, layer)))

    def text(self, x: float, y: float, value: str, height: float = 28, layer: str = "TEXT") -> None:
        self.entities.append(("TEXT", (x, y, value, height, layer)))
        self.text_boxes.append((value, (x, y, x + estimate_text_width(value, height), y + height)))

    def dim_h(self, x1: float, x2: float, y: float, label: str) -> None:
        self.line(x1, y, x2, y, "DIM")
        self.line(x1, y - 12, x1, y + 12, "DIM")
        self.line(x2, y - 12, x2, y + 12, "DIM")
        self.text((x1 + x2) / 2 - estimate_text_width(label, 22) / 2, y + 16, label, 22, "DIM")

    def dim_v(self, y1: float, y2: float, x: float, label: str, side: str = "right") -> None:
        self.line(x, y1, x, y2, "DIM")
        self.line(x - 12, y1, x + 12, y1, "DIM")
        self.line(x - 12, y2, x + 12, y2, "DIM")
        tx = x + 16 if side == "right" else x - 16 - estimate_text_width(label, 22)
        self.text(tx, (y1 + y2) / 2, label, 22, "DIM")


def dogleg_leader(
    d: Drawing,
    x: float,
    y: float,
    label: str,
    view_box: tuple[float, float, float, float],
    route: str = "right",
    outside_offset: float = 35.0,
    diagonal_sign: int = 1,
) -> None:
    """Draw a conventional two-segment leader: diagonal exit plus short landing."""
    assert diagonal_sign in (-1, 1)
    landing = 60.0  # sheet-layout convention: three times the 20-unit text height
    if route == "right":
        elbow_x = view_box[2] + outside_offset
        elbow = (elbow_x, y + diagonal_sign * (elbow_x - x))
        end = (elbow_x + landing, elbow[1])
        text_x = end[0] + 8
        text_y = end[1]
        align = "left"
    elif route == "left":
        elbow_x = view_box[0] - outside_offset
        elbow = (elbow_x, y + diagonal_sign * (x - elbow_x))
        end = (elbow_x - landing, elbow[1])
        text_x = end[0] - 8 - estimate_text_width(label, 20)
        text_y = end[1]
        align = "right"
    elif route == "top":
        elbow_y = view_box[3] + outside_offset
        elbow = (x + diagonal_sign * (elbow_y - y), elbow_y)
        end = (elbow[0] + diagonal_sign * landing, elbow_y)
        text_x = end[0] + 8 if diagonal_sign > 0 else end[0] - 8 - estimate_text_width(label, 20)
        text_y = elbow_y
        align = "left" if diagonal_sign > 0 else "right"
    elif route == "bottom":
        elbow_y = view_box[1] - outside_offset
        elbow = (x + diagonal_sign * (y - elbow_y), elbow_y)
        end = (elbow[0] + diagonal_sign * landing, elbow_y)
        text_x = end[0] + 8 if diagonal_sign > 0 else end[0] - 8 - estimate_text_width(label, 20)
        text_y = elbow_y
        align = "left" if diagonal_sign > 0 else "right"
    else:
        raise ValueError(f"unsupported leader route: {route}")
    waypoints = [(x, y), elbow, end]
    segments = []
    for start, end in zip(waypoints, waypoints[1:]):
        d.line(start[0], start[1], end[0], end[1], "LEADER")
        segments.append((start[0], start[1], end[0], end[1], "LEADER"))
    d.text(text_x, text_y, label, 20, "TEXT")
    d.leaders.append({"label": label, "segments": segments, "label_box": d.text_boxes[-1][1], "view_box": view_box, "alignment": align})


def add_marker(d: Drawing, x: float, y: float, label: str, view_box: tuple[float, float, float, float], route: str = "right", outside_offset: float = 35.0, diagonal_sign: int = 1) -> None:
    d.circle(x, y, 18, "SENSOR")
    d.line(x - 13, y, x + 13, y, "SENSOR")
    d.line(x, y - 13, x, y + 13, "SENSOR")
    dogleg_leader(d, x, y, label, view_box, route, outside_offset, diagonal_sign)


def add_sen55(d: Drawing, x: float, y: float, label: str, view_box: tuple[float, float, float, float], outside_offset: float, diagonal_sign: int = 1) -> None:
    width, height = 52.3, 43.3
    d.rect(x - width / 2, y - height / 2, width, height, "SEN55")
    dogleg_leader(d, x, y + height / 2, label, view_box, "top", outside_offset, diagonal_sign)


def add_port(d: Drawing, x: float, y: float, label: str, view_box: tuple[float, float, float, float], route: str = "right", outside_offset: float = 35.0, diagonal_sign: int = 1) -> tuple[float, float, float, float]:
    """Draw a symbolic port marker; its radius is sheet layout, not a physical diameter."""
    d.circle(x, y, 22, "PORT")
    dogleg_leader(d, x, y, label, view_box, route, outside_offset, diagonal_sign)
    return (x - 22, y - 22, x + 22, y + 22)


def add_cable_plate(d: Drawing, x: float, y: float, label: str, view_box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Draw the penetration plate outline only; size is a sheet-layout symbol, not a physical dimension."""
    width, height = 70.0, 45.0
    box = (x, y, x + width, y + height)
    d.rect(x, y, width, height, "PORT")
    dogleg_leader(d, x, y + height, label, view_box, "bottom", 250, -1)
    return box


def add_leader_label(d: Drawing, x: float, y: float, label: str, view_box: tuple[float, float, float, float], route: str = "right", outside_offset: float = 35.0, diagonal_sign: int = 1) -> None:
    dogleg_leader(d, x, y, label, view_box, route, outside_offset, diagonal_sign)


def estimate_text_width(value: str, height: float) -> float:
    """Estimate TEXT width, counting Hangul/CJK glyphs as full-width."""
    units = 0.0
    for char in value:
        if unicodedata.east_asian_width(char) in ("W", "F"):
            units += 1.0
        elif char.isspace():
            units += 0.35
        else:
            units += 0.6
    return units * height


def build(p: dict[str, Any]) -> tuple[Drawing, dict[str, float]]:
    m, d = dimensions(p), Drawing()
    wall = m["wall"]
    m.update({"outer_w": m["w"] + 2 * wall, "outer_d": m["d"] + 2 * wall, "outer_h": m["h"] + 2 * wall})
    fx, fy, gap = 450.0, 2100.0, 700.0
    sx, sy, px, py = fx + m["w"] + gap, fy, fx, 250.0

    def frame(x: float, y: float, width: float, name: str) -> tuple[float, float, float, float]:
        top_t, leg_w = 18.0, 35.0  # sheet-layout depiction only
        d.rect(x, y + m["bottom"] - top_t, width, top_t, "FRAME")
        left_x = x + 35
        d.rect(left_x, y, leg_w, m["bottom"] - top_t, "FRAME")
        right_x = x + width - 70
        d.rect(right_x, y, leg_w, m["bottom"] - top_t, "FRAME")
        d.regions[f"{name}_leg_left"] = (left_x, y, left_x + leg_w, y + m["bottom"] - top_t)
        d.regions[f"{name}_leg_right"] = (right_x, y, right_x + leg_w, y + m["bottom"] - top_t)
        return (x, y, x + width, y + m["bottom"])

    # 정면도
    front_view = (fx - wall, fy - wall, fx + m["w"] + wall, fy + m["h"] + wall)
    d.rect(front_view[0], front_view[1], m["outer_w"], m["outer_h"], "OUTLINE")
    d.rect(fx, fy, m["w"], m["h"], "EFFECTIVE")
    d.regions["chamber_front"] = (fx, fy, fx + m["w"], fy + m["h"])
    pack_x, pack_y = fx + m["left"], fy + m["bottom"]
    d.regions["frame_front"] = frame(fx, fy, m["w"], "frame_front")
    d.regions["pack_front"] = (pack_x, pack_y, pack_x + m["pack_w"], pack_y + m["stack_h"])
    d.rect(pack_x, pack_y, m["pack_w"], m["stack_h"], "PACK")
    door_w = number(p["enclosure"]["door_opening_width"], "door width")
    door_h = number(p["enclosure"]["door_opening_height"], "door height")
    door_x = fx + (m["w"] - door_w) / 2
    d.regions["door"] = (door_x, fy, door_x + door_w, fy + door_h)
    d.line(door_x, fy, door_x + door_w, fy, "DOOR")
    d.line(door_x, fy, door_x, fy + door_h, "DOOR")
    d.line(door_x + door_w, fy, door_x + door_w, fy + door_h, "DOOR")
    d.line(door_x, fy + door_h, door_x + door_w, fy + door_h, "DOOR")
    win_w = number(p["enclosure"]["observation_window_width"], "window width")
    win_h = number(p["enclosure"]["observation_window_height"], "window height")
    win_x, win_y = fx + (m["w"] - win_w) / 2, fy + 150
    d.regions["window"] = (win_x, win_y, win_x + win_w, win_y + win_h)
    d.rect(win_x, win_y, win_w, win_h, "WINDOW")
    handle_type = str(p["enclosure"]["door_handle_type"]["value"])
    handle_length = number(p["enclosure"]["door_handle_length"], "door handle length")
    handle_offset = number(p["enclosure"]["door_handle_offset"], "door handle offset")
    handle_x = door_x + door_w - handle_offset
    handle_y = fy + door_h / 2
    handle_half_width = 8.0  # sheet-layout depiction only
    d.regions["handle"] = (handle_x - handle_half_width, handle_y - handle_length / 2, handle_x + handle_half_width, handle_y + handle_length / 2)
    d.line(handle_x, handle_y - handle_length / 2, handle_x, handle_y + handle_length / 2, "HANDLE")
    d.line(handle_x - handle_half_width, handle_y - handle_length / 2, handle_x + handle_half_width, handle_y - handle_length / 2, "HANDLE")
    d.line(handle_x - handle_half_width, handle_y + handle_length / 2, handle_x + handle_half_width, handle_y + handle_length / 2, "HANDLE")
    d.text(fx, fy + m["h"] + 150, "정면 (도어측)", 30)
    add_leader_label(d, pack_x + m["pack_w"], pack_y + m["stack_h"], "시료 팩 1", front_view, "right", 35, 1)
    add_leader_label(d, fx + m["w"], fy + m["bottom"], f"받침 프레임 H{m['bottom']:.0f}", front_view, "right", 35, -1)
    add_leader_label(d, door_x + door_w, fy + door_h, f"도어 개구 {door_w:.0f} x {door_h:.0f}", front_view, "right", 85, 1)
    add_leader_label(d, win_x, win_y + win_h, f"관찰창 {win_w:.0f} x {win_h:.0f}", front_view, "left", 135, -1)
    add_leader_label(d, handle_x, handle_y, f"{handle_type} L{handle_length:.0f}", front_view, "right", 35, 1)
    for i, (ratio, label) in enumerate(((.22, "SEN55 상부1"), (.50, "SEN55 상부2"), (.78, "SEN55 상부3"))):
        marker_y = fy + m["h"] - 180 + i * 50
        add_sen55(d, fx + m["w"] * ratio, marker_y, label, front_view, 35 + i * 50, -1 if i < 2 else 1)
    d.dim_h(handle_x, door_x + door_w, fy - 240, f"핸들 오프셋 {handle_offset:.0f}")
    d.dim_v(handle_y - handle_length / 2, handle_y + handle_length / 2, front_view[0] - 750, f"핸들 길이 {handle_length:.0f}", "left")
    d.dim_h(fx - wall, fx + m["w"] + wall, fy - 185, f"외형 폭 {m['outer_w']:.0f} (W_out)")
    d.dim_h(fx, fx + m["w"], fy - 130, f"내부 폭 {m['w']:.0f} (W_in)")
    d.dim_h(fx, pack_x, fy - 75, f"좌측 여유 {m['left']:.0f} (C_side)")
    d.dim_h(pack_x + m["pack_w"], fx + m["w"], fy - 75, f"우측 여유 {m['right']:.0f} (C_side)")
    d.dim_v(fy - wall, fy + m["h"] + wall, fx - 500, f"외형 높이 {m['outer_h']:.0f} (H_out)", "left")
    d.dim_v(fy, fy + m["h"], fx - 175, f"내부 높이 {m['h']:.0f} (H_in)", "left")
    d.dim_v(fy, pack_y, fx - 175, f"하부 여유 {m['bottom']:.0f} (C_bottom)", "left")
    d.dim_v(pack_y + m["stack_h"], fy + m["h"], fx - 175, f"상부 여유 {m['top']:.0f} (C_top)", "left")

    # 측면도
    side_view = (sx - wall, sy - wall, sx + m["d"] + wall, sy + m["h"] + wall)
    d.rect(side_view[0], side_view[1], m["outer_d"], m["outer_h"], "OUTLINE")
    d.rect(sx, sy, m["d"], m["h"], "EFFECTIVE")
    spx, spy = sx + m["front"], sy + m["bottom"]
    cable_y = sy + m["bottom"]
    d.regions["frame_side"] = frame(sx, sy, m["d"], "frame_side")
    d.regions["pack_side"] = (spx, spy, spx + m["pack_d"], spy + m["stack_h"])
    d.rect(spx, spy, m["pack_d"], m["stack_h"], "PACK")
    d.text(sx, sy + m["h"] + 150, "측면", 30)
    d.dim_h(sx - wall, sx + m["d"] + wall, sy - 185, f"외형 깊이 {m['outer_d']:.0f} (D_out)")
    d.dim_h(sx, sx + m["d"], sy - 130, f"내부 깊이 {m['d']:.0f} (D_in)")
    d.dim_h(sx, spx, sy - 75, f"전면 여유 {m['front']:.0f} (C_front)")
    d.dim_h(spx + m["pack_d"], sx + m["d"], sy - 75, f"후면 여유 {m['rear']:.0f} (C_rear)")
    d.regions["cable_plate"] = add_cable_plate(d, sx + m["front"] * .45, cable_y, "케이블 관통 포트", side_view)
    add_leader_label(d, sx + m["d"], sy + m["bottom"], f"받침 프레임 H{m['bottom']:.0f}", side_view, "right", 35, 1)
    add_port(d, sx + m["d"] - 35, sy + m["h"] * .40, "공용 주입 포트 1구", side_view, "right", 35, 1)
    add_port(d, sx + 35, sy + m["h"] * .82, "배기 포트", side_view, "left", 85, 1)

    # 평면도
    plan_view = (px - wall, py - wall, px + m["w"] + wall, py + m["d"] + wall)
    d.rect(plan_view[0], plan_view[1], m["outer_w"], m["outer_d"], "OUTLINE")
    d.rect(px, py, m["w"], m["d"], "EFFECTIVE")
    d.rect(px + m["left"], py + m["front"], m["pack_w"], m["pack_d"], "PACK")
    d.text(px, py + m["d"] + 130, "평면", 30)
    d.dim_h(px - wall, px + m["w"] + wall, py - 185, f"외형 폭 {m['outer_w']:.0f} (W_out)")
    d.dim_h(px + m["left"], px + m["left"] + m["pack_w"], py - 130, f"팩 폭 {m['pack_w']:.0f}")
    d.dim_v(py - wall, py + m["d"] + wall, px - 500, f"외형 깊이 {m['outer_d']:.0f} (D_out)", "left")
    d.dim_v(py + m["front"], py + m["front"] + m["pack_d"], px - 90, f"팩 깊이 {m['pack_d']:.0f}", "left")
    handle_plan_x = px + (door_x - fx) + door_w - handle_offset
    d.line(handle_plan_x - 12, plan_view[1], handle_plan_x - 12, plan_view[1] - 25, "HANDLE")
    d.line(handle_plan_x + 12, plan_view[1], handle_plan_x + 12, plan_view[1] - 25, "HANDLE")
    d.line(handle_plan_x - 12, plan_view[1] - 25, handle_plan_x + 12, plan_view[1] - 25, "HANDLE")

    # 표제란과 주기는 각각 독립 앵커에서 위로 자란다.
    tbx, tby, tbw, tbh = sx, 240.0, m["d"], 190.0
    notes = ["주기", f"1. 재질 {p['enclosure']['material']['value']}, 판 두께 {wall:g} mm, 밀폐 등급 {p['enclosure']['sealing_grade']['value']}.", f"2. 내부 유효 {m['w']:.0f} x {m['d']:.0f} x {m['h']:.0f} mm; 외형 {m['outer_w']:.0f} x {m['outer_d']:.0f} x {m['outer_h']:.0f} mm.", "3. 센서 지점 3개소(포트 아님): 상부 SEN55 3대.", "4. SEN55 상세는 도면 J3-SN-001 참조. 외형 방향은 흡입구 위치 미상으로 단정하지 않는다.", "5. SEN55 금속 실드는 내부 GND와 연결된다. 챔버 직결 금지, 절연 브래킷 또는 등전위 설치.", "6. SEN55의 I2C 권장 배선 길이 10 cm 미만은 전장이 챔버 외부인 이 배치에서 준수 불가. 차폐 케이블 사용과 P82B715 버스 익스텐더 채널별 1쌍 삽입을 검토 중이며 둘 다 미확정. 배선 길이도 미정.", "7. 포트 구경은 종속값이다: 주입·배기는 장비 토출구·유량·압력손실·누설 시험, 케이블은 선정 케이블 외경(관통판 + 외경별 글랜드, 예비구 막음).", "8. 배수 포트를 두지 않는다. 관통부는 공용 주입 1구, 배기 1구, 케이블 관통 포트뿐이다. 잔류액은 퍼지·안전 확인 후 도어를 열어 회수한다.", "9. 전장(ESP32-S3-WROOM-1 N16R8 1대, PCA9548A 1개)은 챔버 상단 외부에 둔다. 챔버 내부에는 SEN55 3대만 노출한다. 전장함 규격과 설치 상세는 미정.", "10. SEN55 3대는 ESP32-S3의 I2C 1버스에서 PCA9548A(주소 0x70, A0=A1=A2=GND, RESET은 VCC 풀업)를 거쳐 채널 0~2에 한 대씩 연결한다. 전원 5 V와 통신은 USB 1개로 통합한다."]
    def text_block(name: str, x: float, bottom: float, lines: list[str]) -> None:
        spacing = 42.0
        top = bottom + (len(lines) - 1) * spacing + 30
        for i, line in enumerate(lines):
            d.text(x, top - 30 - i * spacing, line, 30 if i == 0 else 20, "NOTE")
        width = max(estimate_text_width(line, 30 if i == 0 else 20) for i, line in enumerate(lines))
        d.regions[name] = (x, bottom, x + width, top)
    text_block("notes", sx, tby + tbh + 55, notes)
    d.regions["title"] = (tbx, tby, tbx + tbw, tby + tbh)
    for first, second in (("notes", "title"),):
        assert_boxes_do_not_overlap(d.regions[first], d.regions[second])
    d.rect(tbx, tby, tbw, tbh, "TITLE")
    d.line(tbx, tby + 70, tbx + tbw, tby + 70, "TITLE")
    d.line(tbx, tby + 130, tbx + tbw, tby + 130, "TITLE")
    d.text(tbx + 15, tby + 145, p["meta"]["drawing_title"], 25, "TITLE")
    d.text(tbx + 15, tby + 88, f"도면번호: {p['meta']['drawing_number']}  REV: {p['meta']['revision']}", 22, "TITLE")
    d.text(tbx + 15, tby + 25, f"축척: {p['meta']['scale']}  단위: mm  작성일: {p['meta']['date']}", 22, "TITLE")
    return d, m


def assert_boxes_do_not_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> None:
    """Regression guard for two axis-aligned (min-x, min-y, max-x, max-y) boxes."""
    separated = (
        first[2] <= second[0]
        or second[2] <= first[0]
        or first[3] <= second[1]
        or second[3] <= first[1]
    )
    assert separated, f"drawing regions overlap: {first} vs {second}"


def assert_box_contains(
    outer: tuple[float, float, float, float],
    inner: tuple[float, float, float, float],
) -> None:
    assert outer[0] < inner[0] and outer[1] < inner[1] and outer[2] > inner[2] and outer[3] > inner[3], (
        f"outer box does not contain inner box with clearance on all sides: {outer} vs {inner}"
    )


def assert_vertical_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> None:
    overlap = min(first[3], second[3]) - max(first[1], second[1])
    assert overlap > 0, f"boxes have no vertical overlap: {first} vs {second}"


def line_intersects_box(line: tuple[Any, ...], box: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2, _ = line
    if max(x1, x2) < box[0] or min(x1, x2) > box[2] or max(y1, y2) < box[1] or min(y1, y2) > box[3]:
        return False
    dx, dy = x2 - x1, y2 - y1
    p, q = (-dx, dx, -dy, dy), (x1 - box[0], box[2] - x1, y1 - box[1], box[3] - y1)
    low, high = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return False
        else:
            ratio = qi / pi
            if pi < 0:
                low = max(low, ratio)
            else:
                high = min(high, ratio)
    return low <= high


def circle_intersects_box(circle: tuple[Any, ...], box: tuple[float, float, float, float]) -> bool:
    x, y, radius, _ = circle
    nearest_x = min(max(x, box[0]), box[2])
    nearest_y = min(max(y, box[1]), box[3])
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= radius ** 2


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def point_on_segment(point: tuple[float, float], line: tuple[Any, ...]) -> bool:
    a, b = (float(line[0]), float(line[1])), (float(line[2]), float(line[3]))
    return abs(orientation(a, b, point)) < 1e-9 and min(a[0], b[0]) - 1e-9 <= point[0] <= max(a[0], b[0]) + 1e-9 and min(a[1], b[1]) - 1e-9 <= point[1] <= max(a[1], b[1]) + 1e-9


def segments_intersect(first: tuple[Any, ...], second: tuple[Any, ...]) -> bool:
    a, b = (float(first[0]), float(first[1])), (float(first[2]), float(first[3]))
    c, e = (float(second[0]), float(second[1])), (float(second[2]), float(second[3]))
    values = orientation(a, b, c), orientation(a, b, e), orientation(c, e, a), orientation(c, e, b)
    if ((values[0] > 0 > values[1]) or (values[0] < 0 < values[1])) and ((values[2] > 0 > values[3]) or (values[2] < 0 < values[3])):
        return True
    return any(abs(value) < 1e-9 and point_on_segment(point, line) for value, point, line in (
        (values[0], c, first), (values[1], e, first), (values[2], a, second), (values[3], b, second)
    ))


def point_to_segment_distance(point: tuple[float, float], line: tuple[Any, ...]) -> float:
    x1, y1, x2, y2 = map(float, line[:4])
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(point[0] - x1, point[1] - y1)
    ratio = max(0.0, min(1.0, ((point[0] - x1) * dx + (point[1] - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(point[0] - (x1 + ratio * dx), point[1] - (y1 + ratio * dy))


def segment_distance(first: tuple[Any, ...], second: tuple[Any, ...]) -> float:
    if segments_intersect(first, second):
        return 0.0
    endpoints = ((float(first[0]), float(first[1])), (float(first[2]), float(first[3])))
    other_endpoints = ((float(second[0]), float(second[1])), (float(second[2]), float(second[3])))
    return min(*(point_to_segment_distance(point, second) for point in endpoints), *(point_to_segment_distance(point, first) for point in other_endpoints))


def acute_segment_angle(first: tuple[Any, ...], second: tuple[Any, ...]) -> float:
    first_dx, first_dy = float(first[2]) - float(first[0]), float(first[3]) - float(first[1])
    second_dx, second_dy = float(second[2]) - float(second[0]), float(second[3]) - float(second[1])
    cosine = abs(first_dx * second_dx + first_dy * second_dy) / (math.hypot(first_dx, first_dy) * math.hypot(second_dx, second_dy))
    return math.degrees(math.acos(min(1.0, cosine)))


def assert_leaders_do_not_obscure_geometry(drawing: Drawing) -> None:
    guarded_layers = {"EFFECTIVE", "OUTLINE", "PACK", "FRAME", "DOOR", "WINDOW", "HANDLE", "SEN55", "PORT"}
    geometry = [args for kind, args in drawing.entities if kind == "LINE" and args[-1] in guarded_layers]
    # 15°와 SVG 선 굵기(2)의 3배는 교차가 아니라 나란히 붙어 선을 가리는 경우만 잡는다.
    parallel_angle_limit, proximity_limit = 15.0, 6.0
    all_segments: list[tuple[int, int, tuple[Any, ...]]] = []
    for leader_index, leader in enumerate(drawing.leaders):
        for segment_index, segment in enumerate(leader["segments"]):
            all_segments.append((leader_index, segment_index, segment))
            for physical in geometry:
                angle = acute_segment_angle(segment, physical)
                distance = segment_distance(segment, physical)
                assert not (angle < parallel_angle_limit and distance <= proximity_limit), f"leader obscures drawing geometry: {leader['label']!r} angle={angle:g} distance={distance:g} {segment} vs {physical}"
    for index, (leader_a, segment_a, first) in enumerate(all_segments):
        for leader_b, segment_b, second in all_segments[index + 1:]:
            if leader_a == leader_b:
                continue
            assert not segments_intersect(first, second), f"leaders intersect: {drawing.leaders[leader_a]['label']!r} segment {segment_a} vs {drawing.leaders[leader_b]['label']!r} segment {segment_b}"


def assert_text_boxes_do_not_overlap_leaders(drawing: Drawing) -> None:
    for label, box in drawing.text_boxes:
        for leader in drawing.leaders:
            for segment_index, segment in enumerate(leader["segments"]):
                own_landing = box == leader["label_box"] and segment_index == len(leader["segments"]) - 1
                assert own_landing or not line_intersects_box(segment, box), f"text intersects leader: {label!r} {box} vs {leader['label']!r} {segment}"


def assert_leader_lengths_within_view_diagonal(drawing: Drawing) -> None:
    for leader in drawing.leaders:
        assert len(leader["segments"]) == 2, f"leader must have exactly two segments: {leader['label']!r}"
        diagonal_segment, landing_segment = leader["segments"]
        diagonal_dx = abs(float(diagonal_segment[2]) - float(diagonal_segment[0]))
        diagonal_dy = abs(float(diagonal_segment[3]) - float(diagonal_segment[1]))
        assert diagonal_dx > 0 and abs(diagonal_dx - diagonal_dy) < 1e-9, f"leader exit is not 45 degrees: {leader['label']!r}"
        assert float(landing_segment[1]) == float(landing_segment[3]) and abs(float(landing_segment[2]) - float(landing_segment[0])) == 60.0, f"leader landing is not the fixed short horizontal segment: {leader['label']!r}"
        view = leader["view_box"]
        diagonal = math.hypot(view[2] - view[0], view[3] - view[1])
        total = sum(math.hypot(float(segment[2]) - float(segment[0]), float(segment[3]) - float(segment[1])) for segment in leader["segments"])
        assert total <= diagonal, f"leader exceeds view diagonal: {leader['label']!r} {total:g} > {diagonal:g}"


def assert_text_boxes_do_not_overlap(drawing: Drawing) -> None:
    for index, (first_label, first) in enumerate(drawing.text_boxes):
        for second_label, second in drawing.text_boxes[index + 1 :]:
            try:
                assert_boxes_do_not_overlap(first, second)
            except AssertionError as error:
                raise AssertionError(
                    f"text labels overlap: {first_label!r} {first} vs {second_label!r} {second}"
                ) from error
        for kind, args in drawing.entities:
            if args[-1] == "LEADER":
                continue
            intersects = (kind == "LINE" and line_intersects_box(args, first)) or (kind == "CIRCLE" and circle_intersects_box(args, first))
            if intersects:
                raise AssertionError(f"text intersects geometry: {first_label!r} {first} vs {kind} {args}")


def dxf_pair(code: int, value: Any) -> str:
    return f"{code}\n{value}\n"


def write_dxf(d: Drawing, path: Path) -> None:
    parts = [dxf_pair(0, "SECTION"), dxf_pair(2, "HEADER"), dxf_pair(9, "$ACADVER"), dxf_pair(1, "AC1021"), dxf_pair(9, "$DWGCODEPAGE"), dxf_pair(3, "UTF-8"), dxf_pair(0, "ENDSEC")]
    parts += [dxf_pair(0, "SECTION"), dxf_pair(2, "TABLES"), dxf_pair(0, "TABLE"), dxf_pair(2, "LTYPE"), dxf_pair(70, 2)]
    parts += [dxf_pair(0, "LTYPE"), dxf_pair(2, "CONTINUOUS"), dxf_pair(70, 0), dxf_pair(3, "Solid line"), dxf_pair(72, 65), dxf_pair(73, 0), dxf_pair(40, 0.0)]
    parts += [dxf_pair(0, "LTYPE"), dxf_pair(2, "DASHED"), dxf_pair(70, 0), dxf_pair(3, "Dashed __ __"), dxf_pair(72, 65), dxf_pair(73, 2), dxf_pair(40, 12.0), dxf_pair(49, 8.0), dxf_pair(74, 0), dxf_pair(49, -4.0), dxf_pair(74, 0)]
    parts += [dxf_pair(0, "ENDTAB"), dxf_pair(0, "ENDSEC")]
    parts += [dxf_pair(0, "SECTION"), dxf_pair(2, "ENTITIES")]
    for kind, args in d.entities:
        if kind == "LINE":
            x1, y1, x2, y2, layer = args
            line_type, lineweight, _, _ = LAYER_STYLES.get(layer, ("CONTINUOUS", 18, 2.0, None))
            parts += [dxf_pair(0, "LINE"), dxf_pair(8, layer), dxf_pair(6, line_type), dxf_pair(370, lineweight), dxf_pair(10, x1), dxf_pair(20, y1), dxf_pair(30, 0), dxf_pair(11, x2), dxf_pair(21, y2), dxf_pair(31, 0)]
        elif kind == "CIRCLE":
            x, y, r, layer = args
            line_type, lineweight, _, _ = LAYER_STYLES.get(layer, ("CONTINUOUS", 18, 2.0, None))
            parts += [dxf_pair(0, "CIRCLE"), dxf_pair(8, layer), dxf_pair(6, line_type), dxf_pair(370, lineweight), dxf_pair(10, x), dxf_pair(20, y), dxf_pair(30, 0), dxf_pair(40, r)]
        elif kind == "TEXT":
            x, y, value, height, layer = args
            parts += [dxf_pair(0, "TEXT"), dxf_pair(8, layer), dxf_pair(10, x), dxf_pair(20, y), dxf_pair(30, 0), dxf_pair(40, height), dxf_pair(1, value)]
    parts += [dxf_pair(0, "ENDSEC"), dxf_pair(0, "EOF")]
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("".join(parts))


def write_svg(d: Drawing, path: Path) -> None:
    xs: list[float] = []
    ys: list[float] = []
    for kind, args in d.entities:
        if kind == "LINE":
            xs += [float(args[0]), float(args[2])]
            ys += [float(args[1]), float(args[3])]
        elif kind == "CIRCLE":
            radius = float(args[2])
            xs += [float(args[0]) - radius, float(args[0]) + radius]
            ys += [float(args[1]) - radius, float(args[1]) + radius]
        elif kind == "TEXT":
            xs.append(float(args[0]))
            xs.append(float(args[0]) + estimate_text_width(str(args[2]), float(args[3])))
            ys += [float(args[1]), float(args[1]) + float(args[3])]
    min_x, max_x = min(xs) - 180, max(xs) + 180
    min_y, max_y = min(ys) - 180, max(ys) + 180
    width, height = max_x - min_x, max_y - min_y
    svg_width, svg_height = width, height
    assert abs((svg_width / svg_height) - (width / height)) < 1e-12
    styles = {"PACK": "#1261a0", "FRAME": "#d97706", "OUTLINE": "#444", "HANDLE": "#c026d3", "DIM": "#7a3e00", "PORT": "#a02020", "SENSOR": "#087f5b", "SEN55": "#0f766e", "EFFECTIVE": "#111"}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {-max_y} {width} {height}" width="{svg_width}" height="{svg_height}">', '<rect x="-10000" y="-10000" width="20000" height="20000" fill="white"/>', '<g fill="none" stroke="#111" stroke-width="3" vector-effect="non-scaling-stroke">']
    for kind, args in d.entities:
        color = styles.get(str(args[-1]), "#111")
        _, _, stroke_width, dash_pattern = LAYER_STYLES.get(str(args[-1]), ("CONTINUOUS", 18, 2.0, None))
        dash = f' stroke-dasharray="{dash_pattern}"' if dash_pattern else ""
        if kind == "LINE":
            x1, y1, x2, y2, _ = args
            out.append(f'<line x1="{x1}" y1="{-y1}" x2="{x2}" y2="{-y2}" stroke="{color}" stroke-width="{stroke_width}"{dash}/>')
        elif kind == "CIRCLE":
            x, y, r, _ = args
            out.append(f'<circle cx="{x}" cy="{-y}" r="{r}" stroke="{color}" stroke-width="{stroke_width}"{dash}/>')
    out.append('</g><g font-family="Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif" fill="#111">')
    for kind, args in d.entities:
        if kind == "TEXT":
            x, y, value, size, layer = args
            out.append(f'<text x="{x}" y="{-y}" font-size="{size}" fill="{styles.get(layer, "#111")}">{html.escape(str(value))}</text>')
    out.append('</g></svg>')
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def validate_svg(path: Path) -> None:
    """Regression guard: declared SVG size must have the viewBox aspect ratio."""
    root = ET.parse(path).getroot()
    view_box = [float(value) for value in root.attrib["viewBox"].split()]
    declared_width = float(root.attrib["width"])
    declared_height = float(root.attrib["height"])
    view_width, view_height = view_box[2], view_box[3]
    assert abs((declared_width / declared_height) - (view_width / view_height)) < 1e-12, (
        "SVG declared size and viewBox aspect ratios differ: "
        f"{declared_width}x{declared_height} vs {view_width}x{view_height}"
    )
    print(
        "SVG validation OK: width/height aspect ratio matches viewBox "
        f"({declared_width:g} x {declared_height:g})"
    )


def validate_dxf(path: Path, expected_entities: int) -> None:
    text = path.read_text(encoding="utf-8")
    for section in ("HEADER", "TABLES", "ENTITIES"):
        if f"2\n{section}\n" not in text:
            raise ValueError(f"DXF section missing: {section}")
    if not text.endswith("0\nEOF\n"):
        raise ValueError("DXF EOF missing")
    if "1\nAC1021\n" not in text or "3\nUTF-8\n" not in text:
        raise ValueError("DXF must declare AC1021 and UTF-8")
    entity_count = sum(text.count(f"0\n{name}\n") for name in ("LINE", "CIRCLE", "TEXT"))
    if entity_count != expected_entities:
        raise ValueError(f"DXF entity count mismatch: {entity_count} != {expected_entities}")
    print(f"DXF validation OK: AC1021 UTF-8, HEADER/TABLES/ENTITIES/EOF, {entity_count} entities")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, default=DEFAULT_PARAMS)
    args = parser.parse_args()
    p = load_params(args.params)
    dependent = dependent_parameters(p)
    if dependent:
        print(f"Dependent parameters ({len(dependent)}):")
        for item in dependent:
            print(f"- {item}")
    drawing, m = build(p)
    for first, second in (("notes", "title"),):
        assert_boxes_do_not_overlap(drawing.regions[first], drawing.regions[second])
    print("Layout validation OK: 주기/표제란 2개 영역은 서로 겹치지 않음")
    assert_box_contains(drawing.regions["door"], drawing.regions["pack_front"])
    chamber, door = drawing.regions["chamber_front"], drawing.regions["door"]
    assert chamber[0] <= door[0] and chamber[1] <= door[1] and chamber[2] >= door[2] and chamber[3] >= door[3]
    print("Door validation OK: 도어 개구 contains the pack and remains inside the chamber")
    assert_vertical_overlap(drawing.regions["window"], drawing.regions["pack_front"])
    print("Window validation OK: 관찰창 overlaps the pack front height interval")
    assert_box_contains(drawing.regions["door"], drawing.regions["window"])
    print("Window/door validation OK: 관찰창 is fully contained by the door opening")
    assert_box_contains(drawing.regions["door"], drawing.regions["handle"])
    assert_boxes_do_not_overlap(drawing.regions["handle"], drawing.regions["window"])
    print("Handle validation OK: 핸들은 도어 안에 있고 관찰창과 겹치지 않음")
    assert drawing.regions["frame_front"][3] == drawing.regions["pack_front"][1]
    assert drawing.regions["frame_side"][3] == drawing.regions["pack_side"][1]
    print("Frame validation OK: 정면·측면 프레임 상면과 팩 저면 일치")
    assert drawing.regions["cable_plate"][1] >= drawing.regions["frame_side"][3]
    print("Cable/frame validation OK: 케이블 관통 포트 최저점은 프레임 상면 이상")
    assert m["outer_w"] - m["w"] == 2 * m["wall"] and m["outer_d"] - m["d"] == 2 * m["wall"] and m["outer_h"] - m["h"] == 2 * m["wall"]
    print("Outline validation OK: 외형선은 내부 유효선에서 판 두께만큼 정확히 오프셋")
    sen55_lines = [args for kind, args in drawing.entities if kind == "LINE" and args[-1] == "SEN55"]
    assert len(sen55_lines) % 4 == 0 and len(sen55_lines) // 4 == len(p["sensor_points"])
    print(f"Sensor marker validation OK: SEN55 레이어 사각형 {len(sen55_lines) // 4}개가 sensor_points {len(p['sensor_points'])}개와 일치")
    assert_text_boxes_do_not_overlap(drawing)
    print(f"Text/geometry validation OK: {len(drawing.text_boxes)} label boxes do not overlap text, LINE, or CIRCLE")
    assert_leaders_do_not_obscure_geometry(drawing)
    print(f"Leader/geometry validation OK: {len(drawing.leaders)} dogleg leaders do not obscure protected drawing geometry")
    assert_text_boxes_do_not_overlap_leaders(drawing)
    print("Leader validation OK: 지시선 상호 교차와 텍스트 상자 침범 없음")
    assert_leader_lengths_within_view_diagonal(drawing)
    print("Leader length validation OK: 모든 지시선 길이는 해당 뷰 대각선 이하")
    write_dxf(drawing, DXF_PATH)
    write_svg(drawing, SVG_PATH)
    validate_dxf(DXF_PATH, len(drawing.entities))
    validate_svg(SVG_PATH)
    print(f"Generated {DXF_PATH.name} and {SVG_PATH.name}")
    print(f"Fixed dimensions: internal {m['w']:.0f} x {m['d']:.0f} x {m['h']:.0f} mm; outer {m['outer_w']:.0f} x {m['outer_d']:.0f} x {m['outer_h']:.0f} mm")


if __name__ == "__main__":
    main()
