"""도어 밀폐재.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 앞면 패널 바깥면에 붙이는 EPDM 스펀지 사각 링 하나이고, 단면은 폭 gasket_W × 두께 gasket_T, 모서리는 각지게 둔다(사용자 결정 2026-10-07). 링은 도어 판이 개구 둘레에 겹치는 폭 door_overlap의 가운데에 놓인다.

압착 전 두께로 그린다. 뒷면이 앞면 패널 바깥면, 앞면이 도어 판 뒷면에 닿는다.
"""

from cadgen import build123d as bd
from cadgen import step

from params import (
    gasket_T,
    gasket_W,
    gasket_in_x0,
    gasket_in_x1,
    gasket_in_z0,
    gasket_in_z1,
    gasket_out_x0,
    gasket_out_x1,
    gasket_out_z0,
    gasket_out_z1,
    gasket_y0,
    gasket_y1,
)


def _box(x0, x1, y0, y1, z0, z1):
    box = bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    return box.moved(bd.Location((x0, y0, z0)))


@step(out="../step/door_gasket.step")
def door_gasket():
    assert abs((gasket_y1 - gasket_y0) - gasket_T) < 1e-6, "밀폐재 y 구간이 gasket_T와 다르다"
    for out_lo, in_lo, in_hi, out_hi in (
        (gasket_out_x0, gasket_in_x0, gasket_in_x1, gasket_out_x1),
        (gasket_out_z0, gasket_in_z0, gasket_in_z1, gasket_out_z1),
    ):
        assert abs((in_lo - out_lo) - gasket_W) < 1e-6 and abs((out_hi - in_hi) - gasket_W) < 1e-6, "링 단면 폭이 gasket_W와 다르다"
    outer = _box(gasket_out_x0, gasket_out_x1, gasket_y0, gasket_y1, gasket_out_z0, gasket_out_z1)
    inner = _box(gasket_in_x0, gasket_in_x1, gasket_y0, gasket_y1, gasket_in_z0, gasket_in_z1)
    body = outer - inner
    body.label = "door_gasket"
    # 솔리드 하나를 그대로 반환하면 STEP에 label이 남지 않으므로 compound로 감싼다.
    return bd.Compound(children=[body])


if __name__ == "__main__":
    door_gasket()
