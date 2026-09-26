"""전장 기판의 치수 도면.

`control_board()`를 불러 label `pcb`인 기판 솔리드만 꺼내, 소자를 싣는 윗면을 `top` 뷰 하나로 그린다. ESP32 모듈과 USB-C 블록은 그리지 않는다(기판 외곽과 구멍의 도면이다). 주 뷰는 같은 판의 가공 도면(`control_board_dxf.py`)과 같은 면 · 같은 방향이고 — `top` 뷰는 위쪽이 챔버 +y, 오른쪽이 +x라 긴 변 80이 가로다 — 판 외곽의 왼쪽 아래 모서리가 DXF 원점이다(cad/CLAUDE.md). 치수는 `overall()`의 폭 · 높이, 구멍 중심이 기준점 쪽 변(왼쪽 · 아래)에서 떨어진 거리 가로 · 세로 하나씩, 구멍 사이 가로 · 세로 하나씩과 구멍 표기 하나다. 점과 구멍 수 · 지름은 params.py의 기판 상수에서, 값은 cadgen이 형상에서 잰다. 두께는 도곽의 재질 칸이 담는다.

치수 줄의 배치는 cadgen의 동작에 맞춘다. 위쪽 · 왼쪽은 `overall()`이 맨 바깥 줄을 쓰므로, 그 두 쪽 첫 줄에는 판 변에서 잰 구멍 거리만 둔다(1:1에서 4 mm라 화살표가 보조선 바깥으로 나가므로 이웃 치수와 한 줄에 잇지 않는다). 구멍 사이 거리는 아래쪽 · 오른쪽 첫 줄에 둔다. 판 변에서 잰 거리의 두 점은 가로 · 세로로 같은 4만큼 떨어져 있어 어느 쪽 치수인지 형상으로 정해지지 않으므로 방향을 준다. 구멍 표기는 오른쪽 위 구멍에서 오른쪽 치수 바깥으로 낸다.

A4 2:1은 뷰(160 × 120)와 위 · 아래 치수 줄, 뷰 이름을 더하면 노트 위 빈 높이를 넘으므로 명세의 첫 축척 1:1로 그린다. 뷰 자리는 기판의 bounding box에서 계산해, 뷰가 용지 가로 가운데에 오고 아래쪽이 노트 · 도곽 위로 떨어지게 둔다.
"""

from __future__ import annotations

from cadgen.eng_drawing import Sheet, eng_drawing

from control_board import control_board
from params import pcb_hole_dia, pcb_hole_x, pcb_hole_y, pcb_T, pcb_x0, pcb_x1, pcb_y0, pcb_y1, pcb_z1

SCALE = 1.0  # 1:1
ROW = 12.0  # 치수 줄 하나의 폭(도면 mm). cadgen이 자리를 정하지 않은 치수를 쌓는 간격과 같다
ORIGIN = (108.5, 100.0)  # 뷰 왼쪽 아래 모서리의 도면 위치 mm
MATERIAL = f"PCB {pcb_T:g} mm"
NOTES = ["VIEW FROM COMPONENT SIDE. DATUM: LOWER LEFT CORNER (= DXF ORIGIN)."]


def face(x: float, y: float) -> tuple[float, float, float]:
    """소자면(z = pcb_z1, top 뷰가 보는 면) 위의 점."""
    return (x, y, pcb_z1)


@eng_drawing(out="../pdf/control_board.pdf")
def control_board_drawing():
    pcb = next(p for p in control_board().children if p.label == "pcb")
    size = pcb.bounding_box().size  # top 뷰의 가로가 챔버 x, 세로가 챔버 y
    sheet = Sheet("A4", scale=SCALE, title="CONTROL BOARD PCB", material=MATERIAL, revision="A",
                  general_tolerance="ISO 2768-m", notes=NOTES)
    view = sheet.view(pcb, "top", at=(ORIGIN[0] + size.X * SCALE / 2, ORIGIN[1] + size.Y * SCALE / 2))
    view.overall()

    hx0, hx1 = min(pcb_hole_x), max(pcb_hole_x)
    hy0, hy1 = min(pcb_hole_y), max(pcb_hole_y)
    # cadgen의 offset은 두 점 가운데 바깥쪽 점에서 잰 도면 mm다. 반올림은 줄 수를 세는 cadgen의 `//`가 부동소수 오차로 한 줄 적게 세지 않게 한다
    # 위쪽 첫 줄: 구멍 중심이 왼쪽 변에서 떨어진 거리(왼쪽 위 모서리 · 구멍)
    view.dim(face(pcb_x0, pcb_y1), face(hx0, hy1), orientation="h", offset=round(ROW, 6))
    # 왼쪽 첫 줄: 구멍 중심이 아래 변에서 떨어진 거리(왼쪽 아래 모서리 · 구멍)
    view.dim(face(pcb_x0, pcb_y0), face(hx0, hy0), orientation="v", offset=round(-ROW, 6))
    # 아래쪽 첫 줄: 구멍 사이 가로(아래 줄 두 구멍)
    view.dim(face(hx0, hy0), face(hx1, hy0), orientation="h", offset=round(-(ROW + (hy0 - pcb_y0) * SCALE), 6))
    # 오른쪽 첫 줄: 구멍 사이 세로(오른쪽 열 두 구멍)
    view.dim(face(hx1, hy0), face(hx1, hy1), orientation="v", offset=round(ROW + (pcb_x1 - hx1) * SCALE, 6))
    # 구멍 표기: 오른쪽 위 구멍에서 오른쪽 치수 바깥으로
    view.hole(face(hx1, hy1), pcb_hole_dia, thru=True, count=len(pcb_hole_x) * len(pcb_hole_y))
    return sheet


if __name__ == "__main__":
    control_board_drawing()
