"""도어를 연 조립품.

src/assembly.py의 build_assembly(OPEN_ANGLE)을 그대로 돌려준다. 좌표계·개체 구조·label은 step/assembly.step과 같고, 도어·손잡이·도어 쪽 경첩 날개 3개가 너클 축을 중심으로 OPEN_ANGLE만큼 돌았고 토글 클램프 2개는 풀린 자세다(assembly.py 맨 위 주석). assembly.py의 DOOR_ANGLE을 바꾸지 않고도 솔리드웍스에서 열린 모습을 바로 볼 수 있게 따로 둔다.

assembly.py를 불러 쓰므로 조립품을 다시 빌드할 때 함께 실행한다. cad/ 안에서 `./cadgen python src/assembly_door_open.py`(저장소 루트에서는 `cad/cadgen python cad/src/assembly_door_open.py`).
"""

from cadgen import step

from assembly import DOOR_ANGLE_MAX, build_assembly

OPEN_ANGLE = DOOR_ANGLE_MAX  # 도는 동안의 간섭을 확인한 범위의 끝(90°)


@step(out="../step/assembly_door_open.step")
def assembly_door_open():
    return build_assembly(OPEN_ANGLE)


if __name__ == "__main__":
    assembly_door_open()
