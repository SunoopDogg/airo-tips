"""P82B715 센서측 기판의 치수 도면.

기판 3장(extender_1 · extender_2 · extender_3)이 같은 형상이므로 도면은 하나다(cad/CLAUDE.md). `extender_board()`를 불러 label `extender_1`인 기판 솔리드만 꺼내, 브래킷에서 먼 큰 면을 `right` 뷰 하나로 그린다. `extender_1`의 그 면은 법선이 챔버 +x이고, `right` 뷰는 +x에서 보며 오른쪽이 챔버 +y, 위쪽이 +z라 긴 변 30이 가로다. 같은 판의 가공 도면(`extender_board_dxf.py`)과 같은 면 · 같은 방향이고, 판 외곽의 왼쪽 아래 모서리(bounding box의 최소 y · 최소 z)가 DXF 원점이다. 치수는 `overall()`의 폭 · 높이, 첫 구멍 중심이 기준점 쪽 변(왼쪽 · 아래)에서 떨어진 거리 가로 · 세로 하나씩, 구멍 사이 가로 하나와 구멍 표기 하나다. 기준점은 기판의 bounding box에서, 구멍 점과 수 · 지름은 params.py의 기판 상수에서 얻고, 값은 cadgen이 형상에서 잰다. 두께는 도곽의 재질 칸이 담는다.

치수 줄의 배치는 cadgen의 동작에 맞춘다. 위쪽 · 왼쪽은 `overall()`이 맨 바깥 줄을 쓰므로, 그 두 쪽 첫 줄에는 판 변에서 잰 구멍 거리만 둔다. 가로 거리는 왼쪽 위 모서리에서 재어 치수선이 뷰 위로 나가게 하고, 세로 거리는 기준점 모서리에서 잰다. 두 점이 가로 4 · 세로 10만큼 떨어져 있어 cadgen이 고르는 방향과 재려는 방향이 다를 수 있으므로 방향을 준다. 구멍 사이 거리는 아래쪽 첫 줄에 둔다. 구멍 표기는 오른쪽 구멍에서 오른쪽으로 낸다.

뷰 자리는 기판의 bounding box에서 계산해, 뷰가 용지 가로 가운데에 오고 아래쪽이 노트 · 도곽 위로 떨어지게 둔다.
"""

from __future__ import annotations

from cadgen.eng_drawing import Sheet, eng_drawing

from extender_board import extender_board
from params import ext_D, ext_hole_dia, ext_hole_edge, ext_hole_N, ext_T, ext_W

BOARD = "extender_1"  # 같은 형상 3장 중 그리는 기판
SCALE = 2.0  # 2:1
ROW = 12.0  # 치수 줄 하나의 폭(도면 mm). cadgen이 자리를 정하지 않은 치수를 쌓는 간격과 같다
VIEW_Y0 = 112.0  # 뷰 아래 변의 도면 높이 mm. 뷰 이름 아래와 노트 위, 30 치수 위와 틀 위 변 사이가 비슷하게 남는 높이
MATERIAL = f"PCB {ext_T:g} mm"
NOTES = ["VIEW FROM SIDE AWAY FROM BRACKET. DATUM: LOWER LEFT CORNER (= DXF ORIGIN).", "QUANTITY: 3 (IDENTICAL)."]


@eng_drawing(out="../pdf/extender_board.pdf")
def extender_board_drawing():
    board = next(p for p in extender_board().children if p.label == BOARD)
    bb = board.bounding_box()  # right 뷰의 가로가 챔버 y, 세로가 챔버 z, 보이는 면이 x 최대

    def face(u: float, v: float) -> tuple[float, float, float]:
        """보이는 면(x 최대) 위에서 기준점으로부터 오른쪽 u, 위로 v인 점."""
        return (bb.max.X, bb.min.Y + u, bb.min.Z + v)

    sheet = Sheet("A4", scale=SCALE, title="P82B715 EXTENDER PCB", material=MATERIAL, revision="A",
                  general_tolerance="ISO 2768-m", notes=NOTES)
    view = sheet.view(board, "right", at=(sheet.width / 2, VIEW_Y0 + bb.size.Z * SCALE / 2))
    view.overall()

    hu0, hu1 = ext_hole_edge, ext_W - ext_hole_edge  # 구멍 중심의 가로 위치, 긴 변 중심선 위
    hv = ext_D / 2  # 구멍 중심의 세로 위치
    # cadgen의 offset은 두 점 가운데 바깥쪽 점에서 잰 도면 mm다. 반올림은 줄 수를 세는 cadgen의 `//`가 부동소수 오차로 한 줄 적게 세지 않게 한다
    # 위쪽 첫 줄: 첫 구멍 중심이 왼쪽 변에서 떨어진 거리(왼쪽 위 모서리 · 구멍)
    view.dim(face(0, ext_D), face(hu0, hv), orientation="h", offset=round(ROW, 6))
    # 왼쪽 첫 줄: 첫 구멍 중심이 아래 변에서 떨어진 거리(왼쪽 아래 모서리 · 구멍)
    view.dim(face(0, 0), face(hu0, hv), orientation="v", offset=round(-ROW, 6))
    # 아래쪽 첫 줄: 구멍 사이 가로
    view.dim(face(hu0, hv), face(hu1, hv), orientation="h", offset=round(-(ROW + hv * SCALE), 6))
    # 구멍 표기: 오른쪽 구멍에서 오른쪽으로
    view.hole(face(hu1, hv), ext_hole_dia, thru=True, count=ext_hole_N)
    return sheet


if __name__ == "__main__":
    extender_board_drawing()
