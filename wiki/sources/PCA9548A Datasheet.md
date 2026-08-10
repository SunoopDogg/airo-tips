---
title: PCA9548A Datasheet
type: source
tags: [sensor-spec, 멀티플렉서]
created: 2026-09-07
updated: 2026-09-07
status: developing
sources: []
source_path: raw/sensor-spec/pca9548a.pdf
ingested: 2026-09-07
---

Texas Instruments의 PCA9548A 데이터시트(SCPS143G, 2009년 6월 최초 발행, 2021년 3월 개정). 8채널 양방향 I2C 스위치(멀티플렉서) IC의 전기·타이밍 사양과 레지스터 맵을 담는다.

## 무엇인가

PCA9548A는 SCL/SDA 한 쌍의 업스트림을 여덟 개의 다운스트림 채널(SC0/SD0~SC7/SD7)로 팬아웃하는 I2C 스위치다. 각 채널 또는 채널 조합은 8비트 제어 레지스터로 선택하며, 이 구조는 동일한 I2C 슬레이브 주소를 가진 장치 여러 개(예: 동일 모델 온도센서 다수)를 하나의 버스에 붙이는 용도로 소개된다.

## 슬레이브 주소

PCA9548A 자신의 I2C 주소는 고정 상위 비트 `1110`에 하드웨어 핀 A2·A1·A0으로 정하는 하위 3비트를 더한 7비트다. A0~A2를 전부 GND로 접지하면 주소는 0x70이고, 세 핀을 VCC/GND로 조합하면 0x70~0x77 여덟 개 중 하나를 고를 수 있다.

## 채널 선택

주소 바이트가 ACK된 뒤, 마스터가 쓰는 8비트 명령 바이트의 각 비트(B0~B7)가 채널 0~7 하나씩에 대응한다. 해당 비트가 1이면 그 채널이 열리고, 여러 비트를 동시에 1로 두면 여러 채널이 동시에 열린다. 선택은 I2C 스톱 조건 이후에 적용된다. 전원 인가 직후에는 모든 채널이 닫힌 상태로 시작한다.

## 전기·타이밍 사양

동작전압 범위 2.3~5.5 V, 입출력 전 핀이 5 V-tolerant다. 클럭 주파수는 0~400 kHz(Standard/Fast mode)를 지원하고, 채널마다 서로 다른 버스 전압(1.8/2.5/3.3/5 V)을 걸 수 있어 전압 레벨 변환 용도로도 쓰인다. RESET 핀은 active-low이고, 미사용 시 VCC로 풀업 저항을 통해 연결하라고 명시되어 있다. RESET을 로우로 걸거나 전원을 재인가(POR)하면 모든 채널이 닫힌 상태로 초기화된다.

## 인용할 만한 문구

"Any individual downstream channel can be selected as well as any combination of the eight channels." — 8채널 임의 선택·동시 선택이 가능하다는 근거.

"RESET… Connect to VCC through a pull-up resistor, if not used." — RESET 미사용 시 배선 규칙.
