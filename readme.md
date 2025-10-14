# KlipperIWC

KlipperIWC ist eine FastAPI-basierte Backend-Anwendung, die als Grundlage für eine Integrations- und Steueroberfläche von Klipper-3D-Druckerinstallationen dient. Dieses Repository enthält alle Skripte, um die Software lokal, auf einem Server oder innerhalb eines Containers zu betreiben.

> **Hinweis:** Eine Benutzerverwaltung bzw. ein Login ist derzeit nicht vorgesehen und wird erst in einer späteren Phase ergänzt.

Neue Board- oder Druckerdefinitionen werden aktuell über Pull Requests im GitHub-Repository gepflegt. Sobald eine Authentifizierung verfügbar ist, sollen Anwender fehlende Hardware direkt in der Weboberfläche ergänzen können. Die Landingpage (`/`) verlinkt bereits auf den Board-Designer sowie einen interaktiven Printer-Designer. Beide erzeugen angereicherte JSON-Dokumente, die über neue REST-Endpunkte dauerhaft gespeichert werden können.

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

## Designer & Definition Registry

- **Landingpage (`/`)** – bündelt Einstiegspunkte in Board- und Drucker-Designer und erklärt den geplanten Konfigurations-Generator.
- **Board-Designer (`/board-designer`)** – erlaubt das Annotieren von Pins, Steckern und Signalen auf hochgeladenen Bildern.
- **Printer-Designer (`/printer-designer`)** – erlaubt Bild-Uploads, markiert Extruder, Schalter, Sensoren, Lüfter oder Stepper mit Rechtecken, Kreisen und Maßpfeilen und erfasst Rotationsdistanzen für Antriebe.
- **Persistente Registry** – neue Tabellen `board_definition_documents` und `printer_definition_documents` speichern Designer-Ergebnisse inklusive Metadaten und Vorschaubild-Links.
- **REST-API** – über `/api/definitions/boards` und `/api/definitions/printers` lassen sich Definitionen anlegen, abrufen und aktualisieren.

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
| GET     | `/api/dashboard/overview` | Verdichteter Status-Snapshot inkl. Verlaufspunkten |
| GET     | `/api/dashboard/temperatures` | Statistiken pro Temperaturkanal (min/avg/max, aktueller Wert) |
| GET     | `/api/dashboard/jobs` | Zusammenfassung der zuletzt beobachteten Druckaufträge |
| POST    | `/api/board-assets/` | Lädt Board-Grafiken samt Metadaten hoch (Upload-Token erforderlich) |
| PATCH   | `/api/board-assets/{id}` | Aktualisiert Metadaten eines Assets (Upload-Token erforderlich) |
| GET     | `/api/board-assets/` | Listet Assets (standardmäßig nur freigegebene) |
| GET     | `/api/board-assets/moderation/pending` | Liefert Moderations-Warteschlange (Moderator-Token erforderlich) |
| PATCH   | `/api/board-assets/{id}/moderation` | Trifft Moderationsentscheidung (Moderator-Token erforderlich) |
| GET     | `/api/definitions/boards` | Listet gespeicherte Board-Definitionen inkl. Metadaten |
| POST    | `/api/definitions/boards` | Persistiert eine neue Board-Definition (JSON aus dem Designer) |
| PUT     | `/api/definitions/boards/{slug}` | Aktualisiert Namen, Beschreibung oder Daten einer Board-Definition |
| GET     | `/api/definitions/printers` | Listet gespeicherte Drucker-Definitionen |
| POST    | `/api/definitions/printers` | Legt eine neue Drucker-Definition an |
| PUT     | `/api/definitions/printers/{slug}` | Aktualisiert eine vorhandene Drucker-Definition |
| GET     | `/api/boards/definitions` | Listet alle gültigen Board-Definitionen inkl. Metadaten |
| POST    | `/api/boards/definitions/validate` | Führt eine vollständige Schema-Validierung aller Definitionen aus |
| GET     | `/api/boards/versions` | Aggregiert verfügbare Revisionen pro Board-Identifier |
| GET     | `/api/boards/schema` | Liefert Schema-Version und Speicherort der erwarteten Definition |

Zusätzliche Zustände (`pending`, `rejected`) können ausschließlich mit gültigem Upload- oder Moderator-Token abgefragt werden.

### Board-Asset-Upload & Moderation

Uploads und Moderationsentscheidungen werden über zwei API-Tokens abgesichert:

- `BOARD_ASSET_UPLOAD_TOKEN`: berechtigt zum Hochladen neuer Assets sowie zum Bearbeiten von Metadaten.
- `BOARD_ASSET_MODERATION_TOKEN`: erlaubt das Einsehen der Moderationswarteschlange und das Freigeben/Ablehnen von Assets.

Für die Ablage stehen zwei Storage-Backends zur Verfügung:

| Backend | Erforderliche Variablen | Beschreibung |
| ------- | ---------------------- | ------------ |
| `local` (Standard) | `BOARD_ASSET_LOCAL_PATH` (Pfad, Standard `./var/board-assets`), optional `BOARD_ASSET_LOCAL_PUBLIC_URL` | Speichert Dateien im lokalen Dateisystem. Eine Public-URL erzeugt Downloadlinks. |
| `s3` | `BOARD_ASSET_S3_BUCKET`, optional `BOARD_ASSET_S3_REGION`, `BOARD_ASSET_S3_PUBLIC_URL`, `BOARD_ASSET_S3_ENDPOINT` | Lädt Assets in ein S3-kompatibles Object-Storage. |

Beispielupload via `curl` (lokales Backend):

```bash
export BOARD_ASSET_UPLOAD_TOKEN="mein-upload-token"

curl -X POST \
  -H "X-Board-Assets-Key: ${BOARD_ASSET_UPLOAD_TOKEN}" \
  -F "file=@/pfad/zur/grafik.svg" \
  -F "title=Voron Stealthburner" \
  http://localhost:8000/api/board-assets/
```

Die öffentliche `GET /api/board-assets/`-Route liefert ausschließlich genehmigte, als `public` markierte Assets. Mit Upload- oder Moderator-Token lassen sich zusätzliche Moderationszustände über den Parameter `status_filter` einsehen.

### Dashboard-Metriken aus der Historie

Die neuen Dashboard-Endpunkte greifen auf die persistente Historie zu und liefern
kompakte JSON-Strukturen für Frontend-Widgets. Damit lassen sich Diagramme oder
KPI-Kacheln ohne zusätzliche Transformationen aufbauen.

**`GET /api/dashboard/overview`**

Optionale Query-Parameter:

- `progress_points` (Standard `20`, min. `1`, max. `200`): Anzahl Verlaufspunkte für den
  Fortschritts-Chart.

Beispielantwort:

```json
{
  "updated_at": "2024-04-15T12:35:00+00:00",
  "state": "printing",
  "message": "Druck läuft stabil",
  "uptime_seconds": 16320,
  "active_job": {
    "job_identifier": "job-20240415-01",
    "name": "Voron_Mount_v6.gcode",
    "progress": 0.42,
    "status": "running",
    "started_at": "2024-04-15T12:17:00+00:00",
    "estimated_completion": "2024-04-15T13:00:00+00:00",
    "is_active": true,
    "last_seen_at": "2024-04-15T12:35:00+00:00"
  },
  "queued_jobs": {
    "count": 2,
    "entries": [
      {
        "job_identifier": "job-20240415-02",
        "name": "Calibration_Cube_20mm.gcode",
        "progress": 0.0,
        "status": "queued",
        "started_at": null,
        "estimated_completion": null,
        "is_active": false,
        "last_seen_at": "2024-04-15T12:35:00+00:00"
      }
    ]
  },
  "history": {
    "progress": [
      {"recorded_at": "2024-04-15T12:30:00+00:00", "progress": 0.38},
      {"recorded_at": "2024-04-15T12:35:00+00:00", "progress": 0.42}
    ]
  }
}
```

**`GET /api/dashboard/temperatures`**

Liefert die jeweils neuesten Messwerte sowie min/avg/max je Komponente.

```json
{
  "updated_at": "2024-04-15T12:35:00+00:00",
  "components": [
    {
      "component": "hotend",
      "latest": {
        "actual": 205.3,
        "target": 210.0,
        "timestamp": "2024-04-15T12:35:00+00:00"
      },
      "statistics": {
        "samples": 24,
        "min_actual": 198.6,
        "max_actual": 207.4,
        "avg_actual": 203.8
      }
    }
  ]
}
```

**`GET /api/dashboard/jobs`**

Optionale Query-Parameter:

- `limit` (Standard `5`, min. `1`, max. `50`): Anzahl der zurückgelieferten Jobs.

Die Antwort beinhaltet für jeden Job den zuletzt beobachteten Zustand sowie eine
Statusverteilung für schnelle KPIs.

```json
{
  "updated_at": "2024-04-15T12:35:00+00:00",
  "recent": [
    {
      "job_identifier": "job-20240415-01",
      "name": "Voron_Mount_v6.gcode",
      "progress": 0.42,
      "status": "running",
      "started_at": "2024-04-15T12:17:00+00:00",
      "estimated_completion": "2024-04-15T13:00:00+00:00",
      "is_active": true,
      "last_seen_at": "2024-04-15T12:35:00+00:00"
    }
  ],
  "status_totals": {
    "running": 1,
    "queued": 2,
    "completed": 0
  }
}
```

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

## Board-Definitionen versionieren & prüfen

Hardware-Definitionen werden als JSON-Dateien im Verzeichnis `board-definitions/`
versioniert. Das Schema `schemas/board-definition.schema.json` dokumentiert Pflichtfelder
für Metadaten (`identifier`, `name`, `manufacturer`, `revision`), Steckverbinder (`id`,
`name`, `type`, `pins`) sowie Pins (`number`, `signal`). Über den Schlüssel
`x-klipperiwc-version` ist ersichtlich, welche `schema_version` gültige Definitionen
verwenden müssen. Die Pfade können über die Umgebungsvariablen
`BOARD_DEFINITION_ROOT` (Standard: `./board-definitions`) und
`BOARD_DEFINITION_SCHEMA` (Standard: `./schemas/board-definition.schema.json`) angepasst
werden.

**Empfohlener Workflow:**

1. Unter `http://localhost:8000/board-designer` Steckverbinder markieren und Pins
   benennen. Die Markierungen dienen als Vorlage für die JSON-Definition.
2. Eine Datei `<identifier>/<revision>.json` im Registry-Ordner anlegen und anhand des
   Schemas ausfüllen.
3. Über `GET /api/boards/schema` prüfen, welche Schema-Version aktuell erwartet wird.
4. Mit `POST /api/boards/definitions/validate` sämtliche Definitionen validieren. Die
   Antwort enthält pro Datei Validierungsfehler und bei Erfolg eine komprimierte
   Zusammenfassung.
5. Mit `GET /api/boards/definitions` bzw. `GET /api/boards/versions` lassen sich
   resultierende Metadaten und verfügbare Revisionen automatisiert konsumieren.

Beispielaufruf für die Validierung:

```bash
curl -X POST "http://localhost:8000/api/boards/definitions/validate" | jq
```

Die Pydantic-Modelle unter `klipperiwc/models/boards.py` erlauben es, Definitionen in
Python-Diensten weiterzuverwenden. Die API reagiert automatisch auf neue Dateien,
solange sie im konfigurierten Registry-Verzeichnis abgelegt werden.

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
