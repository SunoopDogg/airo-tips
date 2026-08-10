---
title: ESP32-S3-WROOM-1
type: entity
tags: [sensor-spec, 컨트롤러, 모의장치]
created: 2026-09-07
updated: 2026-09-07
status: developing
sources: ["[[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]", "[[Sensirion SEN5x Datasheet]]", "[[PCA9548A Datasheet]]", "[[P82B715 Datasheet]]"]
---

에스프레시프의 Wi-Fi + Bluetooth LE MCU 모듈. 모의장치에서 환경센서 세 대를 읽어 PC로 넘기는 컨트롤러이며, 쓰는 변형은 ESP32-S3-WROOM-1-N16R8이다.

## 무엇인가

ESP32-S3 계열 SoC(Xtensa 듀얼코어 LX7, 최대 240 MHz)에 16 MB Quad SPI 플래시와 8 MB Octal SPI PSRAM을 얹은 모듈이 N16R8이다 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]). 이 변형은 [[모의장치]]의 [[SEN55]] 3대를 I2C로 읽고 USB로 PC에 중계하는 역할을 맡는다 (사용자 확인 2026-09-07).

## N16R8 변형이 가져오는 제약

**동작온도 상한이 65 °C다.** Octal SPI PSRAM 변형(R8·R16V)의 권장 주위온도는 −40~65 °C이고, PSRAM 없는 변형의 85 °C보다 낮다. 여기서 주위온도는 모듈 바로 바깥 환경의 온도다 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]). PSRAM ECC를 켜면 85 °C까지 올라가지만 PSRAM 가용 용량이 1/16 줄어든다 (같은 문헌). 이 모듈은 챔버 상단 외부에 놓이고, 챔버 내부 시험 조건에 직접 노출되지 않는다 (사용자 확인 2026-09-07).

**IO35·IO36·IO37을 쓸 수 없다.** 이 세 핀은 Octal SPI PSRAM에 연결되어 있다 (같은 문헌). 나머지 GPIO 중 스트래핑 핀 GPIO0·GPIO3·GPIO45·GPIO46도 부팅 시 상태가 잡히므로 (같은 문헌) I2C 배선에서는 피하는 것이 안전하다.

## SEN55 3대 연결

**SEN55 주소가 0x69로 고정이라 한 버스에 3대를 못 붙인다.** SEN55는 I2C 주소가 0x69이고 명령 목록에 주소 변경 명령이 없다 ([[Sensirion SEN5x Datasheet]]). 그래서 ESP32-S3의 하드웨어 I2C 1버스를 [[PCA9548A]] 멀티플렉서에 물리고, 그 채널 0~2에 SEN55를 한 대씩 연결하기로 했다 (사용자 확인 2026-09-07). PCA9548A 주소는 A0=A1=A2=GND로 0x70 고정이고, RESET 핀은 쓰지 않고 VCC로 풀업만 한다 (같은 확인). ESP32-S3의 I2C는 2개이고 핀은 GPIO Matrix로 어느 GPIO든 고를 수 있으므로 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]) 나머지 1버스는 예비로 남는다.

**논리 레벨은 맞는다.** ESP32-S3의 IO는 3.0~3.6 V 전원 도메인이고 VIH는 0.75 × VDD 이상이다 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]). SEN55의 SDA/SCL은 "LVTTL 3.3V compatible"이고 VIH 최소 2.31 V, VIL 최대 0.99 V, VOL 최대 0.4 V다 ([[Sensirion SEN5x Datasheet]]). 따라서 레벨 시프터 없이 직결된다. SEN55 쪽 SCL·SDA는 오픈드레인이라 외부 풀업(예: 10 kΩ)이 필요하고, 버스마다 따로 달아야 한다 (같은 문헌).

**속도는 SEN55가 정한다.** ESP32-S3 I2C는 400 kbit/s 이상까지 되지만 SEN55는 표준 모드 100 kbit/s가 최대이고 클럭 스트레칭을 쓰지 않는다 ([[Sensirion SEN5x Datasheet]]). 세 버스 모두 100 kbit/s 이하다.

**배선 길이.** SEN55 데이터시트는 전자기 간섭과 크로스토크를 피하려면 I2C 배선을 10 cm 미만으로 하거나 차폐 케이블을 쓰라고 한다 (같은 문헌). 모듈과 [[PCA9548A]]는 챔버 상단 외부에 두고 SEN55만 챔버 내부에 두기로 했으므로 (사용자 확인 2026-09-07), PCA9548A~SEN55 배선이 챔버 벽을 가로지른다. 이 구간에 [[P82B715]] 버스 익스텐더를 채널마다 한 쌍씩 넣는 안과 차폐 케이블을 쓰는 안을 고려 중이며, 둘 다 확정은 아니다 (사용자 확인 2026-09-07). P82B715를 쓰면 VCC 5 V를 USB VBUS에서 분기하고 대기 전류 개당 14 mA가 ([[P82B715 Datasheet]]) USB 전류 예산에 더해진다. [[모의장치]]의 Contradictions 참조.

## 전원

SEN55는 5 V ± 10% 공급을 받고 측정 모드 평균 63 mA, 피크 100 mA다 ([[Sensirion SEN5x Datasheet]]). 모듈은 3.0~3.6 V이고 외부 전원은 최소 0.5 A를 공급해야 한다 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]). SEN55 3대의 5 V는 **USB VBUS에서 분기**하기로 했다 (사용자 확인 2026-09-07). 세 대 평균 약 190 mA에 모듈 자체 소비(Modem-sleep 최대 107.9 mA, Wi-Fi TX 시 피크 355 mA)를 더한 값이 USB 포트에서 나와야 한다.

## PC 연결

측정값은 **USB Serial/JTAG 컨트롤러의 CDC-ACM**으로 PC에 보낸다 (사용자 확인 2026-09-07). 내장 PHY라 외부 부품이 거의 필요 없고, 대부분의 OS에서 플러그앤플레이이며, 호스트가 칩 리셋과 다운로드 모드 진입을 제어할 수 있다 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]). USB_D−/USB_D+는 GPIO19/GPIO20이므로 이 두 핀도 I2C에 쓸 수 없다 (같은 문헌).

역할 분담은 **PC가 명령하고 ESP는 중계**한다 (사용자 확인 2026-09-07). VOC 알고리즘 상태 저장·복원(0x6181)과 조건별 출발점 맞추기, 벤팅 임계값 판정은 PC 쪽이 하고, 모듈은 I2C 브리지다. [[VOC Index]] 참조.

## 이 모듈이 하지 않는 것

카메라는 별도 장비이고 이 모듈과 무관하다 (사용자 확인 2026-09-07). ESP32-S3에 DVP 카메라 인터페이스가 있지만 ([[ESP32-S3-WROOM-1 & WROOM-1U Datasheet]]) [[불꽃검출 알고리즘]]의 영상은 다른 경로로 PC에 들어간다. Wi-Fi·Bluetooth도 이 구성에서는 쓰지 않는다.

내장 온도센서는 칩 내부 온도용이며 주위온도보다 높게 나온다 (같은 문헌). 챔버 온도는 [[SEN55]]의 온도 채널이 잰다.
