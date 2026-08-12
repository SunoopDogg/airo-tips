---
title: EnerX-0.5P Battery Container Operating Instruction and Maintenance Manual
type: source
tags: [ess-reference, 상용ESS, 화재감지, bms]
created: 2026-09-08
updated: 2026-09-08
status: developing
sources: []
source_path: raw/ess-reference/EnerX-0.5P Battery Container-CATL-Operating Instruction and Maintenance Manual.pdf
ingested: 2026-09-08
---

CATL의 액체냉각 컨테이너형 ESS EnerX-0.5P의 운용·유지보수 매뉴얼. 안전수칙, 제품 구성, 소화시스템(FSS)과 BMS의 동작, 운송·설치·시운전·진단·유지보수 절차를 담는다.

## 무엇인가

CATL(Contemporary Amperex Technology Limited)이 작성한 96쪽 영문 매뉴얼. 표지에 Confidential 등급, 작성자 WPX, 작성일 2024.08.01이 적혀 있고 개정 이력은 Rev 1.0 "Draft revision"(2024/8/01) 하나뿐인 **초안**이다. 대상 독자는 BESS 운영자와 서비스 요원이며 운용·유지보수·부품 정보 셋을 제공한다고 밝힌다.

원문 자체의 상태: 목차 3.3.10과 8.3절 표 참조가 워드 오류 문자열(错误!未定义书签。/ 错误!未找到引用源。)로 남아 있고, 표 3-11(TMS 주요 특징)은 제목만 있다. 그림은 텍스트로 추출되지 않았다. 아래 "원문 내부의 불일치"도 참조.

## 제품 구성

[[EnerX-0.5P]] 컨테이너는 배터리 시스템, BMS, 소화시스템(FSS), 열관리시스템(TMS), 보조 배전 시스템으로 이루어진다.

| 항목 | 값 |
|---|---|
| 형식 | 20ft 컨테이너, 6058 × 2438 × 2896 mm, 약 47 t, IP55, 옥외 비보행형 |
| 배터리 | LFP, 8랙 병렬 × 랙당 4모듈 × 모듈당 104S(1P104S) 셀(530 Ah / 3.2 V) = 3328셀. 모듈마다 CSC와 고속 DC 퓨즈 내장 |
| 시스템 | 정격 5644.29 kWh, 정격 1331.2 VDC, 1040~1500 VDC, 정격 2120 A / 2822.14 kW (0.5P), 최대 2714 A/1분 |
| 운전 환경 | 충·방전 −35~+55 ℃, 보관 −35~+60 ℃, 상대습도 0~95 %(비결로), 고도 ≤4000 m |
| 냉각 | 액체냉각 칠러 1대 70 kW, 냉각수 에틸렌글리콜 50 % + DI 50 % |
| 통신 | CAN, RS485, TCP/IP |
| 규격 | 셀 UN38.3·UL1973·IEC62619·UL9540A, 컨테이너 UL1973·NFPA855·UL9540A·UL9540·IEC 62477·IEC 62619·IEC 62933-5-2·IEC 63056·IEC 61000-6-2/-6-4 |

안전 절은 주요 위험으로 1500 VDC 고전압과 아크 결함을 들고, NFPA 70E 최대전력법으로 아크플래시 경계를 정하며 PPE 카테고리 2를 요구한다. "특정 극한 결함 조건에서 화재가 가능하다"는 경고가 있고, 대피용 스트로브·경보는 FSS가 기동한다.

## 소화시스템(FSS)

EnerX는 옥외 비보행형이므로 검출·폭발 제어·소화 기능을 갖춘 FSS를 통째로 제공하며, 제어 전략은 4단계다.

1. 1단계: 경보 발령
2. 2단계: 배기환기로 폭연(deflagration) 방지
3. 3단계: 에어로졸 방출로 초기 화재 진압
4. 4단계: 살수로 화재 확산 억제

FSS는 검출계, 배기환기계, 소화계 셋으로 나뉜다.

| 구분 | 구성품 | 수량 | 위치·비고 |
|---|---|---|---|
| 검출·경보 | 화재수신기 ARC-100 | 1 | 전기실. 검출기 신호를 받아 소화·배기환기를 제어 |
| | 광섬유 네트워크 카드 NCF-1000 | 1 | 옵션. 수신기 신호를 광신호로 변환, 단말 호스트 AFC-1000과 연결 |
| | H2 검출기 | 1 | 배터리실, 수소 검출 |
| | CO 검출기 | 1 | 배터리실, CO 검출 |
| | 열감지기 | 2 | 배터리실, 온도 검출 |
| | 연기감지기 | 3 | 배터리실 2, 전기실 1 |
| | 방출회로 차단 스위치, 혼·스트로브, 2릴레이 2입력 모듈 ×4, 수동발신기 | | 전기실·전기실 문 |
| 배기환기 | 방폭 배기팬 | 1 | TMS 옆. 128 W, 230 VAC, 820 ±15 % CFM |
| | 방폭 환기 루버 | 2 | 배터리실 문 |
| | 팬 비상 스위치 | 1 | 전기실 문 |
| 소화 | 에어로졸 | 12 | 옵션, 배터리실 |
| | 드라이파이프 노즐(고무 플러그) V2709 | 8 | 옵션, 배터리실. 개방형(비자동) 수평 측벽형, 최대 250 psi |
| | 플랜지 NPS 2" | 1 | 소화용수 인입 |

검출기는 세 종류이고 모든 검출 신호는 화재수신기가 받아 처리한다. 유지보수 표 8-1은 검출기 종류를 "가스 검출기·연기감지기·온도감지기"로 묶는다.

**배기환기 동작:** 화재수신기(FCP)가 **H2 검출기 또는 CO 검출기의 경보**를 받으면 배기환기계에 신호를 보내 전동 루버와 방폭팬을 켜고 배터리실의 가연성 가스를 배출한다. 방폭 배기팬은 켜진 뒤 자동으로 꺼지지 않는다. 환기 설계는 NFPA 69를 만족한다.

**소화 동작:** 배터리실에 초기 화재가 생기면 화재경보 신호가 나가고 소화계가 에어로졸 방출을 자동 제어하며 수동 기동도 가능하다. 드라이파이프는 화재 확산 억제용이다.

**FSS 건접점 5개:** 외부 FSS 또는 EMS가 다음 접점을 본다.

| 접점 | 의미 | open 시 조치 |
|---|---|---|
| Fire system fault level 1 | FSS 센서 중 **하나라도** 경보 | EMS가 PCS 전원 차단, FCP에서 상세 확인 |
| Fire system fault level 2 | 배터리실에서 **열감지기 1 + 연기감지기 1**이 경보, 또는 **열감지기 2**가 경보 | EMS가 PCS 전원 차단, FCP에서 상세 확인 |
| Exhaust ventilation state | 환기팬 켜짐 | EMS가 PCS 전원 차단, FCP에서 상세 확인 |
| Exhaust ventilation body warning | 환기팬을 켰는데 팬·루버가 동작 불가 | FCP에서 상세 확인 |
| Fire system failure warning | FSS 자체 고장 | FCP에서 상세 확인 |

FSS 제어반에는 12 V 배터리 2직렬 UPS가 내장되어 외부 보조전원 없이 대기 24시간·경보 2시간을 버틴다. 방폭계 전원은 고객 측 백업이 따로 필요하다. 보조전원이 24시간 이상 끊기면 UPS 과방전 위험이 있다.

## BMS

BMS는 배터리 전압·전류·온도 감시, 에너지 흡수·방출 관리, 열관리, 저전압 전원, 고전압 안전 감시, 고장 진단·관리, PCS·EMS와의 외부 통신을 맡는다. 구성은 MBMU 1, IMM 2, ETH 1, SBMU 4, CSC 32의 3계층이다. 전원 버튼이 없어 전원을 넣으면 켜지고 끊으면 꺼진다.

| 모듈 | 위치 | 역할 |
|---|---|---|
| MBMU | 마스터 제어박스 | 시스템 전원 on/off, 시각 동기, MCAN(SBMU·ETH·PC)/DCAN(TMS)/ACAN(ETH) 통신, 환경온도 2점 검출, SOC·SOH·SOP·운전상태 업로드, 랙 HV 릴레이 제어, SPD·UPS·FSS·보조전원 건접점 검출, IMM 값으로 절연상태 판정, 환기팬 상태 검출 |
| IMM | 마스터 제어박스 | HV+/HV−와 케이스 사이 절연저항 측정 |
| ETH | 마스터 제어박스 | RJ45로 PCS·EMS와 TCP/IP 통신(고정 IP/DHCP), **Modbus 지원**, 원격 업데이트, MCAN·ACAN 두 CAN 인터페이스 |
| SBMU | 서브 제어박스(4개) | HV 접촉기·프리차지·DC 퓨즈와 함께 랙을 제어하고 랙 상태를 CAN으로 MBMU에 전송 |
| CSC | 배터리 모듈 | 셀 감시 |

MBMU의 환경온도 입력은 2점으로 범위 −40~85 ℃, 정확도 ±3 ℃이며, 하나는 화재수신기에, 하나는 배전박스 변압기 T1에 있다. 환경온도가 60 ℃를 넘으면 Level 1 알람을 낸다.

**배터리 상태 감시:** 셀 전압, 모듈 온도, 배터리 전류, 총전압을 감시한다. SOC·SOH·SOP를 **정밀도 5 %**로 산출한다. 저전압·과방전·과전압·과온·과전류에서 안전관리 기능을 하며, 고장 시 상위 장비에 경보하고 충·방전 전류·전력을 제한하며 모든 HV 릴레이의 차단을 지연시킨다. 데이터 기록과 고장 정보 기록을 EMS에 제공하고, 운전 파라미터와 이력 알람을 저장해 ESS 모니터링 툴로 볼 수 있다. 열관리에서는 셀 온도와 칠러 상태를 샘플링하고 셀·냉각수 온도로 TMS를 제어한다.

CAN 속도는 ACAN 250 k, CCAN·MCAN·SCAN 500 k. 모니터 소프트웨어 설정에서 모듈당 온도 측정점은 11, 랙당 CSC(모듈) 수는 8, 모듈당 셀전압 수는 52(104셀, 2P52S)로 적혀 있다. HV 릴레이를 닫은 뒤 시스템 전압과 셀 누적전압의 차가 2 V 미만이 되도록 내부 전압 보정을 한다.

**시스템 상태 워드(레지스터 0x0000~0x0004):** 셀 과전압·저전압 경고, 셀 극단 과·저전압, 캐비닛 과·저전압, 셀 전압차 큼, 셀전압 무효, 방전·충전 과전류, 전류센서, 셀 과온·저온, SBMU 제어박스 과온·저온, 단일·복수 온도 샘플링 이상, 릴레이 구동 단락, CSC·SBMU 전원·코드 구동 단락 경고를 비트로 낸다.

**고장 등급별 대응(표 8-2):** 고장이 검출되면 심각도에 따라 안전 운전 모드로 자동 전환한다.

| 등급 | 심각도 | EMS 보고 | BMS 고장 건접점 | HV 접촉기 |
|---|---|---|---|---|
| CAT 1 | 매우 낮음 | 보고 | close | 없음 |
| CAT 2 | 낮음 | 보고 | close | 없음 |
| CAT 3 | 낮음 | 보고 | close | 없음 |
| CAT 4 | 중간 | 보고 | close | 고장 랙 1개를 10 s 후 차단 |
| CAT 5 | 높음 | 보고 | close | 고장 랙 1개를 즉시 차단 |
| CAT 6 | 높음 | 보고 | open | 전 랙 10 s 후 차단 |
| CAT 7 | 매우 높음 | 보고 | open | 전 랙 즉시 차단 |

본문은 "5 level"이라 쓰고 표는 CAT 1~7을 든다.

**진단표(표 8-3)의 알람과 조치:** 셀 과전압(충전 중지·대기 균등화), 셀 저전압(방전 중지), NTC 과온(공조 동작 확인, 충·방전 전류 저감), NTC 저온(가열 확인, 충전 금지), 충·방전 과전류, SOC 상·하한, 셀 온도차 큼(공조·온도센서), 셀 전압차 큼(80 % SOC 이상 충전 후 균등화), 랙 간 SOC 차, 균등화 회로 이상 등.

## 운용·유지보수

시운전은 보조전원 투입 → 제어박스 HV 릴레이 투입(1040~1500 VDC 발생) → PCS 기동·DC 커패시터 프리차지(PCS 측이 수행할 것을 권고) → PCS-컨테이너 DC 연결(전동 DC 차단기) → EMS가 PCS에 충·방전 명령 순이다. 문에 E-stop 버튼이 있다.

예방 유지보수는 연 2회(반기 기본 점검 + 연간 종합 점검)를 권고한다. 배터리실 점검 항목에 **자극성 냄새·탄내**(반기, 문을 열지 않아도 됨), **크래클링 소리**(반기), 온습도 기록이 있고, FSS 항목에 가스·연기·온도 검출기 정상 여부(연 1회 또는 현지 규정), **연기+가스 동시 트리거 시 경보 동작**, **온도+연기 동시 트리거 시 경보 동작**, 커넥터 체결, 에어로졸 수명이 있다. 심층 점검에서는 운전 중 휴대 열화상으로 제어 캐비닛 온도를 재어 **온도상승(측정값 − 실온) 50 ℃ 초과** 여부를 보고, 절연저항은 1500 VDC에서 ≥20 MΩ, 셀 전압차는 ≤300 mV(동적, 전 범위) 또는 ≤100 mV(동적, SOC 30~80 %)를 기준으로 한다.

배터리 연간 유지보수는 컷오프(최저 셀 2.5 V 미만)까지 방전 → 만충(최고 셀 3.65 V 초과) → SOC 23 %로 맞추는 절차다. 장기 유휴 시 SOC 30~60 %, 90일 초과면 50 % 이상, 셀 정지전압 3.2 V 미만이면 즉시 재충전, 2.5 V 미만이면 보증 무효, 2.0 V 미만이면 수리 불가. 출하 SOC는 23 %. 냉각수는 5년 또는 pH <6.5 / >9.5, 염화물 >60 ppm, 탁함 시 교체하며 공급사 혼용 금지.

## 원문 내부의 불일치

- 모듈 셀 구성: 3.1.1·3.1.2·사양표는 104S(1P104S)라 하고, 6.5절 모니터 소프트웨어 설정은 "셀전압 수 52, 모듈당 셀 104(2P52S)"라 한다.
- 랙당 모듈 수: 3.1.1은 랙당 4모듈(총 32모듈)이라 하고, 서브 제어박스 JX3 설명과 6.5절 CSC 수는 랙당 8이라 한다.
- IMM 수량: 표 3-1은 마스터 제어박스에 IMM 포함(수량 미기재), 3.3.1은 IMM 2대, 3.1.3은 MBMU·IMM·ETH·광모듈이 마스터 제어박스에 통합이라 한다. BMS 구조도에는 IMM1·IMM2가 있다.
- 고장 등급 수: 8.2절 본문은 5단계, 표 8-2는 CAT 1~7.
- 보조전원: 3.2 사양표는 1AC 230 V, 7.3절은 1AC 120~230 V.

## 인용할 만한 문구

- "The fire suppression control strategy is divided into four levels: The first level: Alarm warning; The second level: Smoke exhaust ventilation system to prevent deflagration; The third level: Aerosol is released to extinguish the initial fire; The fourth level: Water spraying to control the spread of the fire."
- "The smoke exhaust ventilation system receives the alarm signal from the FCP after the FCP receives the alarm signal sent by the H2 detector or CO detector, then turns on the air electric louver and the explosion-proof fan, and discharges the combustible gas in the battery compartment. The explosion-proof exhaust fan doesn't turn off automatically after opening."
- "Fire system fault level 2 — To indicate that one heat detector and one smoke detector in battery room give an alarm or two heat detectors give an alarm."
- "The BMS detects the battery status, including State of Charge (SOC), SOH and SOP calculation, with a precision of 5%."
- "Fire is possible under certain, extreme fault conditions."
