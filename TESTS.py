import json
from src.data.localities import localities

# Il tuo dizionario di partenza
data = localities

"""
data = {
    "data_one": {
        "subdata_one": "one",
        "subdata_two": "two",
        "subdata_three": "three",
        "subdata_four": "four",
        "subdata_five": "five",
    },
    "data_two": {
        "subdata_one": "A",
        "subdata_two": "B",
        "subdata_three": "C",
        "subdata_four": "D",
        "subdata_five": "E",
    },
}
---
localities = {
    "Italian": {
        "state": "Italia",
        "capital": "Roma",
        "latitude": 41.9028,
        "longitude": 12.4964,
        "timezone": "Europe/Rome",
        "months": [
... ecc.
"""

# 1. Estrazione e trasformazione dei dati
subdata = {
    v["capital"]: {
        "state": v["state"],
        "latitude": v["latitude"],
        "longitude": v["longitude"],
        "timezone": v["timezone"]
    }
    for v in data.values()
}

# 2. Salvataggio nel file "subdatafile.py" come codice Python valido
with open("cities.py", "w", encoding="utf-8") as f:
    # Scrive la dichiarazione della variabile seguita dal dizionario formattato
    f.write(f"cities = {json.dumps(subdata, indent=2)}\n")
