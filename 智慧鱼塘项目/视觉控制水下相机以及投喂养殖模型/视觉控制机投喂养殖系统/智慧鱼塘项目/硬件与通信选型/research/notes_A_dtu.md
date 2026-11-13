# 有人 USR-DR154 (PUSR "口红" DTU) 官方规格书
URL: https://www.pusr.com/uploads/20240903/3fecdb5e29c6507a75ff701435196e0e.pdf
- Power Supply: 5-24V DC, 12V/1A recommended
- Consumption: Average 0.8W, Max 3.5W
- 天线: 1*SMA Female
=> 换算: 0.8W / 12V ≈ 67 mA 平均; 3.5W / 12V ≈ 292 mA 峰值

# 亿佰特 E840-DTU(EC04) 4G Cat-1 DTU (官网产品页)
URL: https://www.ebyte.com/product/1687.html
- 工作电压 DC 8~28V
- 功耗(官方, 与环境有关仅供参考): 待机 59mA @12V; 入网 120mA @12V; 传输 120mA @12V
- 尺寸 100*87*25mm, 213g, 工作温度 -40~+80C
=> 待机约 0.71W@12V; 传输约 1.44W@12V

# 亿佰特 E840-DTU(4G-02) 技术手册 PDF (老款, 全网通 5模13频)
URL: https://www.ebyte.com/Uploadfiles/Files/2019-4-22/2019422141749027.pdf
- 耗流(典型值): 11uA @关机 ; 1.8mA @LTE休眠(PF=128) ; 1.5mA @LTE休眠(PF=256) ; 20mA @空闲
- 工作电压 DC 8~28V, 尺寸 82x84x24mm
- 注意: 该型号非 Cat-1 而是多模 LTE Cat-4/3G/2G DTU, 数据仅作对照

# Quectel EC800M-CN 硬件设计手册 V1.3 表37
URL: https://python.quectel.com/wp-content/uploads/2024/09/Quectel_EC800MEG810M%E7%B3%BB%E5%88%97_%E7%A1%AC%E4%BB%B6%E8%AE%BE%E8%AE%A1%E6%89%8B%E5%86%8C_V1.3.pdf
- 关机模式: 21.23 uA (不带GNSS) / 38.72 uA (带GNSS)
- 休眠模式: AT+CFUN=0: 0.89mA ; CFUN=4: 1.01mA ; LTE-FDD PF=256: 1.11mA ; PF=128: 1.20mA ; PF=64: 1.42mA ; PF=32: 1.82mA
- 空闲模式: LTE-FDD PF=64 USB断开 17.27mA / USB连接 30.28mA
- LTE 数据传输: FDD B1 606mA / B3 521mA / B5 516mA / B8 496mA / TDD B34 205mA / B38 211mA
- VBAT 峰值电流(最大发射功率等级): 典型 1.5A, 最大 2A
- VBAT 范围 3.4/3.8/4.3V
- 该手册未给出 PSM 单独条目 (grep "PSM" = 0 次)

# Quectel EC200A 系列 QuecOpen 硬件设计 V1.1 表40 (EC200A-CN)
URL: http://python.quectel.com/en/wp-content/uploads/sites/2/2024/11/Quectel_EC200A_Series_QuecOpen_Hardware_Design_V1.1.pdf
- OFF state: 12 uA
- Sleep: AT+CFUN=0: 0.84mA ; LTE-FDD PF=256: 1.12mA ; PF=128: 1.26mA ; PF=64: 1.54mA ; PF=32: 2.16mA ; WCDMA PF=64: 2.44mA
- Idle: LTE-FDD PF=64 USB断开 14.41mA / USB连接 37.68mA
- LTE 数据传输: FDD B1 @22.87dBm 609mA / B3 552mA / B5 528mA / B8 564mA
- IVBAT_RF 峰值供电电流: 最大 2.0 A
- 注意: EC200A 是 LTE Cat 4 模块, 非 Cat-1
