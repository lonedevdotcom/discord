import sqlite3

class ServerDatabase:

    def __init__(self):
        self.conn = sqlite3.connect('/home/pi/discord/serverdb')
        self.conn.execute('pragma foreign_keys=on')
        self.dbcursor = self.conn.cursor()

    def setup_database(self):
        self.create_server_table()

    def create_server_table(self):
        self.dbcursor.execute("drop table if exists server")
        self.dbcursor.execute("drop table if exists server_member_system_alias")
        self.dbcursor.execute("drop table if exists system")

        self.dbcursor.execute("create table server (server_id text primary key, last_update_timestamp integer)")

        self.dbcursor.execute("create table system (system_type text primary key)")
        self.dbcursor.execute("replace into system (system_type) values (?)", ('ps4',))
        self.dbcursor.execute("replace into system (system_type) values (?)", ('pc',))
        self.dbcursor.execute("replace into system (system_type) values (?)", ('xbox',))

        self.dbcursor.execute("create table server_member_system_alias (server_id text, member_id text, system_type text, system_alias text not null, primary key (server_id, member_id, system_type), foreign key (system_type) references system(system_type))")

        self.conn.commit()

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
        
    def update_last_update_timestamp(self, server_id, timestamp):
        self.dbcursor.execute("replace into server (server_id, last_update_timestamp) values (?, ?)", (server_id, timestamp))
        self.conn.commit()

    def get_last_update_timestamp(self, server_id):
        self.dbcursor.execute("select last_update_timestamp from server where server_id = ?", (server_id,))
        row = self.dbcursor.fetchone()
        return row[0] if row is not None else None
