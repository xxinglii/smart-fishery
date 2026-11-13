# OASIS MQTT 3.1.1 规范 (官方 PDF)
URL: https://groups.oasis-open.org/higherlogic/ws/public/download/56950/mqtt-v3.1.1-os_plus_eratta_01.pdf
- 固定头 = 1 字节 (报文类型 4bit + 标志 4bit) + Remaining Length
- §2.2.3 Remaining Length: 变长编码, 值 <=127 用 1 字节; 最多 4 字节 (最大 268,435,455 字节)
  => 固定头最小 2 字节, 最大 5 字节
- PINGREQ/PINGRESP: 无变量头、无 payload -> 整包仅 2 字节 (0xC0 0x00 / 0xD0 0x00)
- CONNECT 含 Protocol Name("MQTT" 6字节 UTF-8 长度前缀+4), Protocol Level(1), Connect Flags(1), Keep Alive(2), Client ID, 用户名/密码等
- PUBLISH: 固定头 + Topic Name(2字节长度前缀 + N 字节) + Packet Identifier(仅 QoS>0, 2字节) + Payload

# ETSI TR 137 901-5 V16.11.0 (2023-10) 3GPP TR 37.901-5 (官方)
URL: https://www.etsi.org/deliver/etsi_tr/137900_137999/13790105/16.11.00_60/tr_13790105v161100p.pdf
- Table 5.4.4-1 各层头部开销 (octet): TCP 24 ; UDP 8 ; IP 40(IPv6)/24(IPv4) ; SDAP 1(SA) ; PDCP 7 ; RLC 5 ; MAC 3
- Table 5.4.4-2 (IPv6, 1500 MTU): 用 TCP 时 MAC PDU 1516 vs 上层 1436 -> 开销 5.5%
- Table 5.4.4-3 (IPv4): TCP 1516/1452 -> 4.4% ; UDP 1516/1468 -> 3.1%
- PDCP-SN + MAC-I 最大 7 octets (TS 38.523-1 §6.3.2/6.3.4)
- LTE: DRB PDCP 头最多 3 octets (TS 36.323)

# 经典 TLS 1.3 握手字节数
URL: https://pqprobe.com/blog/handshake-bytes-on-the-wire
- "A classical TLS 1.3 handshake is four to six kilobytes on the wire."
- 最大贡献是证书链: 2~3 KB ("The largest single contributor is the certificate chain at 2 to 3 KB.")
- X25519 密钥交换: 客户端 key share 32 B + 服务端 key share 32 B = 64 B
- P-256 ECDHE (uncompressed): 65+65 = 130 B
- 签名开销(每链条目): Ed25519 44+64=108 B ; ECDSA-P256 91+72=163 B ; RSA-2048 294+256=550 B
- TCP IW10 = 10 MSS ≈ 14.6 KB, 经典握手可放进首个窗口
- (注: 该文主题是 PQC 尺寸参考; 经典 TLS 数字与证书链尺寸对本文有效)

# ESP32 datasheet 供电要求 (见 notes_B)
