"""챔버 공유 치수.

좌표는 챔버 좌표계다. 원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, 단위 mm, 각도 도(°).

`cad/chamber.md` "치수 대장" 표의 fixed 값과 수치가 적힌 dependent 값을 옮긴다. fixed는 숫자로, dependent는 다른 상수로 계산하는 식으로 쓴다. 줄마다 주석의 첫머리는 chamber.md 표의 행 이름(변수명이 있으면 변수명)이다. unknown 행(밀폐 등급, cable_dia)은 넣지 않는다.
"""

import math

# --- 더미 팩 외형 ---
pack_W = 1130.0  # pack_W — 더미 팩 폭 (fixed, 사용자 결정 2026-10-06)
pack_D = 810.0  # pack_D — 더미 팩 깊이 (fixed, 사용자 결정 2026-10-06)
pack_H = 260.0  # pack_H — 더미 팩 높이, 눕혀 놓아 가장 작은 변 (fixed, 사용자 결정 2026-10-06)
pack_N = 1  # pack_N — 더미 팩 수량 (fixed, 사용자 결정 2026-10-06)

# --- 받침 높이와 팩 둘레 여유 ---
rail_H = 100.0  # rail_H — 바닥에서 팩 밑면까지 받침 높이 (fixed, 사용자 결정 2026-10-06)
clr_front = 80.0  # clr_front — 팩 앞 여유 (fixed, 사용자 결정 2026-10-06)
clr_back = 80.0  # clr_back — 팩 뒤 여유 (fixed, 사용자 결정 2026-10-06)
clr_left = 100.0  # clr_left — 팩 왼쪽(배기) 여유 (fixed, 사용자 결정 2026-10-06)
clr_right = 150.0  # clr_right — 팩 오른쪽(주입) 여유 (fixed, 사용자 결정 2026-10-06)
clr_top = 300.0  # clr_top — 팩 위 여유 (fixed, 사용자 결정 2026-10-06)
clr_bottom = rail_H  # clr_bottom — 팩 아래 여유 (dependent, rail_H와 같다)

# --- 내부 유효 치수 ---
W_in = clr_left + pack_W + clr_right  # W_in — 내부 유효 폭 (dependent, 1380)
D_in = clr_front + pack_D + clr_back  # D_in — 내부 유효 깊이 (dependent, 970)
H_in = rail_H + pack_H + clr_top  # H_in — 내부 유효 높이 (dependent, 660)

# --- 팩 위치 (원점 기준 팩 외곽) ---
pack_x0 = clr_left  # 팩 위치 — x 시작 (dependent, 100)
pack_x1 = pack_x0 + pack_W  # 팩 위치 — x 끝 (dependent, 1230)
pack_y0 = clr_front  # 팩 위치 — y 시작 (dependent, 80)
pack_y1 = pack_y0 + pack_D  # 팩 위치 — y 끝 (dependent, 890)
pack_z0 = clr_bottom  # 팩 위치 — z 시작 (dependent, 100)
pack_z1 = pack_z0 + pack_H  # 팩 위치 — z 끝 (dependent, 360)

# --- 골조 ---
prof_W = 30.0  # prof_W — 골조 프로파일 단면 한 변 (fixed, 3030 규격, 사용자 결정 2026-10-06)
profile_id = "profile_3030_b_slot8"  # 사용자가 결정한 형상 — 3030 B형 슬롯 8 단면의 step.parts id (2026-10-07)
corner_bracket_id = "extrusion_3030_slot8_inside_corner_bracket_standard"  # 사용자가 결정한 형상 — 골조 이음 안쪽 코너 브래킷의 step.parts id (2026-10-07)
frame_post_N = 4  # 골조 부재 — 세로재 개수 (dependent)
frame_beam_x_N = 4  # 골조 부재 — 폭 방향 수평재 개수 (dependent)
frame_beam_y_N = 4  # 골조 부재 — 깊이 방향 수평재 개수 (dependent)
frame_post_L = H_in + 2 * prof_W  # 골조 부재 — 세로재 길이, 통짜 (dependent, 720)
frame_beam_x_L = W_in  # 골조 부재 — 폭 방향 수평재 길이, 세로재 사이 (dependent, 1380)
frame_beam_y_L = D_in  # 골조 부재 — 깊이 방향 수평재 길이, 세로재 사이 (dependent, 970)
frame_x0 = -prof_W  # 골조 부재 — 골조 바깥 외곽 x 시작 (dependent, −30)
frame_x1 = W_in + prof_W  # 골조 부재 — 골조 바깥 외곽 x 끝 (dependent, 1410)
frame_y0 = -prof_W  # 골조 부재 — 골조 바깥 외곽 y 시작 (dependent, −30)
frame_y1 = D_in + prof_W  # 골조 부재 — 골조 바깥 외곽 y 끝 (dependent, 1000)
frame_z0 = -prof_W  # 골조 부재 — 골조 바깥 외곽 z 시작 (dependent, −30)
frame_z1 = H_in + prof_W  # 골조 부재 — 골조 바깥 외곽 z 끝 (dependent, 690)

# --- 바닥 보강재 (레일 밑 깊이 방향 3030) ---
stiff_N = 2  # 바닥 보강재 — 개수 (dependent)
stiff_y0 = 0.0  # 바닥 보강재 — y 시작, 바닥 앞 수평재의 안쪽 면 (dependent, 0)
stiff_y1 = D_in  # 바닥 보강재 — y 끝, 바닥 뒤 수평재의 안쪽 면 (dependent, 970)
stiff_L = stiff_y1 - stiff_y0  # 바닥 보강재 — 길이 (dependent, 970)
stiff_z1 = 0.0  # 바닥 보강재 — 윗면, 내부 바닥 (dependent, 0)
stiff_z0 = stiff_z1 - prof_W  # 바닥 보강재 — 밑면 (dependent, −30)

# --- 받침 레일과 다리 ---
rail_N = 2  # 받침 레일 — 깊이 방향 줄 수 (사용자 결정 2026-10-07)
rail_inset = 100.0  # 받침 레일 — 레일 중심이 팩 좌우 끝에서 안쪽으로 들어온 거리 (사용자 결정 2026-10-07)
rail_cx = (pack_x0 + rail_inset, pack_x1 - rail_inset)  # 받침 레일 — 중심 x (dependent, 200 · 1130)
stiff_cx = rail_cx  # 바닥 보강재 — 중심 x, 레일 중심과 같은 x (dependent, 200 · 1130)
rail_L = pack_D  # 받침 레일 — 길이 (dependent, 810)
rail_y0 = pack_y0  # 받침 레일 — y 시작 (dependent, 80)
rail_y1 = rail_y0 + rail_L  # 받침 레일 — y 끝 (dependent, 890)
rail_z1 = rail_H  # 받침 레일 — 윗면 (dependent, 100)
rail_z0 = rail_z1 - prof_W  # 받침 레일 — 밑면 (dependent, 70)
leg_N_per_rail = 2  # 받침 다리 — 레일마다 다리 수 (사용자 결정 2026-10-07)
leg_H = rail_H - prof_W  # 받침 다리 — 높이 (dependent, 70)
leg_z1 = rail_z0  # 받침 다리 — 윗면, 레일 밑면 (dependent, 70)
leg_z0 = leg_z1 - leg_H  # 받침 다리 — 밑면, 바닥 보강재 윗면 (dependent, 0)
leg_y = ((rail_y0, rail_y0 + prof_W), (rail_y1 - prof_W, rail_y1))  # 받침 다리 — 레일 양 끝의 y 구간 (dependent, 80–110 · 860–890)

# --- 패널 ---
t_panel = 3.0  # t_panel — 알루미늄 복합판 패널 두께 (fixed, 사용자 결정 2026-10-06)
W_out = W_in + 2 * prof_W + 2 * t_panel  # W_out — 외형 폭 (dependent, 1446)
D_out = D_in + 2 * prof_W + 2 * t_panel  # D_out — 외형 깊이 (dependent, 1036)
H_out = H_in + 2 * prof_W + 2 * t_panel  # H_out — 외형 높이 (dependent, 726)
out_x0 = frame_x0 - t_panel  # W_out — 패널 바깥 외곽 x 시작, 왼쪽 패널 바깥면 (dependent, −33)
out_x1 = frame_x1 + t_panel  # W_out — 패널 바깥 외곽 x 끝, 오른쪽 패널 바깥면 (dependent, 1413)
out_y0 = frame_y0 - t_panel  # D_out — 패널 바깥 외곽 y 시작, 앞면 패널 바깥면 (dependent, −33)
out_y1 = frame_y1 + t_panel  # D_out — 패널 바깥 외곽 y 끝, 뒷면 패널 바깥면 (dependent, 1003)
out_z0 = frame_z0 - t_panel  # H_out — 패널 바깥 외곽 z 시작, 바닥 패널 아랫면 (dependent, −33)
out_z1 = frame_z1 + t_panel  # H_out — 패널 바깥 외곽 z 끝, 천장 패널 윗면 (dependent, 693)
# 패널은 여섯 면 모두 골조 바깥면 크기 그대로라(사용자가 결정한 형상, 2026-10-07) 면 안의 외곽은 frame_x0…frame_z1이고, 두께 방향 위치만 아래에 둔다.
panel_front_y0 = frame_y0 - t_panel  # 도어 판 — 앞면 패널 바깥면 (dependent, −33)
panel_front_y1 = frame_y0  # 패널 — 앞면 패널 안쪽 면 (dependent, −30)
panel_back_y0 = frame_y1  # 패널 — 뒷면 패널 안쪽 면 (dependent, 1000)
panel_back_y1 = frame_y1 + t_panel  # 패널 — 뒷면 패널 바깥면 (dependent, 1003)
panel_left_x0 = frame_x0 - t_panel  # 포트 평면 위치 — 왼쪽 패널 바깥면 (dependent, −33)
panel_left_x1 = frame_x0  # 포트 평면 위치 — 왼쪽 패널 안쪽 면 (dependent, −30)
panel_right_x0 = frame_x1  # 포트 평면 위치 — 오른쪽 패널 안쪽 면 (dependent, 1410)
panel_right_x1 = frame_x1 + t_panel  # 포트 평면 위치 — 오른쪽 패널 바깥면 (dependent, 1413)
panel_bottom_z0 = frame_z0 - t_panel  # 캐스터 모델 — 바닥 패널 아랫면 (dependent, −33)
panel_bottom_z1 = frame_z0  # 패널 — 바닥 패널 윗면 (dependent, −30)
panel_top_z0 = frame_z1  # SEN55 높이 — 천장 패널 안쪽 면 (dependent, 690)
panel_top_z1 = frame_z1 + t_panel  # elec_W elec_D elec_H — 천장 패널 윗면 (dependent, 693)

# --- 패널 볼트 ---
panel_bolt_thread = "M6"  # 패널 볼트 — 볼트 규격 (fixed, 사용자 결정 2026-10-07)
panel_bolt_hole_dia = 6.5  # 패널 볼트 — 구멍 지름 (fixed, 사용자 결정 2026-10-07)
panel_bolt_pitch_max = 200.0  # 패널 볼트 — 최대 간격 (fixed, 사용자 결정 2026-10-07)
panel_bolt_edge = 30.0  # 패널 볼트 — 패널 모서리에서 첫 볼트까지 (fixed, 사용자 결정 2026-10-07)
panel_bolt_front_bottom_x = (frame_x0 + panel_bolt_edge, frame_x1 - panel_bolt_edge)  # 패널 볼트 — 앞면 패널 아래 변의 양 끝 볼트 x (dependent, 0 · 1380)

# --- 도어 개구 ---
door_W = 1230.0  # door_W — 도어 개구 폭 (fixed, 사용자 결정 2026-10-07)
door_H = 460.0  # door_H — 도어 개구 높이 (fixed, 사용자 결정 2026-10-07)
door_x0 = pack_x0 - (door_W - pack_W) / 2  # door_W — 개구 x 시작, 팩 좌우로 같은 폭 50 (dependent, 50)
door_x1 = door_x0 + door_W  # door_W — 개구 x 끝 (dependent, 1280)
door_z0 = 0.0  # door_H — 개구 z 시작, 바닥부터 (fixed, 사용자 결정 2026-10-07)
door_z1 = door_z0 + door_H  # door_H — 개구 z 끝 (dependent, 460)

# --- 도어 판 ---
door_overlap = 30.0  # door_overlap — 아크릴 도어 판이 개구 둘레에 겹치는 폭 (fixed, 사용자 결정 2026-10-07)
t_door = 8.0  # t_door — 아크릴 도어 판 두께 (fixed, 사용자 결정 2026-10-06)
gasket_W = 15.0  # gasket_W — 밀폐재 단면 폭 (fixed, 사용자 결정 2026-10-07)
gasket_T = 10.0  # gasket_T — 밀폐재 단면 두께 (fixed, 사용자 결정 2026-10-07)
door_plate_W = door_W + 2 * door_overlap  # 도어 판 — 폭 (dependent, 1290)
door_plate_H = door_H + 2 * door_overlap  # 도어 판 — 높이 (dependent, 520)
door_plate_x0 = door_x0 - door_overlap  # 도어 판 — x 시작 (dependent, 20)
door_plate_x1 = door_x1 + door_overlap  # 도어 판 — x 끝 (dependent, 1310)
door_plate_z0 = door_z0 - door_overlap  # 도어 판 — z 시작 (dependent, −30)
door_plate_z1 = door_z1 + door_overlap  # 도어 판 — z 끝 (dependent, 490)
door_plate_zc = (door_plate_z0 + door_plate_z1) / 2  # 경첩 모델 / 손잡이 모델 — 판 높이의 중앙 (dependent, 230)
door_plate_y1 = panel_front_y0 - gasket_T  # 도어 판 — 뒷면, 밀폐재 앞면 (dependent, −43)
door_plate_y0 = door_plate_y1 - t_door  # 도어 판 — 앞면 (dependent, −51)

# --- 밀폐재 위치 (사각 링, 겹침 폭의 가운데) ---
gasket_off_out = door_overlap / 2 + gasket_W / 2  # 밀폐재 위치 — 개구 가장자리에서 링 바깥 가장자리까지 (dependent, 22.5)
gasket_off_in = door_overlap / 2 - gasket_W / 2  # 밀폐재 위치 — 개구 가장자리에서 링 안쪽 가장자리까지 (dependent, 7.5)
gasket_out_x0 = door_x0 - gasket_off_out  # 밀폐재 위치 — 바깥 x 시작 (dependent, 27.5)
gasket_out_x1 = door_x1 + gasket_off_out  # 밀폐재 위치 — 바깥 x 끝 (dependent, 1302.5)
gasket_out_z0 = door_z0 - gasket_off_out  # 밀폐재 위치 — 바깥 z 시작 (dependent, −22.5)
gasket_out_z1 = door_z1 + gasket_off_out  # 밀폐재 위치 — 바깥 z 끝 (dependent, 482.5)
gasket_in_x0 = door_x0 - gasket_off_in  # 밀폐재 위치 — 안쪽 x 시작 (dependent, 42.5)
gasket_in_x1 = door_x1 + gasket_off_in  # 밀폐재 위치 — 안쪽 x 끝 (dependent, 1287.5)
gasket_in_z0 = door_z0 - gasket_off_in  # 밀폐재 위치 — 안쪽 z 시작 (dependent, −7.5)
gasket_in_z1 = door_z1 + gasket_off_in  # 밀폐재 위치 — 안쪽 z 끝 (dependent, 467.5)
gasket_y1 = panel_front_y0  # 밀폐재 위치 — 뒷면, 앞면 패널 바깥면 (dependent, −33)
gasket_y0 = gasket_y1 - gasket_T  # 밀폐재 위치 — 앞면 (dependent, −43)

# --- 경첩 ---
t_spacer = gasket_T + t_door  # t_spacer — 경첩 받침 블록 두께 (dependent, 18)
spacer_head_dia = 11.0  # t_spacer — 블록 밑면의 M6 버튼 볼트 머리 자리 지름 (fixed, 사용자 결정 2026-10-07)
spacer_head_depth = 4.0  # t_spacer — 블록 밑면의 M6 버튼 볼트 머리 자리 깊이 (fixed, 사용자 결정 2026-10-07)
hinge_id = "butt_hinge_50x50"  # 경첩 모델 — step.parts id (fixed, 사용자 결정 2026-10-07)
hinge_N = 3  # 경첩 모델 — 개수 (fixed, 사용자 결정 2026-10-06)
hinge_end = 50.0  # 경첩 모델 — 위·아래 경첩 중심이 도어 판 끝에서 떨어진 거리 (fixed, 사용자 결정 2026-10-07)
hinge_z = (door_plate_z1 - hinge_end, door_plate_zc, door_plate_z0 + hinge_end)  # 경첩 모델 — 위·가운데·아래 중심 z (dependent, 440 · 230 · 20)

# --- 토글 클램프 ---
clamp_N = 2  # 토글 클램프 모델 — 개수 (fixed, 사용자 결정 2026-10-06)
clamp_end = 50.0  # 토글 클램프 모델 — 위·아래 중심이 도어 판 끝에서 떨어진 거리 (fixed, 사용자 결정 2026-10-07)
clamp_z = (door_plate_z1 - clamp_end, door_plate_z0 + clamp_end)  # 토글 클램프 모델 — 위·아래 중심 z (dependent, 440 · 20)

# --- 손잡이 ---
handle_id = "pull_handle_mount_spacing128"  # 손잡이 모델 — step.parts id, 세로로 단다 (fixed, 사용자 결정 2026-10-07)
handle_inset = 40.0  # 손잡이 모델 — 중심이 도어 판 왼쪽 끝에서 안쪽으로 들어온 거리 (fixed, 사용자 결정 2026-10-07)
handle_x = door_plate_x0 + handle_inset  # 손잡이 모델 — 중심 x (dependent, 60)
handle_z = door_plate_zc  # 손잡이 모델 — 중심 z, 판 높이의 중앙 (dependent, 230)

# --- 캐스터 ---
caster_id = "locking_swivel_caster_wheel_d100"  # 캐스터 모델 · 바퀴 지름 — step.parts id (fixed, 사용자 결정 2026-10-07)
caster_N = 4  # 캐스터 모델 · 바퀴 지름 — 개수 (fixed, 사용자 결정 2026-10-06)
caster_wheel_dia = 100.0  # 캐스터 모델 · 바퀴 지름 — 바퀴 지름 (fixed, 사용자 결정 2026-10-07)
caster_mount_z = panel_bottom_z0  # 캐스터 모델 · 바퀴 지름 — 장착면, 바닥 패널 아랫면 (dependent, −33)

# --- 주입·배기 포트 ---
inlet_dia = 50.0  # inlet_dia — 주입 관 내경 (fixed, 사용자 결정 2026-10-07)
exhaust_dia = 50.0  # exhaust_dia — 배기 관 내경 (fixed, 사용자 결정 2026-10-07)
port_z = rail_H + pack_H + clr_top / 2  # port_z — 포트 중심 높이, 팩 윗면과 천장의 가운데 (dependent, 510)
port_y = 485.0  # 포트 평면 위치 — 관 중심 y, 옆면 깊이 가운데 (fixed, 사용자 결정 2026-10-07)
assert port_y == D_in / 2, "포트 평면 위치(y 485)가 옆면 깊이 가운데와 어긋난다"
port_tube_wall = 3.0  # 포트 세부 — 관 벽 두께 (fixed, 사용자 결정 2026-10-07)
inlet_tube_OD = inlet_dia + 2 * port_tube_wall  # 포트 세부 — 주입 관 외경 (dependent, 56)
exhaust_tube_OD = exhaust_dia + 2 * port_tube_wall  # 포트 세부 — 배기 관 외경 (dependent, 56)
port_protrude = 50.0  # 포트 세부 — 관이 패널 바깥면에서 돌출하는 길이 (fixed, 사용자 결정 2026-10-07)
port_flange_OD = 100.0  # 포트 세부 — 플랜지 외경 (fixed, 사용자 결정 2026-10-07)
port_flange_T = 5.0  # 포트 세부 — 플랜지 두께 (fixed, 사용자 결정 2026-10-07)
port_bolt_thread = "M5"  # 포트 세부 — 플랜지 볼트 규격 (fixed, 사용자 결정 2026-10-07)
port_bolt_N = 4  # 포트 세부 — 플랜지 구멍 개수 (fixed, 사용자 결정 2026-10-07)
port_bolt_PCD = 80.0  # 포트 세부 — 플랜지 구멍 피치원 지름 (fixed, 사용자 결정 2026-10-07)
port_cap_wall = 3.0  # 포트 세부 — 마개 벽 두께 (fixed, 사용자 결정 2026-10-07)
port_cap_depth = 20.0  # 포트 세부 — 마개 깊이 (fixed, 사용자 결정 2026-10-07)
inlet_tube_x0 = panel_right_x0  # 포트 세부 — 주입 관 안쪽 끝, 오른쪽 패널 안쪽 면 (dependent, 1410)
inlet_tube_x1 = panel_right_x1 + port_protrude  # 포트 세부 — 주입 관 바깥 끝 (dependent, 1463)
exhaust_tube_x1 = panel_left_x1  # 포트 세부 — 배기 관 안쪽 끝, 왼쪽 패널 안쪽 면 (dependent, −30)
exhaust_tube_x0 = panel_left_x0 - port_protrude  # 포트 세부 — 배기 관 바깥 끝 (dependent, −83)

# --- 천장 중심과 케이블 관통 ---
ceil_cx = W_in / 2  # 케이블 관통 위치 — 천장 중심 x (dependent, 690)
ceil_cy = D_in / 2  # 케이블 관통 위치 — 천장 중심 y (dependent, 485)
gland_id = "cable_gland_body_m20"  # 글랜드 — step.parts id (fixed, 사용자 결정 2026-10-07)
gland_N = 3  # 글랜드 — 개수, 케이블마다 하나 (fixed, 사용자 결정 2026-10-07)
gland_pitch = 30.0  # 글랜드 — 간격 (fixed, 사용자 결정 2026-10-07)
gland_x = tuple(ceil_cx + (i - (gland_N - 1) / 2) * gland_pitch for i in range(gland_N))  # 케이블 관통 위치 — 천장 중심을 기준으로 x 방향 한 줄의 글랜드 중심 x (dependent, 660 · 690 · 720)
gland_y = ceil_cy  # 케이블 관통 위치 — 글랜드 중심 y (dependent, 485)

# --- SEN55 ---
sen_L = 52.3  # sen_L — SEN55 모듈 길이 (fixed, 데이터시트 Figure 7)
sen_W = 43.3  # sen_W — SEN55 모듈 폭 (fixed, 데이터시트 Figure 7)
sen_T = 22.3  # sen_T — SEN55 모듈 두께 (fixed, 데이터시트 Figure 7)
sen_body_T = 13.2  # sen_T — SEN55 본체 두께 (fixed, 데이터시트 Figure 7)
sen_tol = 0.4  # sen_L sen_W sen_T — 외형 공차 ± (fixed, 데이터시트 Figure 7)
sen_W_tol_plus = 0.2  # sen_L sen_W sen_T — 폭 공차 + (fixed, 데이터시트 Figure 7)
sen_W_tol_minus = 0.6  # sen_L sen_W sen_T — 폭 공차 − (fixed, 데이터시트 Figure 7)
sen_N = 3  # SEN55 평면 위치 — 대수 (fixed, 사용자 확인 2026-09-07)
sen_gap = 20.0  # sen_gap — 천장 부착면에서 모듈을 띄우는 거리 (fixed, 사용자 결정 2026-10-07)
sen_top_z = panel_top_z0 - sen_gap  # SEN55 높이 — 모듈 윗면 (dependent, 670)
sen_r = D_in / 4  # sen_r — 천장 중심에서 각 SEN55까지의 거리, 천장 짧은 변의 1/4 (dependent, 242.5)
sen_phi = -90.0  # sen_phi — 첫 대의 방향, 앞쪽(−y, 도어 쪽). 각도는 +x에서 +y 쪽으로 잰다 (fixed, 사용자 결정 2026-10-06)
sen_step = 120.0  # SEN55 평면 위치 — 대칭 배치 간격 (fixed, 사용자 결정 2026-10-06)
sen_angles = (sen_phi, sen_phi - sen_step, sen_phi + sen_step)  # SEN55 평면 위치 — 앞, 뒤 왼쪽, 뒤 오른쪽 순서의 방향 (dependent)
sen_xy = tuple((ceil_cx + sen_r * math.cos(math.radians(a)), ceil_cy + sen_r * math.sin(math.radians(a))) for a in sen_angles)  # SEN55 평면 위치 — 세 대의 중심 (dependent, (690, 242.5) · (479.99, 606.25) · (900.01, 606.25))
brk_wall = 2.5  # brk_wall — SEN55 브래킷 벽 두께 (fixed, 사용자 결정 2026-10-07)
brk_bolt_thread = "M4"  # brk_wall — 브래킷을 천장 패널에 다는 볼트 규격 (fixed, 사용자 결정 2026-10-07)
brk_bolt_N = 2  # brk_wall — 브래킷 볼트 개수 (fixed, 사용자 결정 2026-10-07)

# --- P82B715 센서측 기판 ---
ext_W = 30.0  # ext_W — 기판 긴 변 (fixed, 사용자 결정 2026-10-07)
ext_D = 20.0  # ext_D — 기판 짧은 변 (fixed, 사용자 결정 2026-10-07)
ext_T = 1.6  # ext_W ext_D — 기판 두께 (fixed, 사용자 결정 2026-10-07)
ext_hole_thread = "M3"  # ext_W ext_D — 구멍 규격 (fixed, 사용자 결정 2026-10-07)
ext_hole_dia = 3.2  # ext_W ext_D — 구멍 지름, 전장 기판과 같은 Ø3.2 (fixed, 사용자 결정 2026-10-07)
ext_hole_N = 2  # ext_W ext_D — 구멍 개수 (fixed, 사용자 결정 2026-10-07)
ext_hole_edge = 4.0  # ext_W ext_D — 구멍 중심이 짧은 변에서 떨어진 거리, 긴 변 중심선 위 (fixed, 사용자 결정 2026-10-07)

# --- 전장 기판 ---
pcb_W = 80.0  # pcb_W — 전장 기판 폭 (fixed, 사용자 결정 2026-10-07)
pcb_D = 60.0  # pcb_D — 전장 기판 깊이 (fixed, 사용자 결정 2026-10-07)
pcb_T = 1.6  # pcb_T — 전장 기판 두께 (fixed, 사용자 결정 2026-10-07)
pcb_hole_thread = "M3"  # pcb_W pcb_D pcb_T — 구멍 규격 (fixed, 사용자 결정 2026-10-07)
pcb_hole_dia = 3.2  # pcb_W pcb_D pcb_T — 구멍 지름 (fixed, 사용자 결정 2026-10-07)
pcb_hole_N = 4  # pcb_W pcb_D pcb_T — 구멍 개수 (fixed, 사용자 결정 2026-10-07)
pcb_hole_edge = 4.0  # pcb_W pcb_D pcb_T — 구멍 중심이 모서리에서 떨어진 거리 (fixed, 사용자 결정 2026-10-07)
usbc_W = 9.0  # pcb_W pcb_D pcb_T — USB-C 외곽 블록 9 × 7.5 × 3.3의 첫째 값 (fixed, 사용자 결정 2026-10-07)
usbc_D = 7.5  # pcb_W pcb_D pcb_T — USB-C 외곽 블록 9 × 7.5 × 3.3의 둘째 값 (fixed, 사용자 결정 2026-10-07)
usbc_H = 3.3  # pcb_W pcb_D pcb_T — USB-C 외곽 블록 9 × 7.5 × 3.3의 셋째 값 (fixed, 사용자 결정 2026-10-07)

# --- 전장함 ---
elec_wall = 2.0  # 전장함 세부 — 벽 두께 (fixed, 사용자 결정 2026-10-07)
elec_clr = 5.0  # 전장함 세부 — 기판 둘레 여유 (fixed, 사용자 결정 2026-10-07)
elec_in_H = 25.0  # 전장함 세부 — 안쪽 높이 (fixed, 사용자 결정 2026-10-07)
elec_lid_T = 2.0  # 전장함 세부 — 뚜껑 두께 (fixed, 사용자 결정 2026-10-07)
elec_floor_T = elec_wall  # elec_W elec_D elec_H — 바닥 두께, 바깥 높이 29 = 바닥 + 안쪽 높이 25 + 뚜껑 2에서 벽 두께와 같다 (dependent, 2)
elec_standoff_H = 10.0  # 전장함 세부 — 스탠드오프 높이 (fixed, 사용자 결정 2026-10-07)
elec_standoff_dia = 6.0  # 전장함 세부 — 스탠드오프 지름 (fixed, 사용자 결정 2026-10-07)
elec_standoff_thread = "M3"  # 전장함 세부 — 스탠드오프 나사 규격 (fixed, 사용자 결정 2026-10-07)
elec_usb_hole_W = 12.0  # 전장함 세부 — USB 구멍 12 × 7의 첫째 값 (fixed, 사용자 결정 2026-10-07)
elec_usb_hole_H = 7.0  # 전장함 세부 — USB 구멍 12 × 7의 둘째 값 (fixed, 사용자 결정 2026-10-07)
elec_W = pcb_W + 2 * elec_clr + 2 * elec_wall  # elec_W — 전장함 바깥 폭 (dependent, 94)
elec_D = pcb_D + 2 * elec_clr + 2 * elec_wall  # elec_D — 전장함 바깥 깊이 (dependent, 74)
elec_H = elec_floor_T + elec_in_H + elec_lid_T  # elec_H — 전장함 바깥 높이 (dependent, 29)
elec_cx = ceil_cx  # elec_W elec_D elec_H — 중심 x, 천장 중심 (dependent, 690)
elec_cy = ceil_cy  # elec_W elec_D elec_H — 중심 y, 천장 중심 (dependent, 485)
elec_x0 = elec_cx - elec_W / 2  # elec_W — 전장함 x 시작 (dependent, 643)
elec_x1 = elec_cx + elec_W / 2  # elec_W — 전장함 x 끝 (dependent, 737)
elec_y0 = elec_cy - elec_D / 2  # elec_D — 전장함 y 시작 (dependent, 448)
elec_y1 = elec_cy + elec_D / 2  # elec_D — 전장함 y 끝 (dependent, 522)
elec_z0 = panel_top_z1  # elec_H — 전장함 밑면, 천장 패널 윗면 (dependent, 693)
elec_z1 = elec_z0 + elec_H  # elec_H — 전장함 윗면 (dependent, 722)


if __name__ == "__main__":
    def _fmt(value):
        if isinstance(value, float):
            return f"{value:g}" if value == round(value, 4) else f"{value:.4f}"
        if isinstance(value, tuple):
            return "(" + ", ".join(_fmt(v) for v in value) + ")"
        return repr(value)

    for _name, _value in list(globals().items()):
        if not _name.startswith("_") and isinstance(_value, (int, float, str, tuple)):
            print(f"{_name} = {_fmt(_value)}")
