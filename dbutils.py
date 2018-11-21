import sqlite3
import time
import discord_config

class ServerDatabase:

    def __init__(self):
        self.conn = sqlite3.connect(discord_config.SERVER_DB_FILE)
        self.conn.execute('pragma foreign_keys=on')
        self.dbcursor = self.conn.cursor()
        self.setup_database_if_new()

    def setup_database_if_new(self):
            self.dbcursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'server_member_system_alias'")
            table_exists = self.dbcursor.fetchone()[0] > 0 # Should always be 1 if the server_member_system_alias table exists. If it doesn't, value will be zero, and this is a brand new db.
            if not table_exists:
                print("New DB. Setting up.")
                self.setup_database()

    def setup_database(self):
        self.dbcursor.execute("drop table if exists game_four")
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

        self.dbcursor.execute("create table game_four (server_id string, game_id integer, channel_id string not null, player1_id string not null, player2_id string not null, board string not null, status integer not null, game_created_time integer not null, last_update_time integer not null, primary key(server_id, game_id))")

        self.conn.commit()
        print("Database setup complete.")

#### START OF GAME FOUR FUNCTIONS

    def new_game_four(self, server_id, channel_id, player1_id, player2_id):
        last_game = self.get_latest_game_four(server_id)
        new_game_id = 0

        if last_game is None:
            new_game_id = 1
        elif last_game['status'] in (1, 2):
            raise Exception("Game " + str(last_game['game_id']) + " is still in progress.")
        else:
            new_game_id = last_game['game_id'] + 1

        self.dbcursor.execute("insert into game_four (server_id, game_id, channel_id, player1_id, player2_id, board, status, game_created_time, last_update_time) values (?, ?, ?, ?, ?, ?, ?, ?, ?)", (server_id, new_game_id, channel_id, player1_id, player2_id, ' ' * 42, 1, int(time.time()), int(time.time())))
        self.conn.commit()

        return self.get_game_four(server_id, new_game_id)


    def find_active_game_four_player_turn(self, server_id, player_id):
        for game in self.dbcursor.execute("select game_id from game_four where server_id = ? and ((player1_id = ? and status = 1) or (player2_id = ? and status = 2)) ", (server_id, player_id, player_id)):
            return self.get_game_four(server_id, game[0])
        return None

    def get_latest_game_four(self, server_id):
        # max_game_id = 0
        for game in self.dbcursor.execute("select max(game_id) from game_four where server_id = ?", (server_id,)):
            # max_game_id = game_id[0]
            return self.get_game_four(server_id, game[0])
        return None


    def get_inactive_game_four_games(self, older_than_seconds):
        self.dbcursor.execute("select server_id, game_id, channel_id, player1_id, player2_id, board, status, game_created_time, last_update_time from game_four where status in (1,2) and last_update_time < ?", (older_than_seconds,))
        game_fours = []
        for row in self.dbcursor.fetchall():
            game_four = self.get_game_four(row[0], row[1])
            game_fours.append(game_four)
        return game_fours


    def get_game_four(self, server_id, game_id):
        self.dbcursor.execute("select server_id, game_id, channel_id, player1_id, player2_id, board, status, game_created_time, last_update_time from game_four where server_id = ? and game_id = ?", (server_id, game_id))
        game = self.dbcursor.fetchone()
        if game is not None:
            return {
                    'server_id': game[0],
                    'game_id': game[1],
                    'channel_id': game[2],
                    'player1_id': game[3],
                    'player2_id': game[4],
                    'board': game[5],
                    'status': game[6],
                    'game_created_time': game[7],
                    'last_update_time': game[8]
                    }
        else:
            return None

    def update_board(self, server_id, game_id, board):
        self.dbcursor.execute("update game_four set board = ?, last_update_time = ? where server_id = ? and game_id = ?", (board, int(time.time()), server_id, game_id))
        self.conn.commit()

    def update_status(self, server_id, game_id, status):
        self.dbcursor.execute("update game_four set status = ?, last_update_time = ? where server_id = ? and game_id = ?", (status, int(time.time()), server_id, game_id))
        self.conn.commit()

#### END OF GAME FOUR FUNCTIONS

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
