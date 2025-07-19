from labapp.models import Component

components = [
    "Aplab DUAL OUTPUT REGULATED DC POWER SUPPLY",
    "Aplab REGULATED DC POWER SUPPLY",
    "DC REGULATED POWER SUPPLY (30-0-30V to 2A)",
    "Excel DUAL , MULTI DC REGULATED  POWER SUPPLY",
    "Excel Technologies +15v to -15v",
    "Excel Technologies ± 5V POWER SUPPLY",
    "Excel Technologies ±15V POWER SUPPLY",
    "METRAVI XB-33CF multimeter",
    "MetroQ MTQ 70A DIGITAL MULTIMETER (R)",
    "SCIENTIFIC 2 MHz Function Generator SM5060-2",
    "SIGLENT SDS 1102CML",
    "Scientech 3MHz function-pulse Generator",
    "Scientific 30V, 3A Dual Power Supply PSD3203",
    "Scientific 3MHz Universal Funtion Generator",
    "Scientific SM7023 3.75 DMM",
    "Tektronix DSO TDS 2002C",
    "Trinity TDM-3040",
    "Vinytics DUAL DC RYEGULATED POWER SUPPLY 0-30V , 2A",
    "Vinytics POWER SUPPLY (ALL IN ONE) 0-30V per 2A, 5V, 0- ±15V per 1A  DUAL TRACKING (1)"
]

for name in components:
    Component.objects.get_or_create(name=name.strip(), defaults={'quantity_available': 19})
