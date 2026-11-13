# Quectel EC200U/EG915U Low Power Mode App Note V2.0 (2024-04-26)
URL: https://quectel.com/content/uploads/2024/05/Quectel_EC200UEG91xUEG915G_Series_Low_Power_Mode_Application_Note_V2.0.pdf
- Table3 EC200U avg current, TCP long conn, 100B/60s, Band3:
  Mobile LTE: normal sleep 17.41mA (enter 10.2s); enhanced 6.60mA (2.5s)
  Unicom LTE: normal 31.87mA (20.2s); enhanced 5.84mA (2.1s)
  Telecom LTE: normal 11.24mA (5.8s); enhanced 7.26mA (3.0s)
- Figure1: normal sleep, peak duration ~20s after RX, avg within 60s = 29.92 mA
- Figure2: enhanced sleep, peak ~2s, avg within 60s = 5.63 mA
- Table4 EG915U PSM test (wake->TCP short conn->send 20B->back to PSM):
  PSM 595s @ 0.005mA = 0.943 uAh
  init+wait 1.619s @33.411mA = 15.032 uAh
  network camping 0.393s @63.296mA = 6.917 uAh
  data TX/RX + RRC release 0.840s @170.164mA = 39.750 uAh
  IDLE(T3324 wait) 2.298s @12.264mA = 7.829 uAh
  PSM 595s @0.005mA = 0.944 uAh
  TOTAL 5.210s active window, avg 48.625mA, 69.643 uAh per wake cycle
  -> PSM avg current stable within 6 uA
- Constraint: if (T3412 - T3324) issued by network < 5 min, module will NOT enter PSM
- Enhanced sleep mode: extra signalling burden -> risk of network punishment / cannot go online
