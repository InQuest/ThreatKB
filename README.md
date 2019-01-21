
<p align="center">
    <img src="wiki/res/inquest_logo.svg"></img>
</p>


### NOTE: THIS REPO IS IN AN ALPHA STATE

ThreatKB is a knowledge base workflow management dashboard for Yara rules and C2 artifacts. Rules are categorized and used to denote intent, severity, and confidence on accumulated artifacts.

To start using ThreatKB, follow our [guide](wiki/setup.md).

  ---  

Installing by Docker is the currently recommended way of setting up ThreatKB, directions are included as the first link in the wiki. Installation by source is included in the wiki as well.


## Table of Contents

* [Docker Installation](wiki/docker.md)
* [Setup ThreatKB](wiki/setup.md)
  + [Pre-requisites](wiki/setup.md#pre-requisites)
  + [System Prep](wiki/setup.md#system-prep)
* [Getting Started](wiki/getting-started.md)
  + [Application Install](wiki/getting-started.md#application-install)
  + [Running ThreatKB](wiki/getting-started.md#running-threatkb)
  + [Admin User Creation](wiki/getting-started.md#admin-user-creation)
* [Databases](wiki/db-struct.md)
* [Documentation](wiki/documentation.md)
* [FAQ](wiki/faq.md)



## Thank You
ThreatKB utilizes Plyara to parse yara rules into python dictionaries. A huge thank you to the Plyara team! Links to the project are below:

https://github.com/8u1a/plyara
https://github.com/8u1a/plyara/blob/master/LICENSE

When a release is created, the system first pulls all signatures that are in the release state. Then, it gathers all signatures that are in the staging state and checks their revision history for the most recently released revision that is in the release state. If it finds it, it will include it in the release. If it does not find any previously released revisions, it will skip the signature.

