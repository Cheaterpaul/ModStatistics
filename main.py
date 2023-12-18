import os
import datetime
import sys
import os
import pymysql.cursors

import requests

time = datetime.datetime.now()


def log(marker: str, message: str):
    print(f'[{str(datetime.datetime.now())}] {marker} - {message}')


sep = ",\n"


class Database:
    mods_table = "mods"
    total_downloads_table = "total_downloads"
    files_table = "files"
    file_download_table = "file_downloads"
    versions_table = "versions"

    def __init__(self, host: str, port: int, p_database: str, user: str, password: str):
        log("Database", "start connecting")
        self.db = pymysql.connect(user=user, password=password, host=host, port=port, database=p_database)
        self.cursor = self.db.cursor()
        self.dbname = p_database
        log("Database", "finished connecting")

    def create_tables(self):
        log("Database", "start creating tables")
        self._create_mods_table_()
        self._create_total_downloads_table_()
        self._create_files_table_()
        self._create_file_downloads_table_()
        self._create_versions_table()
        log("Database", "finished creating tables")

    def close(self):
        self.db.commit()
        self.db.close()

    def _create_versions_table(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.dbname}.{self.versions_table} (
                                                version varchar(60) NOT NULL, 
                                                mcversion varchar(10),
                                                majormcversion varchar(10),
                                                modversion varchar(10),
                                                majormodversion varchar(10),
                                                PRIMARY KEY (version)
                                        )''')

    def _create_mods_table_(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.dbname}.{self.mods_table} (
                                                id int(32) AUTO_INCREMENT ,
                                                name varchar(45) NOT NULL,
                                                provider varchar(32) NOT NULL,
                                                PRIMARY KEY (id)
                                       ) auto_increment = 0''')

    def _create_total_downloads_table_(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.dbname}.{self.total_downloads_table} (
                                                        id int NOT NULL,
                                                        time datetime NOT NULL,
                                                        downloads int NOT NULL,
                                                        PRIMARY KEY (id, time)
                                               )''')

    def _create_files_table_(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.dbname}.{self.files_table} (
                                                        id int NOT NULL,
                                                        name varchar(60) NOT NULL,
                                                        version varchar(60) NOT NULL,
                                                        PRIMARY KEY (id, version)
                                               )''')

    def _create_file_downloads_table_(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.dbname}.{self.file_download_table} (
                                                                id int NOT NULL,
                                                                version varchar(60) NOT NULL,
                                                                time datetime NOT NULL,
                                                                downloads int NOT NULL,
                                                                PRIMARY KEY (id, version, time)
                                                       )''')

    def create_provider(self, mod: str, name: str) -> int:
        self.cursor.execute(
            f'''IF NOT EXISTS (SELECT mods.id FROM {self.dbname}.{self.mods_table} as mods WHERE mods.name = '{mod}' AND mods.provider = '{name}') THEN
                                    INSERT INTO {self.dbname}.{self.mods_table}(name, provider)
                                    VALUES('{mod}', '{name}');
                                    SELECT mods.id FROM {self.dbname}.{self.mods_table} as mods WHERE name = '{mod}' AND mods.provider = '{name}' LIMIT 1;
                                ELSE
                                    SELECT mods.id FROM {self.dbname}.{self.mods_table} as mods WHERE name = '{mod}' AND mods.provider = '{name}' LIMIT 1;
                                END IF''')
        result = self.cursor.fetchone()
        return result[0]

    def save_total_downloads(self, id: int, time: datetime, downloads: int):
        self.cursor.execute(
            f'''INSERT INTO {self.dbname}.{self.total_downloads_table} (id, time, downloads) VALUE ({id}, '{str(time)}', {downloads})''')

    def create_file(self, id: int, version: str, name: str):
        self.cursor.execute(
            f'''IF NOT EXISTS (SELECT files.version FROM {self.dbname}.{self.files_table} as files WHERE files.id = '{id}' AND files.version = '{version}') THEN
                                            INSERT INTO {self.dbname}.{self.files_table}(id, version, name)
                                            VALUES({id}, '{version}', '{name}');
                                        END IF''')

    def create_files(self, id: int, item: (str, str)):
        self.cursor.execute(f'''INSERT IGNORE INTO {self.dbname}.{self.files_table}(id, version, name)
                                       VALUES {sep.join([f"({id},'{x[0]}','{x[1]}')" for x in item])}''')

    def save_file_download(self, id: int, version: str, time: datetime, downloads: int):
        self.cursor.execute(f'''INSERT INTO {self.dbname}.{self.file_download_table} (id, version, time, downloads)
                                VALUES('{id}', '{version}', '{str(time)}', {downloads})
                                ON DUPLICATE KEY UPDATE
                                  id = VALUES(id),
                                  version = VALUES(version),
                                  time = VALUES(time),
                                  downloads = VALUES(downloads)''')

    def save_file_downloads(self, id: int, time: datetime, item: (str, int)):
        self.cursor.execute(f'''INSERT INTO {self.dbname}.{self.file_download_table} (id, version, time, downloads)
                                VALUES {sep.join([f"({id},'{x[0]}','{str(time)}','{x[1]}')" for x in item])}
                                ON DUPLICATE KEY UPDATE
                                  id = VALUES(id),
                                  version = VALUES(version),
                                  time = VALUES(time),
                                  downloads = VALUES(downloads)''')

    def create_versions(self, versions: [str]):
        list = []
        for x in versions:
            try:
                split = x.split('-')
                if len(split) > 1:
                    mc = split[0]
                    mcmajor = mc
                    mod = split[1]
                    modmajor = mod
                    split = mc.split('.')
                    if len(split) > 2:
                        mcmajor = '.'.join(split[0:2])
                    split = mod.split('-')[0].split('.')
                    if len(split) > 2:
                        modmajor = '.'.join(split[0:2])
                    list.append((x, mc, mcmajor, mod, modmajor))
            except Exception as e:
                log("Warn - Parse Version", f"could not parse {x}")
                pass
        if len(list) > 0:
            self.cursor.execute(f'''INSERT IGNORE INTO {self.dbname}.{self.versions_table} (version, mcversion, majormcversion, modversion, majormodversion)
                                        VALUES {sep.join([f"('{x[0]}','{x[1]}','{x[2]}','{x[3]}','{x[4]}')" for x in list])}''')


class ModDataProvider:

    def __init__(self, db: Database, provider_name: str):
        self.db = db
        self.name = provider_name

    def download_data(self):
        log("DataProvider", f'start provider {self.name}')
        for mod_id in self.get_mod_ids():
            log("DataProvider", f'{self.name} - download {mod_id[0]}({mod_id[1]})')
            id = self.db.create_provider(mod_id[0], self.name)
            mod_data = self.get_mod(mod_id[1])
            self.db.save_total_downloads(id, time, mod_data)
            files_data = self.get_files(mod_id[1])
            self.db.create_versions([x[0] for x in files_data])
            self.db.create_files(id, [(x[0], x[1]) for x in files_data])
            self.db.save_file_downloads(id, time, [(x[0], x[2]) for x in files_data])
        log("DataProvider", f'finished provider {self.name}')

    def get_mod(self, mod_id) -> int:
        pass

    def get_files(self, mod_id) -> [(str, str, int)]:
        pass

    def get_mod_ids(self) -> [(str, str)]:
        pass


class Curseforge(ModDataProvider):

    def __init__(self, db: Database, url: str, api_key: str):
        super().__init__(db, "curseforge")
        self.curseforge_url = url
        self.api_key = api_key

    def get_mod(self, mod_id: str):
        return requests.get(f"{self.curseforge_url}/v1/mods/{mod_id}", headers={
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }).json()["data"]["downloadCount"]

    def get_files(self, mod_id: str):
        list = []
        all = 1
        index = 0

        while index < all:
            result = requests.get(f"{self.curseforge_url}/v1/mods/{mod_id}/files", headers={
                'Accept': 'application/json',
                'x-api-key': self.api_key
            }, params={
                'index': index
            }).json()
            list += result["data"]
            all = result["pagination"]["totalCount"]
            index = result["pagination"]["index"] + result["pagination"]["resultCount"]
            pass
        return [(x["fileName"].split("-", 1)[1][0:-4], x["displayName"], x["downloadCount"]) for x in list]

    def get_mod_ids(self) -> [(str, str)]:
        return get_mod_ids(os.environ['CURSEFORGE_PROJECTS'])


class Modrinth(ModDataProvider):

    def __init__(self, db: Database, url: str):
        super().__init__(db, "modrinth")
        self.url = url

    def get_mod(self, mod_id: str):
        return requests.get(f"{self.url}/project/{mod_id}", headers={
            'User-Agent': 'Cheaterpaul/ModStatistics'
        }).json()["downloads"]

    def get_files(self, version: str):
        return [(x["version_number"], x["name"], x["downloads"]) for x in
                requests.get(f"{self.url}/project/{version}/version", headers={
                    'User-Agent': 'Cheaterpaul/ModStatistics'
                }).json()]

    def get_mod_ids(self) -> [(str, str)]:
        return get_mod_ids(os.environ['MODRINTH_PROJECTS'])


def get_mod_ids(string: str) -> [(str, str)]:
    return [(y[0], y[1]) for y in [x.split("-") for x in string.split(",")]]


def check_environment_variables():
    if os.environ["DB_HOST"] is None:
        log("Error", "no DB_HOST given")
    if os.environ["DB_PORT"] is None:
        log("Error", "no DB_PORT given")
    if os.environ["DB_DATABASE"] is None:
        log("Error", "no DB_DATABASE given")
    if os.environ["DB_USER"] is None:
        log("Error", "no DB_USER given")
    if os.environ["DB_PASSWORD"] is None:
        log("Error", "no DB_PASSWORD given")
    if os.environ["CURSEFORGE_PROJECTS"] is None:
        log("Error", "no CURSEFORGE_PROJECTS given")
    else:
        try:
            if os.environ["CURSEFORGE_API_KEY"] is None:
                log("Error", "no CURSEFORGE_API_KEY given")
            get_mod_ids(os.environ["CURSEFORGE_PROJECTS"])
        except Exception as e:
            log("Error", "CURSEFORGE_PROJECTS format is wrong\n" + str(e))
            exit(1)
    if os.environ["MODRINTH_PROJECTS"] is None:
        log("Error", "no MODRINTH_PROJECTS given")
    else:
        try:
            get_mod_ids(os.environ["MODRINTH_PROJECTS"])
        except Exception as e:
            log("Error", "MODRINTH_PROJECTS format is wrong\n" + str(e))
            exit(1)


log("Modstats", "started")
check_environment_variables()

database = Database(host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]), p_database=os.environ["DB_DATABASE"],
                    user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"])

curseforge = Curseforge(database, "https://api.curseforge.com", os.environ['CURSEFORGE_API_KEY'])
modrinth = Modrinth(database, "https://api.modrinth.com/v2")

database.create_tables()

log("Modstats", "start provider")
curseforge.download_data()
modrinth.download_data()
log("Modstats", "finished provider")

database.close()

log("Modstats", "finished")
