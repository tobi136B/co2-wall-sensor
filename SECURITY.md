# Security policy

**English** | [Deutsch](#deutsch)

## Supported versions

Only the latest release receives fixes. Devices flashed with the browser installer get them as a firmware update in Home Assistant.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use GitHub's private reporting instead:
[Report a vulnerability](https://github.com/tobi136B/co2-wall-sensor/security/advisories/new).

You will get an answer within a week. Please include the firmware version, how the device was flashed (browser installer or own build) and the steps to reproduce.

## Good to know

* The browser installer firmware contains **no credentials**. WiFi is set up by you after flashing, the API is unencrypted until you adopt the device in the ESPHome dashboard. Adopt it if your network is not trusted.
* Never commit `esphome/secrets.yaml`. The repository ignores it, and GitHub push protection blocks known secret formats.

---

## Deutsch

Sicherheitsprobleme bitte **nicht als öffentliches Issue** melden, sondern privat über [Sicherheitslücke melden](https://github.com/tobi136B/co2-wall-sensor/security/advisories/new). Eine Antwort kommt innerhalb einer Woche. Bitte Firmware-Version, Art der Installation (Browser-Installer oder eigener Build) und die Schritte zum Nachstellen angeben.

Die Firmware des Browser-Installers enthält **keine Zugangsdaten**. Die API ist unverschlüsselt, bis das Gerät im ESPHome Dashboard übernommen wird. In nicht vertrauenswürdigen Netzen bitte übernehmen.
