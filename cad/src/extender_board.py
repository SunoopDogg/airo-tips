"""P82B715 센서측 기판.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. ext_W × ext_D × ext_T(30 × 20 × 1.6) 판 3장이고, 각각 M3 구멍 ext_hole_dia(Ø3.2) 2개를 긴 변 중심선 위, 짧은 변에서 ext_hole_edge(4)에 낸다. 판과 구멍만 그리고 소자는 그리지 않는다(`cad/chamber.md` ext_W ext_D 행, 사용자 결정 2026-10-07).

판은 기판 자기 좌표(외곽 모서리가 원점, x가 긴 변 ext_W, y가 짧은 변 ext_D, z가 두께 ext_T)에 그린 뒤 `sen55_bracket.extender_location(i)`로 SEN55 브래킷 i의 뒤 벽 바깥면에 놓는다. 그 함수의 정의대로 z = 0 면이 뒤 벽 바깥면에 닿고, 구멍 중심 (ext_hole_edge, ext_D/2) · (ext_W − ext_hole_edge, ext_D/2)이 브래킷의 M3 통과 구멍과 같은 축에 온다. 자세 함수를 가져오므로 `sen55_bracket.py`가 바뀌면 이 모델도 다시 빌드된다.

label: extender_1, extender_2, extender_3 — 각각 솔리드 하나이고 번호는 브래킷(bracket_1 앞, bracket_2 뒤 왼쪽, bracket_3 뒤 오른쪽)과 같다.
"""

from __future__ import annotations

from cadgen import build123d as bd
from cadgen import srgb
from cadgen import step

from params import (
    ext_D,
    ext_hole_dia,
    ext_hole_edge,
    ext_hole_N,
    ext_T,
    ext_W,
    sen_N,
)
from sen55_bracket import extender_location
from style import pcb


def board_local() -> bd.Solid:
    """기판 자기 좌표의 판 하나."""
    body = bd.Solid.make_box(ext_W, ext_D, ext_T)
    for hx in (ext_hole_edge, ext_W - ext_hole_edge):
        body = body - bd.Solid.make_cylinder(ext_hole_dia / 2, ext_T + 2, plane=bd.Plane(origin=(hx, ext_D / 2, -1), z_dir=(0, 0, 1)))
    solids = body.solids()
    if not body.is_valid or len(solids) != 1:
        raise ValueError(f"기판 솔리드가 올바르지 않다 (solids {len(solids)})")
    return solids[0]


@step(out="../step/extender_board.step")
def extender_board():
    assert ext_hole_N == 2 and sen_N == 3
    assert ext_hole_dia / 2 < ext_hole_edge < ext_W / 2 - ext_hole_dia / 2, "구멍이 판 가장자리나 서로에 걸린다"
    local = board_local()
    boards = []
    for i in range(1, sen_N + 1):
        b = local.moved(extender_location(i))
        b.label = f"extender_{i}"
        b.color = srgb(pcb)
        boards.append(b)
    return bd.Compound(children=boards)


if __name__ == "__main__":
    extender_board()
