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


## Commands to run the whole system

```bash
docker pull lorena107/recipes-db:latest
docker compose pull mongo

docker compose up -d mongo
docker exec -it mongo mongosh --quiet --eval 'db.getSiblingDB("appdb").getCollectionNames()'
docker compose up -d
```

## mongo: to do Lorena
- recipes stored in data/recipe_nlg as csv, notebook "recipe_preprocessing" does loading, preprocessing and adding of new tags etc
- final jsonl file in mongo schema is created: init / 03..jsonl, place processed data jsonl file name in "rebuild_mongo.sh" and run...
- bash mongoDB/scripts/rebuild_mongo.sh

## 1. mongo queries: local client -> docker (hosted files) (for quick local dev)
- mongosh runs on host machine
```bash
docker exec -it mongo mongosh -u app -p app_pw1234 --authenticationDatabase admin \
  --eval 'db.getSiblingDB("appdb").createUser({user:"appuser",pwd:"apppass",roles:[{role:"readWrite",db:"appdb"}]})'

```

```bash
docker exec -it mongo mongosh \
  "mongodb://appuser:apppass@localhost:27017/appdb?authSource=appdb" \
  --eval 'db.stats().db'

```


```bash
 mongosh "mongodb://appuser:apppass@localhost:27017/appdb?authSource=appdb" \
  --file mongoDB/queries/find_recipes_by_ingredient.js \
  --eval 'DB_NAME="appdb";ING="garlic"'

```


## 2. Container (containerized files) (for reproducible runs)
- mongosh runs inside mongo container 
- Run mongosh inside the mongo container via docker compose exec
- The query file must exist in the container -> need to copy script into container

```bash
 docker cp mongoDB/queries/find_recipes_by_ingredient.js mongo:/tmp/find_recipes_by_ingredient.js
```

```bash
docker compose exec mongo mongosh \
  "mongodb://appuser:apppass@localhost:27017/appdb?authSource=appdb" \
  --file /tmp/find_recipes_by_ingredient.js \
  --eval 'DB_NAME="appdb";ING="garlic"'

```
