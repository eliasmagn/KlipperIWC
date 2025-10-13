# KlipperIWC

KlipperIWC ist ein kleiner FastAPI-Dienst, der eine grafische Oberfläche für die
Erstellung von Klipper-Konfigurationsdateien bereitstellt. Anwender wählen einen
Drucker-Preset und kombinieren Komponenten wie Toolhead, Controller-Board oder
Z-Probe. Das Backend setzt die Auswahl zu einer vollständigen `printer.cfg`
zusammen, ergänzt optionale Parameter-Overrides und individuelle Makros und
stellt das Ergebnis direkt im Browser dar.

## Funktionsumfang

- Vordefinierte Drucker-Presets (z. B. Voron Trident, Ender-3)
- Konfigurierbare Komponenten-Kategorien mit fertigen Snippets
- Zusammenführung der Snippets zu einer konsistenten Klipper-Konfiguration
- Optionales Einfügen eigener Parameter und Makros
- UI wird direkt über FastAPI ausgeliefert – keine zusätzliche Build-Toolchain

## Voraussetzungen

- Python 3.11 oder neuer
- Optional: Docker 24+

## Installation und Betrieb

### Produktionsdeployment

Das Skript `deploy.sh` richtet eine virtuelle Umgebung ein, installiert die
Abhängigkeiten und startet anschließend einen Uvicorn-Server im Hintergrund.

```bash
./deploy.sh
```

Logs landen in `logs/app.log`, die Prozess-ID in `logs/app.pid`.

### Entwicklungsumgebung

Für lokale Entwicklung steht `deploy_dev.sh` bereit. Das Skript installiert alle
Abhängigkeiten und gibt anschließend das Kommando zum Starten mit Live-Reload
aus.

```bash
./deploy_dev.sh
# Ausgegebenen Hinweisen folgen, z. B.:
. .venv/bin/activate
uvicorn klipperiwc.app:create_app --factory --host 0.0.0.0 --port 8000 --reload --log-level debug
```

Nach dem Start ist die UI unter `http://localhost:8000/` erreichbar.

### Docker

Ein containerisiertes Deployment ist über das `Dockerfile` möglich.

```bash
docker build -t klipperiwc .
docker run -p 8000:8000 klipperiwc
```

## API

Die API stellt einen kleinen Satz an Endpunkten bereit, die auch von externen
Tools genutzt werden können:

| Methode | Pfad | Beschreibung |
| ------- | ---- | ------------ |
| GET | `/api/configurator/presets` | Liefert verfügbare Drucker-Presets |
| GET | `/api/configurator/component-groups` | Liefert konfigurierbare Komponenten |
| POST | `/api/configurator/generate` | Erzeugt eine vollständige Konfiguration |

Der POST-Endpoint erwartet ein JSON mit `printer_preset_id`, optionalen
`components`, `parameter_overrides` und `custom_macros`. Die Antwort enthält die
fertige Konfiguration sowie eventuelle Warnhinweise.

## Entwicklung

Die statischen Presets und Komponenten sind in `klipperiwc/configurator.py`
definiert. Die zugehörigen Pydantic-Modelle liegen in
`klipperiwc/models/configurator.py`. Tests verwenden `pytest` und den
`TestClient` von FastAPI (`tests/test_configurator_api.py`). Neue Presets oder
Komponenten sollten mit kurzen Beschreibungen und Snippets ergänzt werden, damit
die UI die Auswahl verständlich darstellen kann.
