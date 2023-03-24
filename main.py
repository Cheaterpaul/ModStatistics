import os
import datetime
import sys
import os
import pymysql.cursors

import requests

print("[ModStats] Start")

modrinth_url = "https://api.modrinth.com/v2"
curseforge_url = "https://api.curseforge.com"

dbname = os.environ["DB_DATABASE"]


def get_db():
    port = int(os.environ["DB_PORT"])
    return pymysql.connect(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=port,
        database=dbname
    )


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
    list = []
    all = 1
    index = 0

    while index < all:
        result = requests.get(f"{curseforge_url}/v1/mods/{mod_id}/files", headers={
            'Accept': 'application/json',
            'x-api-key': os.environ['CURSEFORGE_API_KEY']
        }, params={
            'index': index
        }).json()
        list += result["data"]
        all = result["pagination"]["totalCount"]
        index = result["pagination"]["index"] + result["pagination"]["resultCount"]
        pass


    return list


print("[DB] Connect to database")
conn = get_db()
db = conn.cursor()
print("[DB] Connection established")


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
print(f"[DateTime] Current time is {str(time)}")


def save_curseforge_mod(name: str, data: dict):
    create_table(name)
    command = f'''INSERT INTO {dbname}.{name} (downloads, provider, time) VALUES ({data["downloadCount"]}, \'curseforge\', \'{str(time)}\')'''
    db.execute(command)


def save_modrinth_mod(name: str, data: dict):
    create_table(name)
    db.execute(f'''INSERT INTO {dbname}.{name} (downloads, provider, time) VALUES ({data["downloads"]}, \'modrinth\', \'{str(time)}\')''')


def save_curseforge_files(name: str, data: dict):
    create_version_table(name)
    db.execute(
        f'INSERT INTO {dbname}.{name}_files (name, version, downloads, provider, time) VALUES {",".join([str((x["displayName"], x["fileName"].split("-", 1)[1][0:-4], x["downloadCount"], "curseforge", str(time))) for x in data])}')


def save_modrinth_files(name: str, data: dict):
    create_version_table(name)
    db.execute(
        f"""INSERT INTO {dbname}.{name}_files (name, version, downloads, provider, time) VALUES {",".join([str((x["name"], x["version_number"], x["downloads"], "modrinth", str(time))) for x in data])}""")


print("[Download] Start data provider")
print("[Download] Start curseforge")
if 'CURSEFORGE_PROJECTS' in os.environ:
    for entry in os.environ['CURSEFORGE_PROJECTS'].split(';'):
        project = entry.split(',')
        print(f"[Download]   - downloading {project[0]}")
        # save_curseforge_mod(project[0], get_curseforge_mod(project[1]).json()["data"])
        save_curseforge_files(project[0], get_curseforge_files(project[1]))
else:
    print("[Download] Skipping curseforge")
print("[Download] End curseforge")

print("[Download] Start modrinth")
if 'MODRINTH_PROJECTS' in os.environ:
    for entry in os.environ['MODRINTH_PROJECTS'].split(';'):
        project = entry.split(',')
        print(f"[Download]   - downloading {project[0]}")
        # save_modrinth_mod(project[0], get_modrinth_mod(project[1]).json())
        # save_modrinth_files(project[0], get_modrinth_files(project[1]).json())
else:
    print("[Download] Skipping modrinth")
print("[Download] End modrinth")
print("[Download] End data provider")

print("[DB] Commit changes")

conn.commit()
conn.close()

print("[ModStats] Finished")
