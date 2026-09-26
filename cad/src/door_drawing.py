"""도어의 치수 도면.

`door()`를 불러 label `door`인 아크릴 판을 꺼내, 챔버 바깥에서 본 앞면을 `front` 뷰 하나로 그린다. 주 뷰는 같은 판의 가공 도면(`door_dxf.py`)과 같은 면 · 같은 방향이고, 판 외곽의 왼쪽 아래 모서리가 DXF 원점이다(cad/CLAUDE.md). 판에 구멍이 없으므로 치수는 `overall()`의 폭 · 높이뿐이고, 값은 cadgen이 형상에서 잰다. 두께는 도곽의 재질 칸이 담는다.

뷰 자리는 판의 bounding box에서 계산해, 뷰가 용지 가로 가운데에 오고 아래쪽이 노트 · 도곽 위로 떨어지게 둔다.
"""

from __future__ import annotations

from cadgen.eng_drawing import Sheet, eng_drawing

from door import door
from params import t_door

SCALE = 0.2  # 1:5
ORIGIN = (81.0, 113.0)  # 뷰 왼쪽 아래 모서리의 도면 위치 mm
MATERIAL = f"ACRYLIC {t_door:g} mm"
NOTES = ["HARDWARE MOUNTING HOLES NOT INCLUDED.", "OUTSIDE FACE SHOWN. DATUM: LOWER LEFT CORNER (= DXF ORIGIN)."]


@eng_drawing(out="../pdf/door.pdf")
def door_drawing():
    plate = next(p for p in door().children if p.label == "door")
    size = plate.bounding_box().size  # front 뷰의 가로가 챔버 x, 세로가 챔버 z
    sheet = Sheet("A3", scale=SCALE, title="DOOR", material=MATERIAL, revision="A",
                  general_tolerance="ISO 2768-m", notes=NOTES)
    view = sheet.view(plate, "front", at=(ORIGIN[0] + size.X * SCALE / 2, ORIGIN[1] + size.Z * SCALE / 2))
    view.overall()
    return sheet


if __name__ == "__main__":
    door_drawing()
