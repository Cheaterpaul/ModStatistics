import os
import datetime
import mariadb
import sys
import os

import requests

modrinth_url = "https://api.modrinth.com/v2"
curseforge_url = "https://api.curseforge.com"

dbname = database = os.environ["DB_DATABASE"]




def get_db():
    try:
        port = int(os.environ["DB_PORT"])
        if port is None:
            port = 3306
        return mariadb.connect(
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=port,
            database=dbname
        )
    except mariadb.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def get_modrinth_mod(mod_id):
    return requests.get(f"{modrinth_url}/project/{mod_id}", headers={
        'User-Agent': 'Cheaterpaul/ModStatistics'
    })


def get_modrinth_files(project):
    return requests.get(f"{modrinth_url}/project/{project}/version", headers={
        'User-Agent': 'Cheaterpaul/ModStatistics'
    })

def get_curseforge_mod(mod_id):
    return requests.get(f"{curseforge_url}/v1/mods/{mod_id}", headers={
        'Accept': 'application/json',
        'x-api-key': os.environ['CURSEFORGE_API_KEY']
    })


def get_curseforge_files(mod_id):
    return requests.get(f"{curseforge_url}/v1/mods/{mod_id}/files", headers={
        'Accept': 'application/json',
        'x-api-key': os.environ['CURSEFORGE_API_KEY']
    })


conn = get_db()
db = conn.cursor()


def create_table(name: str):
    db.execute(f'''CREATE TABLE IF NOT EXISTS {dbname}.{name} (
                                        downloads int(32) NOT NULL,
                                        provider varchar(45) NOT NULL,
                                        time datetime NOT NULL,
                                        PRIMARY KEY (provider, time)
                               )''')


def create_version_table(name: str):
    db.execute(f'''CREATE TABLE IF NOT EXISTS {dbname}.{name}_files (
                                            name varchar(60) NOT NULL,
                                            version varchar(60) NOT NULL,
                                            downloads int(32) NOT NULL,
                                            provider varchar(45) NOT NULL,
                                            time datetime NOT NULL,
                                            PRIMARY KEY (version, provider, time)
                                   )''')


time = datetime.datetime.now()


def save_curseforge_mod(name: str, data: dict):
    create_table(name)
    command = f'''INSERT INTO {dbname}.{name} (downloads, provider, time) VALUES (?, ?, ?)'''
    db.execute(command, (data["downloadCount"], "curseforge", time))


def save_modrinth_mod(name: str, data: dict):
    create_table(name)
    db.execute(f'''INSERT INTO {dbname}.{name} (downloads, provider, time) VALUES (?, ?, ?)''',
               (data["downloads"], "modrinth", time))


def save_curseforge_files(name: str, data: dict):
    create_version_table(name)
    db.execute(
        f'INSERT INTO {dbname}.{name}_files (name, version, downloads, provider, time) VALUES {",".join([str((x["displayName"], x["fileName"].split("-", 1)[1][0:-4], x["downloadCount"], "curseforge", str(time))) for x in data])}')


def save_modrinth_files(name: str, data: dict):
    create_version_table(name)
    db.execute(
        f"""INSERT INTO {dbname}.{name}_files (name, version, downloads, provider, time) VALUES {",".join([str((x["name"], x["version_number"], x["downloads"], "modrinth", str(time))) for x in data])}""")


if 'CURSEFORGE_PROJECTS' in os.environ:
    for entry in os.environ['CURSEFORGE_PROJECTS'].split(';'):
        project = entry.split(',')
        save_curseforge_mod(project[0], get_curseforge_mod(project[1]).json()["data"])
        save_curseforge_files(project[0], get_curseforge_files(project[1]).json()["data"])

if 'MODRINTH_PROJECTS' in os.environ:
    for entry in os.environ['MODRINTH_PROJECTS'].split(';'):
        project = entry.split(',')
        save_modrinth_mod(project[0], get_modrinth_mod(project[1]).json())
        save_modrinth_files(project[0], get_modrinth_files(project[1]).json())

conn.commit()
conn.close()
