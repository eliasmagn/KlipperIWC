# Aufgabenliste

## Erledigt

- [x] Basis-FastAPI-Anwendung initialisieren
- [x] Deploy-Skripte für Produktion und Entwicklung bereitstellen
- [x] Docker-Image für containerisierte Ausführung definieren
- [x] SQLAlchemy-Grundkonfiguration mit erster Alembic-Migration einrichten
- [x] API-Spezifikation und Pydantic-Modelle für Druckerstatus, Temperaturen und aktive Jobs erstellen
- [x] Persistente Statushistorie in SQLite mit Service-Layer und automatischem Bereinigungstask aufbauen (Retention via `STATUS_HISTORY_RETENTION_DAYS` konfigurierbar)
- [x] Dashboard-API für aggregierte Kennzahlen (Temperaturen, Jobs, Fortschritt) bereitstellen
- [x] JSON-Schema für Board-Definitionen samt Validierungs-Workflow und API-Endpunkten dokumentieren

## Offene Schritte Richtung Produktivbetrieb

- [ ] Klipper-Polling-Client bzw. Event-Receiver implementieren und als Service-Layer kapseln
- [x] Websocket-Gateway zur Verteilung der Status-Updates an UI-Clients entwickeln
- [ ] Dashboard-Layout im Webfrontend mit Navigation und Grundseiten strukturieren
- [ ] Live-Widgets für Temperaturkurven und Jobfortschritt mit Dashboard-/Websocket-Daten verknüpfen
- [x] Upload-Workflow für Board-Grafiken samt S3-/Dateisystem-Storage und Moderationsschritt implementieren
- [ ] Automatisierte Moderations-Benachrichtigungen (E-Mail/Webhook) integrieren
- [ ] Validierungslogik für Pin-Namen gegen MCU-Datenbank ergänzen und mit Unit-Tests absichern
- [ ] CI/CD-Pipeline mit Linting, Tests und automatischem Container-Build & Tagging aufsetzen
