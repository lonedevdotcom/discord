import sqlite3
import discord_config

class ServerDatabase:

    def __init__(self):
        self.conn = sqlite3.connect(discord_config.SERVER_DB_FILE)
        self.conn.execute('pragma foreign_keys=on')
        self.dbcursor = self.conn.cursor()
        self.setup_database_if_new()

    def setup_database_if_new(self):
            self.dbcursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'server_member_system_alias'")
            table_exists = self.dbcursor.fetchone()[0] > 0 # Should always be 1 if the server_member_system_alias table exists. If it doesn't, this is a brand new db.
            if not table_exists:
                print("New DB. Setting up.")
                self.setup_database()

    def setup_database(self):
        self.dbcursor.execute("drop table if exists server_member_system_alias")
        self.dbcursor.execute("drop table if exists system")

        print("create table 'system'.")
        self.dbcursor.execute("create table system (system_type text primary key)")
        print("Adding data to 'system' table.")
        self.dbcursor.execute("replace into system (system_type) values (?)", ('ps4',))
        self.dbcursor.execute("replace into system (system_type) values (?)", ('pc',))
        self.dbcursor.execute("replace into system (system_type) values (?)", ('xbox',))

        print("create table 'server_member_system_alias'.")
        self.dbcursor.execute("create table server_member_system_alias (server_id text, member_id text, system_type text, system_alias text not null, primary key (server_id, member_id, system_type), foreign key (system_type) references system(system_type))")

        self.conn.commit()
        print("Database setup complete.")

    def update_server_member_system_alias(self, server_id, member_id, system_type, system_alias):
        self.dbcursor.execute("replace into server_member_system_alias (server_id, member_id, system_type, system_alias) values (?, ?, ?, ?)", (server_id, member_id, system_type, system_alias))
        self.conn.commit()
        
    def remove_server_member_system_alias(self, server_id, member_id, system_type):
        if system_type == 'all':
            self.dbcursor.execute("delete from server_member_system_alias where server_id = ? and member_id = ?", (server_id, member_id))
        else:
            self.dbcursor.execute("delete from server_member_system_alias where server_id = ? and member_id = ? and system_type = ?", (server_id, member_id, system_type))

        self.conn.commit()

    def get_all_server_member_system_aliases(self, server_id, system_type = 'all'):
        if system_type == 'all':
            self.dbcursor.execute("select * from server_member_system_alias where server_id = ? order by system_type", (server_id,))
            return self.dbcursor.fetchall()
        else:
            self.dbcursor.execute("select * from server_member_system_alias where server_id = ? and system_type = ? order by system_type", (server_id, system_type))
            return self.dbcursor.fetchall()
