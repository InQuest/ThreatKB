<p align="center">
  <img src="https://raw.githubusercontent.com/InQuest/ThreatKB/wiki-cleanup/.github/wiki/inquest_logo.svg" />
</p>

### NOTE: THIS REPO IS IN AN ALPHA STATE

ThreatKB is a knowledge base workflow management dashboard for YARA rules and C2 artifacts. Rules are categorized and used to denote intent, severity, and confidence in accumulated artifacts.

To start using ThreatKB, check out our [wiki](https://github.com/InQuest/ThreatKB/wiki).

---

Installing by Docker is the currently recommended way of setting up ThreatKB, directions are included as the first link in the wiki. Installation by source is included in the wiki as well.

## Table of Contents

* [Home](https://github.com/InQuest/ThreatKB/wiki)
* [Setup ThreatKB](https://github.com/InQuest/ThreatKB/wiki/Setup#pre-requisites)
  + [Pre-requisites](https://github.com/InQuest/ThreatKB/wiki/Setup#pre-requisites)
  + [System Prep](https://github.com/InQuest/ThreatKB/wiki/Setup#system-prep)
  + [Application Install](https://github.com/InQuest/ThreatKB/wiki/Setup#application-install)
* [Getting Started](https://github.com/InQuest/ThreatKB/wiki/Getting-Started)
  + [Running ThreatKB](https://github.com/InQuest/ThreatKB/wiki/Getting-Started#running-threatkb)
  + [Admin User Creation](https://github.com/InQuest/ThreatKB/wiki/Getting-Started#running-threatkb)
* [Docker Installation](https://github.com/InQuest/ThreatKB/wiki/Docker)
* [Database Structure](https://github.com/InQuest/ThreatKB/wiki/Database-Structure)
* [Documentation](https://github.com/InQuest/ThreatKB/wiki/Documentation)
* [FAQ](https://github.com/InQuest/ThreatKB/wiki/Frequently-Asked-Questions)

## Thank You
ThreatKB utilizes Plyara to parse YARA rules into Python dictionaries. A huge thank you to the Plyara team! Links to the project are below:

- [Plyara](https://github.com/plyara/plyara) ([LICENSE](https://github.com/plyara/plyara/blob/master/LICENSE))

When a release is created, the system first pulls all signatures that are in the release state. Then, it gathers all signatures that are in the staging state and checks their revision history for the most recently released revision that is in the release state. If it finds it, it will include it in the release. If it does not find any previously released revisions, it will skip the signature.
