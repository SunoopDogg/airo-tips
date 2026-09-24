"""더미 팩.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. ESS 배터리 모듈 하나의 외형만 본뜬 상자이고, 높이가 가장 작은 변이 되도록 눕혀 받침 레일 위에 놓인다.
"""

from cadgen import build123d as bd
from cadgen import srgb
from cadgen import step

from params import pack_D, pack_H, pack_W, pack_x0, pack_y0, pack_z0
from style import dummy_pack


@step(out="../step/pack.step")
def pack():
    body = bd.Box(pack_W, pack_D, pack_H, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    body = body.moved(bd.Location((pack_x0, pack_y0, pack_z0)))
    body.label = "pack"
    body.color = srgb(dummy_pack)
    # 솔리드 하나를 그대로 반환하면 STEP에 label이 남지 않으므로 compound로 감싼다.
    return bd.Compound(children=[body])


if __name__ == "__main__":
    pack()
