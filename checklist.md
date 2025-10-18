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
- [x] Zugriffskontrolle für Board-Asset-Uploads, -Listen und Moderationswarteschlange über API-Tokens absichern
- [x] Landingpage mit Verlinkung auf Board- und Drucker-Designer erstellen
- [x] Persistente Tabellen sowie API-Endpunkte für Board- und Druckerdefinitionen anlegen
- [x] Drucker-Designer mit Bild-Upload, Annotationen und Maßpfeilen implementieren
- [x] Cursor-Koordinaten im Board- und Drucker-Designer an die ViewBox-Skalierung anpassen
- [x] 3D-CAD-Viewer mit STEP-Import und Marker-Workflow für Board- und Drucker-Designer integrieren
- [x] Drucker-Designer um Profil-Assistent (Konstanten, Dokumentations-Tooltips) und Klipper-Konfigurationskatalog erweitern
- [x] Landingpage um geführten Ablauf mit Schritt-für-Schritt-Karten erweitern
- [x] Drucker-Designer: 2D-Layout und 3D-CAD-Ansicht in einem Workspace mit Umschalter zusammenführen
- [x] Board-Designer: 2D-Layout und 3D-CAD-Ansicht in einem gemeinsamen Workspace mit Umschalter kombinieren
- [x] STEP-Parser über ein zuverlässiges CDN laden und Verfügbarkeit der 3D-Vorschau verbessern
- [x] Dokumentation zum extern verwalteten Registry-Verzeichnis für Board-Definitionen ergänzen
- [x] 3D-CAD-Viewer mit konfigurierbarem Pixelratio-Limit ausstatten und Resize-Handling für DPI-Wechsel aktualisieren

## Offene Schritte Richtung Produktivbetrieb

- [ ] Klipper-Polling-Client bzw. Event-Receiver implementieren und als Service-Layer kapseln
- [x] Websocket-Gateway zur Verteilung der Status-Updates an UI-Clients entwickeln
- [ ] Authentifizierungsmechanismus für das Websocket-Gateway umsetzen (z. B. Token oder Session)
- [ ] Rate-Limiting und Verbindungsgrenzen für das Websocket-Gateway hinzufügen
- [ ] Dashboard-Layout im Webfrontend mit Navigation und Grundseiten strukturieren
- [ ] Interaktive Nachbearbeitung (Bewegen/Löschen) für Board- und Drucker-Markierungen ergänzen
- [ ] Live-Widgets für Temperaturkurven und Jobfortschritt mit Dashboard-/Websocket-Daten verknüpfen
- [x] Upload-Workflow für Board-Grafiken samt S3-/Dateisystem-Storage und Moderationsschritt implementieren
- [ ] Automatisierte Moderations-Benachrichtigungen (E-Mail/Webhook) integrieren
- [ ] Validierungslogik für Pin-Namen gegen MCU-Datenbank ergänzen und mit Unit-Tests absichern
- [ ] CI/CD-Pipeline mit Linting, Tests und automatischem Container-Build & Tagging aufsetzen
- [ ] Benutzerkonten mit Freigabemodellen für Definitionen implementieren
- [ ] Konfigurations-Generator für kombinierte Board-/Druckerprofile entwickeln
