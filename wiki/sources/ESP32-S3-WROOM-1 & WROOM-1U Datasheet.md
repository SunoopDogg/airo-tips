---
title: ESP32-S3-WROOM-1 & WROOM-1U Datasheet
type: source
tags: [sensor-spec, 데이터시트, 컨트롤러, 모의장치]
created: 2026-09-07
updated: 2026-09-07
status: stable
sources: []
source_path: raw/sensor-spec/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf
ingested: 2026-09-07
---

에스프레시프(Espressif)의 Wi-Fi + Bluetooth LE MCU 모듈 ESP32-S3-WROOM-1과 ESP32-S3-WROOM-1U의 데이터시트. 판본은 v1.4(2024-11-14), 52쪽이다. [[ESP32-S3-WROOM-1]]의 사양 출처다.

## 원문이 무엇인가

두 모듈은 ESP32-S3 계열 SoC(Xtensa 듀얼코어 32비트 LX7, 최대 240 MHz)를 중심으로 40 MHz 수정 발진기와 Quad SPI 플래시(최대 16 MB), 선택적으로 PSRAM(최대 16 MB)을 얹은 것이다. WROOM-1은 온보드 PCB 안테나, WROOM-1U는 외부 안테나 커넥터(U.FL/MHF I/AMC 호환)를 쓴다. 상정된 응용은 스마트홈·산업자동화·저전력 IoT 센서 허브·데이터 로거·영상 스트리밍 카메라·음성/이미지 인식 등이다.

주변장치 절(5장)과 부팅 설정 절(4장)은 ESP32-S3 Series Datasheet에서 발췌한 것이며, 모듈에 노출되지 않은 IO 신호가 있어 일부 내용은 모듈에 적용되지 않는다고 원문이 밝힌다. 회로도(8장)의 도면 날짜는 2023-11-21이고, WROOM-1 도면은 V1.4, WROOM-1U 도면은 V1.5로 판이 다르다.

## 변형(ordering code)과 동작온도

플래시·PSRAM 조합에 따라 변형이 나뉘고, **PSRAM 종류가 동작온도 상한을 정한다.**

| 변형 | 플래시 | PSRAM | 동작 주위온도 |
|---|---|---|---|
| N4 / N8 / N16 | 4 / 8 / 16 MB Quad SPI | 없음 | −40 ~ 85 °C |
| H4 | 4 MB Quad SPI | 없음 | −40 ~ 105 °C |
| N4R2 / N8R2 / N16R2 | 4 / 8 / 16 MB | 2 MB Quad SPI | −40 ~ 85 °C |
| N4R8 / N8R8 / N16R8 | 4 / 8 / 16 MB | 8 MB Octal SPI | −40 ~ 65 °C |
| N16R16VA | 16 MB | 16 MB Octal SPI | −40 ~ 65 °C |

여기서 주위온도는 "모듈 바로 바깥 환경의 권장 온도 범위"다. R8·R16V 변형에서 PSRAM ECC를 켜면 상한이 85 °C로 올라가는 대신 PSRAM 가용 용량이 1/16 줄어든다. Octal SPI PSRAM 변형(ESP32-S3R8·R16V 내장)은 **IO35·IO36·IO37이 PSRAM에 연결되어 있어 다른 용도로 쓸 수 없다.** N16R16VA는 VDD_SPI가 1.8 V라 GPIO47·GPIO48도 1.8 V로 동작한다.

크기는 WROOM-1이 18.0 × 25.5 × 3.1 mm, WROOM-1U가 18.0 × 19.2 × 3.2 mm다. 플래시는 10만 회 이상 프로그램/소거, 20년 이상 데이터 보존이다.

## 핀

모듈 핀은 41개(EPAD 포함)이며 GPIO는 최대 36개다. EN 핀은 High일 때 켜지고 Low일 때 꺼지며 **플로팅으로 두면 안 된다.** 기동 시 전원 안정을 위해 EN에 RC 지연 회로(권장 R = 10 kΩ, C = 1 µF)를 두라고 되어 있다.

스트래핑 핀 네 개는 리셋 시 래치되어 부팅 파라미터를 정한다.

| 핀 | 역할 | 기본 상태 |
|---|---|---|
| GPIO0 | 부팅 모드 (GPIO46과 조합) | 약한 풀업 (1 → SPI Boot) |
| GPIO46 | 부팅 모드·ROM 메시지 출력 | 약한 풀다운 (0) |
| GPIO45 | VDD_SPI 전압 | 약한 풀다운 (0 → 3.3 V) |
| GPIO3 | JTAG 신호원 | 플로팅 — 내부 풀 저항 없음, 외부 회로가 정해야 함 |

GPIO0 = 1이면 SPI Boot(플래시에서 실행), GPIO0 = 0 & GPIO46 = 0이면 Joint Download Boot(UART0 또는 USB로 다운로드)다. 래치는 리셋 뒤 3 ms 홀드 시간 후 풀리고 그 뒤 핀은 일반 IO로 쓸 수 있다. PSRAM 없는 모듈은 **전원 인가 시 외부 회로가 GPIO45를 High로 끌어올리지 않도록** 해야 한다.

## 주변장치

**I2C.** 컨트롤러 **2개**, 마스터/슬레이브 설정 가능. 표준 모드 100 kbit/s, 고속 모드 400 kbit/s, 풀업 강도에 따라 최대 800 kbit/s. 7비트·10비트 주소. **핀은 GPIO Matrix를 통해 어느 GPIO든 고를 수 있다.**

**UART.** 컨트롤러 3개(UART0·1·2), 최대 5 Mbps. UART0 기본 핀은 U0TXD/U0RXD = GPIO43/GPIO44, UART1은 GPIO17/GPIO18이며 모두 GPIO Matrix로 옮길 수 있다. 부팅 시 ROM 메시지는 기본으로 UART0과 USB Serial/JTAG 양쪽에 찍힌다.

**USB Serial/JTAG 컨트롤러.** 내장 PHY를 쓰는 USB 풀스피드 장치. CDC-ACM(시리얼 포트 에뮬레이션)과 JTAG 어댑터 기능이 하드와이어로 고정되어 있고, 내장 PHY라 호스트 PC 연결에 외부 부품이 거의 필요 없다. CDC-ACM은 대부분의 현대 OS에서 플러그앤플레이이며, 호스트가 칩 리셋과 다운로드 모드 진입을 제어할 수 있다. USB_D−/USB_D+는 GPIO19/GPIO20이며 USB OTG와 시분할로 공유한다.

**카메라 인터페이스.** LCD·카메라 컨트롤러가 8~16비트 DVP 이미지센서를 최대 40 MHz 클럭으로 받는다. 핀은 GPIO Matrix에서 고른다.

**SAR ADC.** 12비트 2개, 20채널(GPIO1~GPIO20). **온도센서.** −20~110 °C 범위이나 칩 내부 온도 감지용이며, 클럭 주파수·IO 부하에 따라 달라지고 일반적으로 주위온도보다 높다. **터치센서.** 14핀이나 CS(Conducted Susceptibility) 시험을 통과하지 못해 응용이 제한된다고 원문이 밝힌다.

그 밖에 SPI2/3, I2S 2개, TWAI(ISO 11898-1, CAN 2.0 호환), SD/MMC 호스트, LED PWM 8채널, MCPWM 2개, RMT, PCNT 4개가 있다.

## 전기 특성

| 항목 | 값 |
|---|---|
| 공급전압 VDD33 | 권장 3.0 / 3.3 / 3.6 V (최소/전형/최대), 절대 최대 3.6 V |
| 외부 전원이 공급해야 하는 전류 | 최소 0.5 A |
| VIH / VIL | 0.75 × VDD ~ VDD + 0.3 / −0.3 ~ 0.25 × VDD |
| VOH / VOL | ≥ 0.8 × VDD / ≤ 0.1 × VDD |
| 소스/싱크 전류 (PAD_DRIVER = 3) | 40 mA / 28 mA |
| 내부 약한 풀업/풀다운 | 45 kΩ |
| 핀 정전용량 | 2 pF |

소비전류(3.3 V, 25 °C 기준)는 Wi-Fi TX 피크가 802.11b 1 Mbps @20.5 dBm에서 355 mA, RX가 95~97 mA다. Modem-sleep에서는 클럭에 따라 13.2 mA(40 MHz, 듀얼코어 유휴, 주변장치 클럭 끔)에서 107.9 mA(240 MHz, 듀얼코어 128비트 접근, 주변장치 클럭 켬)까지다. Light-sleep 240 µA, Deep-sleep 7~8 µA, 전원 차단 1 µA. PSRAM 내장 칩은 이보다 높을 수 있다.

## RF

Wi-Fi 802.11b/g/n, 중심주파수 2412~2484 MHz, 802.11n 최대 150 Mbps. TX 전력 전형 17.0~20.5 dBm, RX 감도 −71.2(HT40 MCS7)~−98.2 dBm(11b 1 Mbps). Bluetooth LE는 Bluetooth 5·메시, 125 Kbps~2 Mbps, 2402~2480 MHz, 송신 −24.0~20.0 dBm, 감도 −92(2 Mbps)~−103.5 dBm(125 Kbps). Wi-Fi와 Bluetooth는 안테나 하나를 내부 공존 메커니즘으로 나눠 쓴다.

## 취급

습기차단봉투(MBB) 밀봉 상태로 <40 °C, 90 %RH 비결로 환경에 보관하고, MSL 3이므로 개봉 후 168시간 안에 25±5 °C, 60 %RH에서 납땜해야 하며 아니면 베이킹이 필요하다. ESD는 HBM ±2000 V, CDM ±500 V. 리플로우는 단 1회, 피크 235~250 °C. 초음파 용접기·세척기의 진동은 모듈 내 수정 발진기를 공진시켜 고장을 일으킬 수 있으므로 피해야 한다. EPAD 납땜은 필수는 아니나 방열에 도움이 된다.

## 인용할 만한 문구

- "ESP32-S3 has two I2C bus interfaces which are used for I2C master mode or slave mode, depending on the user's configuration." (5.2.1.2)
- "For I2C, the pins used can be chosen from any GPIOs via the GPIO Matrix." (5.2.1.2)
- "Ambient temperature specifies the recommended temperature range of the environment immediately outside the Espressif module." (Table 1·2 주석 6)
- "For modules with Octal SPI PSRAM, i.e., modules embedded with ESP32-S3R8 or ESP32-S3R16V, pins IO35, IO36, and IO37 are connected to the Octal SPI PSRAM and are not available for other uses." (Table 3 주석 b)
- "Note: Do not leave the EN pin floating." (Table 3)
- "Internal PHY, so no or very few external components needed to connect to a host computer." (5.2.1.8 USB Serial/JTAG)
