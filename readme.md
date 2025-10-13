# KlipperIWC

KlipperIWC ist eine FastAPI-basierte Backend-Anwendung, die als Grundlage für eine Integrations- und Steueroberfläche von Klipper-3D-Druckerinstallationen dient. Dieses Repository enthält alle Skripte, um die Software lokal, auf einem Server oder innerhalb eines Containers zu betreiben.

> **Hinweis:** Eine Benutzerverwaltung bzw. ein Login ist derzeit nicht vorgesehen und wird erst in einer späteren Phase ergänzt.

Neue Board- oder Druckerdefinitionen werden aktuell über Pull Requests im GitHub-Repository gepflegt. Sobald eine Authentifizierung verfügbar ist, sollen Anwender fehlende Hardware direkt in der Weboberfläche ergänzen können. Als Übergangslösung existiert bereits eine visuelle Oberfläche, um Pins, Stecker und MCU-Pins zu annotieren.

## Voraussetzungen

- Python 3.11 oder neuer
- SQLite 3 (in der Regel bereits im Betriebssystem enthalten)
- Optional: Docker 24+

## Installation und Betrieb

### Produktionsdeployment

Das Skript `deploy.sh` richtet eine virtuelle Umgebung ein, installiert alle Abhängigkeiten und startet den Service als Daemon.

```bash
./deploy.sh
```

Logs werden im Verzeichnis `logs/app.log` geschrieben und die Prozess-ID liegt in `logs/app.pid`.

### Entwicklungsumgebung

Für lokale Entwicklung steht `deploy_dev.sh` bereit. Das Skript installiert alle Abhängigkeiten und gibt anschließend das Kommando aus, um den Server mit Live-Reload und Debug-Logging zu starten.

```bash
./deploy_dev.sh
# Hinweis aus dem Skript folgen, z. B.:
. .venv/bin/activate
export APP_ENV=development
export LOG_LEVEL=debug
uvicorn klipperiwc.app:create_app --factory --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Datenbank-Migrationen

KlipperIWC nutzt SQLAlchemy mit einer SQLite-Datenbank im Verzeichnis `data/klipperiwc.sqlite3`. Eigene Pfade lassen sich über
die Umgebungsvariable `DATABASE_URL` konfigurieren (z. B. `sqlite:////pfad/zur/datei.db`).

**Setup:**

```bash
# Virtuelle Umgebung aktivieren (falls noch nicht geschehen)
. .venv/bin/activate

# Erste Migration anwenden
alembic upgrade head
```

**Neue Migration erzeugen:**

```bash
alembic revision --autogenerate -m "kurze beschreibung"
alembic upgrade head
```

Die Generierung nutzt die SQLAlchemy-Modelle innerhalb von `klipperiwc.db`. Zusätzliche Tabellen oder Änderungen müssen dort als
ORM-Modelle gepflegt werden.

### Docker

Ein containerisiertes Deployment ist über das bereitgestellte `Dockerfile` möglich.

```bash
docker build -t klipperiwc .
docker run -p 8000:8000 --env APP_ENV=production klipperiwc
```

## Projektstruktur

```
klipperiwc/          # FastAPI-Anwendung
├── __init__.py
├── app.py
├── api/             # HTTP-Endpunkte (FastAPI Router)
├── db/              # SQLAlchemy-Engine, Session-Handling und Modelle
│   ├── __init__.py
│   ├── models.py
│   └── session.py
├── repositories/    # CRUD-Helfer für persistente Daten
├── services/        # Service-Layer für Geschäftslogik
└── websocket/       # Websocket-Gateway für Status-Streaming
requirements.txt     # Python-Abhängigkeiten
deploy.sh            # Produktionsdeployment
deploy_dev.sh        # Entwicklungssetup
alembic/             # Datenbankmigrationen
└── versions/        # Migration-Skripte
Dockerfile           # Container-Build
```

## HTTP-API

Die Anwendung stellt Status-Endpunkte, einen Upload-Service für Board-Grafiken und ein
Moderations-API bereit. Solange noch keine Anbindung an einen realen Klipper-Service
existiert, liefern die Status-Endpunkte repräsentative Beispielwerte. Bei jedem Abruf
wird der Status zusätzlich in einer Historientabelle gespeichert, sodass spätere
Visualisierungen auf die aufgezeichneten Messwerte zugreifen können. Parallel steht ein
Websocket-Kanal bereit, der neue Statusmeldungen automatisch an verbundene Clients
weiterleitet.

| Methode | Pfad               | Beschreibung                                      |
| ------- | ------------------ | ------------------------------------------------- |
| GET     | `/api/status`      | Aggregierter Druckerstatus inkl. aktiver und wartender Jobs |
| GET     | `/api/jobs`        | Liste aus aktivem Druckauftrag und Warteschlange |
| GET     | `/api/temperatures`| Letzte Temperaturwerte für Hotend, Heizbett etc. |
| POST    | `/api/board-assets/` | Lädt Board-Grafiken samt Metadaten hoch (Upload-Token erforderlich) |
| PATCH   | `/api/board-assets/{id}` | Aktualisiert Metadaten eines Assets (Upload-Token erforderlich) |
| GET     | `/api/board-assets/` | Listet Assets (standardmäßig nur freigegebene) |
| GET     | `/api/board-assets/moderation/pending` | Liefert Moderations-Warteschlange (Moderator-Token erforderlich) |
| PATCH   | `/api/board-assets/{id}/moderation` | Trifft Moderationsentscheidung (Moderator-Token erforderlich) |

### Persistente Statushistorie & Aufbewahrung

Die Tabellen `status_history`, `temperature_history` und `job_history` speichern jede
eingehende Statusmeldung mitsamt Einzelmessungen. Ein Hintergrundtask entfernt Altdaten
in regelmäßigen Abständen. Die Konfiguration erfolgt über Umgebungsvariablen:

- `STATUS_HISTORY_RETENTION_DAYS` (Standard: `30`): Wie viele Tage Historie maximal
  aufbewahrt werden.
- `STATUS_HISTORY_CLEANUP_INTERVAL_SECONDS` (Standard: `3600`): Wie häufig der
  Bereinigungstask ausgeführt wird.

Der Task wird beim Start des FastAPI-Servers aktiviert und läuft, solange der Dienst
aktiv ist.

Die Antworten basieren auf Pydantic-Modellen unter `klipperiwc/models/status.py` bzw.
`klipperiwc/models/board_assets.py` und lassen sich dadurch leicht erweitern oder zur
Schema-Dokumentation exportieren.

## Board-Asset Upload & Moderation

Uploads erfolgen über `/api/board-assets/` mit `multipart/form-data`. Pflichtfeld ist die
Datei (`file`), optionale Formularfelder sind `title`, `description`, `visibility`
(`private`/`public`) und `uploaded_by`. Der Header `X-Board-Assets-Key` muss mit der
Umgebungsvariablen `BOARD_ASSET_UPLOAD_TOKEN` übereinstimmen. Für Moderationsendpunkte
(`GET /api/board-assets/moderation/pending`, `PATCH /api/board-assets/{id}/moderation`)
wird der Header `X-Board-Assets-Moderator` gegen `BOARD_ASSET_MODERATION_TOKEN`
geprüft.

Beispiel-Upload mit `curl`:

```bash
curl -X POST "http://localhost:8000/api/board-assets/" \
  -H "X-Board-Assets-Key: $BOARD_ASSET_UPLOAD_TOKEN" \
  -F "file=@./assets/board.svg" \
  -F "title=Voron Toolhead" \
  -F "visibility=private"
```

### Storage-Konfiguration

Der Storage-Layer unterstützt lokales Dateisystem sowie S3-kompatible Backends.
Konfiguration über Umgebungsvariablen:

| Variable | Beschreibung |
| -------- | ------------ |
| `BOARD_ASSET_STORAGE_BACKEND` | `local` (Standard) oder `s3` |
| `BOARD_ASSET_LOCAL_PATH` | Ablageort für lokale Speicherung (Standard: `./var/board-assets`) |
| `BOARD_ASSET_LOCAL_PUBLIC_URL` | Optionaler Basis-URL-Präfix für generierte Links |
| `BOARD_ASSET_S3_BUCKET` | Bucket-Name für S3-Uploads |
| `BOARD_ASSET_S3_REGION` | Region des Buckets (optional, z. B. `eu-central-1`) |
| `BOARD_ASSET_S3_ENDPOINT` | Optionaler Endpoint für S3-kompatible Dienste |
| `BOARD_ASSET_S3_PUBLIC_URL` | Optionaler Basis-Link für ausgelieferte Assets |
| `BOARD_ASSET_MAX_BYTES` | Maximale Dateigröße in Bytes (Standard: 20 MB) |
| `BOARD_ASSET_UPLOAD_TOKEN` | Token für Upload- und Metadatenänderungen |
| `BOARD_ASSET_MODERATION_TOKEN` | Token für Moderations-Endpunkte |

Jeder Upload erzeugt einen Datensatz in `board_assets` sowie eine Historie in
`board_asset_moderation_events`. Assets starten im Status `pending` und müssen über den
Moderationsendpunkt freigegeben werden, bevor sie in Standardlisten erscheinen.

## Websocket-Streaming

Für Live-Updates steht ein Websocket-Endpunkt unter `ws://<host>:<port>/ws/status`
bereit. Nach erfolgreicher Verbindung sendet der Server automatisch neue Statusmeldungen,
sobald sie über die HTTP-API erzeugt oder von zukünftigen Backends eingespielt werden.
Jede Nachricht folgt dem Schema:

```json
{
  "type": "status",
  "payload": {
    "state": "printing",
    "message": "...",
    "uptime_seconds": 123,
    "active_job": { ... },
    "queued_jobs": [ ... ],
    "temperatures": [ ... ]
  }
}
```

Die Verbindung ist aktuell offen zugänglich; Platzhalter für Authentifizierung und
Rate-Limits sind bereits im Gateway hinterlegt und werden in Phase 2 mit echter Logik
hinterlegt. Clients sollten Verbindungsabbrüche abfangen und bei Bedarf automatisch
reconnecten.

## Weiterführende Schritte

Siehe `roadmap.md` für geplante Erweiterungen und `checklist.md` für den aktuellen Arbeitsfortschritt. Der aktuelle Fokus liegt auf der Definition der Status-API, der Integration eines Klipper-Service-Layers und dem Aufbau einer kleinen Statushistorie, um den Weg in Richtung produktiver Einsatz zu ebnen.

## Interaktiver Board-Designer (Prototyp)

Der Prototyp für die Board-Visualisierung ist unter `http://localhost:8000/board-designer` verfügbar, sobald der Server läuft. Auf der Zeichenfläche lassen sich Rechtecke und Kreise platzieren, um Steckverbinder oder Pin-Gruppen hervorzuheben. Anschließend können individuelle Labels vergeben werden, die in der Seitenleiste als Referenz erscheinen. Die erzeugten Markierungen dienen als Grundlage für künftige Board-Definitionen, die weiterhin über GitHub versioniert werden.
