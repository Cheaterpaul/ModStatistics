
# Mod Statistics

This docker image loads mod statistics from modrinth and curseforge and saves them in a mariadb database for further processing

## What does it do?

Docker image will run the python script daily at 12 AM.

**Error handling is not present** 

### Table Reference

The tables split the data in modrinth and curseforge as the provided data is to different

The script will create and fill the following tables in the database:

#### mods

| Columns | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `id` | `int(32)` | Internal id |
| `name` | `varchar(45)` | Mod name |
| `provider` | `varchar(32)` | Mod data source (modrinth/curseforge) |

#### total_downloads

| Columns | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `id` | `int` | Mod provider id -> mods.id |
| `time` | `datetime` | Timestamp of the data |
| `downloads` | `int` | Total downloads |

#### files

| Columns | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `id` | `int` | Mod provider id -> mods.id |
| `version` | `varchar(60)` | File version|
| `name` | `varchar(60)` | Version name |

#### file_downloads

| Columns | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `id` | `int` | Mod provider id -> mods.id |
| `version` | `varchar(60)` | Mod version -> files.version |
| `time` | `datetime` | Timestamp of the data |
| `downloads` | `int` | File downloads |

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DB_HOST` _required_

`DB_PASSWORD` _required_

`DB_PORT` _optional_ defaults to `3306`

`DB_DATABASE` _optional_ defaults to `modstats`

`DB_USER` _optional_ defaults to `modstats`

`CURSEFORGE_API_KEY` _optional_ but required for curseforge projects

`CURSEFORGE_PROJECTS` _optional_ specify curseforge projects. Format: `<projectname1>-<projectid1>,<projectname2>-<projectid2>,<projectname3>-<projectid3>`

`MODRINTH_PROJECTS` _optional_ specify modrinth projects. Format: `<projectname1>-<projectid1>,<projectname2>-<projectid2>,<projectname3>-<projectid3>`
## Usage/Examples
keep in mind there is no dockerimage available for Dockerfile. **You need to build it yourself**.
```docker-compose
version: '3.3'

services:
  modstats-db:
    image: mariadb
    restart: unless-stopped
    environment:
      - MYSQL_RANDOM_ROOT_PASSWORD=true
      - MYSQL_USER=modstats
      - MYSQL_PASSWORD=
      - MYSQL_DATABASE=modstats
    volumes:
      -/db:/var/lib/mysql
    networks:
      - default
  modstats-app:
    image: modstats
    restart: unless-stopped
    networks:
      - default
    environment:
      - DB_PASSWORD=
      - DB_HOST=modstats-db
      - CURSEFORGE_PROJECTS=fallingleaves-463155,vampirism-233029
      - MODRINTH_PROJECTS=fallingleaves-2JAUNCL4,vampirism-jVZ0F1wn
      - CURSEFORGE_API_KEY=
    depends_on:
      - modstats-db

networks:
  default:
    driver: bridge

```

## License

Do what every you want
[MIT](https://choosealicense.com/licenses/mit/)