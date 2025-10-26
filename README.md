# HSG-MCS: Advanced Databases Courses: **FlavorNet**
## A multi-database recommendation system
For **FlavorNet**, our smart recipe finder, this is a small backend that spins up PostgreSQL, MongoDB and Neo4j as docker containers.

## Prerequisites

- Docker and Docker Compose installed

## Quick start
[AdvDB-FlavorNet](https://github.com/LorenaRaichle/AdvDB-FlavorNet)
```bash
# 1. Clone or download the project from Github https://github.com/LorenaRaichle/AdvDB-FlavorNet --> Unzip the project if need
# 2. In the project directory:
docker compose build
docker compose up -d
```

To stop and remove containers:
```bash
docker compose down
```

## Services

- PostgreSQL - localhost:55432 - db: `socialdb`, user: `app`, password: `app_pw1234`
- MongoDB - localhost:27017 - root user: `app`, password: `app_pw1234`
- Neo4j - Browser http UI at http://localhost:7474 - Bolt at bolt://localhost:7687 - user: `neo4j`, password: `app_pw1234`



-  bash mongoDB/scripts/rebuild_mongo.sh
