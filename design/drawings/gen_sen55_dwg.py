#!/usr/bin/env python3
"""Generate the SEN55 three-view detail drawing from sen55_params.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gen_chamber_dwg import (
    Drawing,
    add_leader_label,
    assert_boxes_do_not_overlap,
    assert_leaders_do_not_obscure_geometry,
    assert_leader_lengths_within_view_diagonal,
    assert_text_boxes_do_not_overlap,
    assert_text_boxes_do_not_overlap_leaders,
    estimate_text_width,
    validate_dxf,
    validate_svg,
    write_dxf,
    write_svg,
)


ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "sen55_params.json"
DXF_PATH = ROOT / "sen55.dxf"
SVG_PATH = ROOT / "sen55.svg"


def load_params(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data) != {"meta", "module"}:
        raise ValueError("sen55 params must contain exactly meta and module sections")
    for name, item in data["module"].items():
        if not isinstance(item, dict) or not {"value", "unit", "status", "source"} <= item.keys():
            raise ValueError(f"invalid parameter record: module.{name}")
        allowed = {"unknown"} if name == "air_inlet_location" else {"fixed"}
        if item["status"] not in allowed:
            raise ValueError(f"invalid status: module.{name}")
        if item["status"] == "fixed" and item["value"] is None:
            raise ValueError(f"fixed value cannot be null: module.{name}")
        if name == "air_inlet_location" and item["value"] is not None:
            raise ValueError("air inlet location must remain unknown until supported by a source")
    return data


def numeric(module: dict[str, Any], name: str) -> float:
    value = module[name]["value"]
    if not isinstance(value, (int, float)):
        raise ValueError(f"numeric value required: module.{name}")
    return float(value)


def build(params: dict[str, Any]) -> Drawing:
    module, meta = params["module"], params["meta"]
    scale = 10.0  # sheet-layout scale only; title block declares NTS
    length = numeric(module, "length")
    width = numeric(module, "width")
    height = numeric(module, "height")
    side_width = numeric(module, "side_width")
    fan_diameter = numeric(module, "fan_opening_diameter")
    label_width = numeric(module, "label_width")
    label_height = numeric(module, "label_height")
    d = Drawing()

    fx, fy = 300.0, 1250.0
    fw, fh = length * scale, width * scale
    front = (fx, fy, fx + fw, fy + fh)
    d.rect(fx, fy, fw, fh, "SEN55")
    d.circle(fx + fw / 2, fy + fh / 2, fan_diameter * scale / 2, "SEN55")
    d.text(fx, fy + fh + 90, "배출구측 정면", 28)
    d.dim_h(fx, fx + fw, fy - 75, f"{length:g} {module['length_tolerance']['value']}")
    d.dim_v(fy, fy + fh, fx - 75, f"{width:g} ({module['width_tolerance']['value']})", "left")
    add_leader_label(d, fx + fw / 2 + fan_diameter * scale / 2, fy + fh / 2, f"팬 개구 Ø{fan_diameter:g} (참조)", front, "right", 35, 1)

    sx, sy = 1150.0, fy
    sw, sh = height * scale, width * scale
    side = (sx, sy, sx + sw, sy + sh)
    d.rect(sx, sy, sw, sh, "SEN55")
    d.line(sx + sw, sy, sx + sw, sy + sh, "CONNECTOR")
    d.text(sx, sy + sh + 90, "측면", 28)
    d.dim_h(sx, sx + sw, sy - 75, f"{height:g} {module['height_tolerance']['value']}")
    d.dim_v(sy, sy + side_width * scale, sx - 75, f"측면 폭 {side_width:g} {module['side_width_tolerance']['value']}", "left")
    add_leader_label(d, sx + sw, sy + sh * .62, f"커넥터 구역: {module['connector']['value']}", side, "right", 35, 1)
    add_leader_label(d, sx + sw, sy + sh * .48, f"위치: {module['connector_location']['value']}", side, "right", 85, -1)

    rx, ry = 300.0, 450.0
    rw, rh = length * scale, width * scale
    rear = (rx, ry, rx + rw, ry + rh)
    d.rect(rx, ry, rw, rh, "SEN55")
    label_x = rx + (rw - label_width * scale) / 2
    label_y = ry + rh - label_height * scale
    d.rect(label_x, label_y, label_width * scale, label_height * scale, "LABEL")
    d.text(rx, ry + rh + 90, "배출구 반대쪽 면", 28)
    add_leader_label(d, label_x + label_width * scale, label_y + label_height * scale / 2, f"라벨 {label_width:g} x {label_height:g}", rear, "right", 35, -1)

    notes = [
        "주기",
        "1. 공기 흡입구 위치는 데이터시트 미상이며 이 도면에 표시하지 않는다.",
        "2. 동작 권장 10 ~ 40 °C / 20 ~ 80 %RH; 절대 -10 ~ 50 °C / 0 ~ 90 %RH 비결로.",
        "3. 결로 조건에 어떤 경우에도 노출 금지.",
        "4. 시험 조건 ⑤ 목표 60 ℃는 절대 최대 50 °C 초과. 이 상태로 수행하면 소자가 손상된다.",
        "5. I2C 주소 0x69 고정. 3대는 멀티플렉서 또는 버스 분리 필요(미결정).",
        "6. 배선 10 cm 미만 권장 또는 차폐 케이블 사용.",
        "7. 금속 실드는 내부 GND와 연결되며 등전위 미확보 시 과열 위험.",
        "8. 측정 주기 1 Hz 고정.",
        "9. 팬 자동 청소 기본 1주. 전원 차단 시 카운터 리셋되므로 주 1회 수동 실행.",
        f"10. 품번 {module['part_number']['value']}, Article Number {module['article_number']['value']}, 무게 {module['weight']['value']:g} g {module['weight_tolerance']['value']}.",
    ]
    nx, notes_bottom, spacing = 1150.0, 430.0, 38.0
    notes_top = notes_bottom + (len(notes) - 1) * spacing + 30
    for index, line in enumerate(notes):
        d.text(nx, notes_top - 30 - index * spacing, line, 28 if index == 0 else 18, "NOTE")
    notes_width = max(estimate_text_width(line, 28 if index == 0 else 18) for index, line in enumerate(notes))
    d.regions["notes"] = (nx, notes_bottom, nx + notes_width, notes_top)

    tbx, tby, tbw, tbh = 1150.0, 100.0, 950.0, 220.0
    d.regions["title"] = (tbx, tby, tbx + tbw, tby + tbh)
    assert_boxes_do_not_overlap(d.regions["notes"], d.regions["title"])
    d.rect(tbx, tby, tbw, tbh, "TITLE")
    d.line(tbx, tby + 75, tbx + tbw, tby + 75, "TITLE")
    d.line(tbx, tby + 145, tbx + tbw, tby + 145, "TITLE")
    d.text(tbx + 15, tby + 165, meta["drawing_title"], 25, "TITLE")
    d.text(tbx + 15, tby + 98, f"도면번호: {meta['drawing_number']}  REV: {meta['revision']}", 22, "TITLE")
    d.text(tbx + 15, tby + 30, f"축척: {meta['scale']}  단위: {meta['unit']}  작성일: {meta['date']}", 22, "TITLE")
    return d


def main() -> None:
    params = load_params(PARAMS_PATH)
    drawing = build(params)
    assert_boxes_do_not_overlap(drawing.regions["notes"], drawing.regions["title"])
    print("Layout validation OK: SEN55 주기와 표제란은 겹치지 않음")
    assert_text_boxes_do_not_overlap(drawing)
    print(f"Text/geometry validation OK: {len(drawing.text_boxes)} label boxes are clear")
    assert_leaders_do_not_obscure_geometry(drawing)
    assert_text_boxes_do_not_overlap_leaders(drawing)
    print(f"Leader validation OK: {len(drawing.leaders)} leaders are clear")
    assert_leader_lengths_within_view_diagonal(drawing)
    print("Leader length validation OK: all leaders are within their view diagonal")
    write_dxf(drawing, DXF_PATH)
    write_svg(drawing, SVG_PATH)
    validate_dxf(DXF_PATH, len(drawing.entities))
    validate_svg(SVG_PATH)
    print(f"Generated {DXF_PATH.name} and {SVG_PATH.name}")


if __name__ == "__main__":
    main()
