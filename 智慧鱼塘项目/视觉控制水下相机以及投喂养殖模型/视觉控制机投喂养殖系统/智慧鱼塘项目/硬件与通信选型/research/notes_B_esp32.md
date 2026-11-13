# ESP32 系列 Datasheet v5.3 (官方)
URL: https://documentation.espressif.com/esp32_datasheet_en.html
- Features: "Power consumption in Deep-sleep mode is 10 µA"
- Table 4-2 Power Consumption by Power Modes:
  Active (RF working): Wi-Fi Tx/Rx 见 Table 5-4
  Modem-sleep 240MHz 双核 30~68mA; 160MHz 双核 27~44mA / 单核 27~34mA; 80MHz 双核 20~31mA / 单核 20~25mA
  Light-sleep 0.8 mA
  Deep-sleep: ULP 开启 150 µA; ULP sensor-monitored pattern 100 µA @1% duty; RTC timer + RTC memory 10 µA
  Hibernation (仅 RTC timer) 5 µA
  Power off (CHIP_PU 拉低) 1 µA
- Table 5-4 Current Consumption Depending on RF Modes (3.3V, 25C, 50% duty):
  TX 802.11b DSSS 1Mbps @+19.5dBm: 240 mA (typ)
  TX 802.11g OFDM 54Mbps @+16dBm: 190 mA
  TX 802.11n OFDM MCS7 @+14dBm: 180 mA
  RX 802.11b/g/n: 95~100 mA
  TX BT/BLE @0dBm: 130 mA
  RX BT/BLE: 95~100 mA
- 供电: VDDA/VDD3P3 2.3~3.6V (typ 3.3V); 外部电源需提供 >=0.5A

# ESP32-S3 系列 Datasheet v1.7 (官方)
URL: https://documentation.espressif.com/esp32-s3_datasheet_en.html
- Table 4-6 Wi-Fi Current Consumption in Active Mode (3.3V, 25C, 100% duty):
  TX 802.11b 1Mbps @21dBm: 340 mA (峰值)
  TX 802.11g 54Mbps @19dBm: 291 mA
  TX 802.11n HT20 MCS7 @18.5dBm: 283 mA
  TX 802.11n HT40 MCS7 @18dBm: 286 mA
  RX 802.11b/g/n HT20: 88 mA ; RX 802.11n HT40: 91 mA
  注: CPU 单核 80MHz 32-bit 访问, 另一核 idle
- Table 4-7 Modem-sleep: 40MHz WAITI 13.2mA(Typ1) / 240MHz 双核 128-bit 91.7mA(Typ1) ~107.9mA(Typ2)
  注: 若访问 flash, 80Mbit/s SPI 2-line 模式额外 ~10mA
- Table 4-8 Current Consumption in Low-Power Modes:
  Light-sleep (VDD_SPI 和 Wi-Fi 断电, GPIO 高阻): 240 µA
  Deep-sleep (RTC memory + RTC 外设上电): 8 µA
  Deep-sleep (仅 RTC memory 上电, RTC 外设断电): 7 µA
  Power off (CHIP_PU 拉低): 1 µA
  注: 内嵌 PSRAM 的型号需另加 PSRAM 功耗: 8MB 8-line PSRAM(3.3V) +140µA; (1.8V) +200µA; 2MB 4-line PSRAM(3.3V) +40µA

# 乐鑫 ESP-Techpedia《ESP 低功耗入门》
URL: https://docs.espressif.com/projects/esp-techpedia/zh_CN/latest/esp-friends/advanced-development/performance/lowpower/lowpower-fundamental.html
- Active 模式底电流约 20~40 mA
- Light sleep 底电流: ESP32-C3 130 µA; ESP32-S3 240 µA
- Deep sleep 底电流: ESP32-C3 5 µA; ESP32-S3 7 µA
- 四种模式: Active / Modem sleep / Light sleep / Deep sleep
