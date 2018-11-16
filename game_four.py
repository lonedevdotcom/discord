import texttable
import dbutils

class GameFour():

    def __init__(self):
        self.dbserver = dbutils.ServerDatabase()

    def new_game(self, server_id, channel_id, player1_id, player2_id):
        return self.dbserver.new_game_four(server_id, channel_id, player1_id, player2_id)

    def get_game(self, server_id, game_id):
        return self.dbserver.get_game_four(server_id, game_id)

    def display_board(self, server_id, game_id):
        board_table = texttable.Texttable()

        game = self.get_game(server_id, game_id)

        if game is None:
            raise Exception("Game " + str(game_id) + " not found on server " + str(server_id))

        board_values = game['board']
        for i in range(0, 6):
            board_table.add_row((board_values[i*7], board_values[i*7+1], board_values[i*7+2], board_values[i*7+3], board_values[i*7+4], board_values[i*7+5], board_values[i*7+6]))
        board_table.add_row((1,2,3,4,5,6,7))

        return board_table.draw()

    def get_column_drop_position(self, server_id, game_id, column):
        if column < 0 or column > 6:
            raise Exception("Invalid Number. Value must be between 1 and 7")

        game = self.get_game(server_id, game_id)
        board_values = game['board']

        highest_value = -1; # -1 will signify no position has been found.

        for i in range(0,6):
            if (board_values[i*7+column]) == ' ':
                highest_value = i * 7 + column

        if highest_value >= 0:
            return highest_value
        else:
            raise Exception("Column " + str(column+1) + " is full.")

    def find_active_player_game(self, server_id, player_id):
        return self.dbserver.find_active_game_four_player_turn(server_id, player_id)


    def drop_chip(self, server_id, game_id, column):
        game = self.get_game(server_id, game_id)

        if game['status'] not in (1, 2):
            raise Exception("Game " + str(game_id) + " has finished.")

        board_values = list(game['board'])
        chip = 'X' if game['status'] == 1 else 'O'
        board_drop_position = self.get_column_drop_position(server_id, game_id, column)
        board_values[board_drop_position] = chip
        new_board_string = ''.join(board_values)
        self.dbserver.update_board(server_id, game_id, new_board_string)
        
        if self.check_for_winner(server_id, game_id, chip):
            new_status = game['status'] + 2
            self.update_status(server_id, game_id, new_status)
            return new_status # Returns 3 for player 1 win, 4 for player 2 win.
        elif not ' ' in board_values:
            self.update_status(server_id, game_id, 5)
            return 5 # 5 = draw
        else:
            new_status = 1 if game['status'] == 2 else 2
            self.update_status(server_id, game_id, new_status)
            return new_status
        

    def update_status(self, server_id, game_id, status):
        self.dbserver.update_status(server_id, game_id, status)


    def check_for_winner(self, server_id, game_id, player_chip):
        game = self.get_game(server_id, game_id)
        board_values = list(game['board'])

        # search for horizontal 4-in-a-rows.
        for i in (0, 1, 2, 3, 7, 8, 9, 10, 14, 15, 16, 17, 21, 22, 23, 24, 28, 29, 30, 21, 35, 36, 37, 38):
            if board_values[i] == player_chip and board_values[i+1] == player_chip and board_values[i+2] == player_chip and board_values[i+3] == player_chip:
                return True

        # Now check for vertical 4-in-a-rows.
        for i in range(0,20):
            if board_values[i] == player_chip and board_values[i+7] == player_chip and board_values[i+14] == player_chip and board_values[i+21] == player_chip:
                return True

        # Check for right-down-diagonals
        for i in (0, 1, 2, 3, 7, 8, 9, 10, 14, 15, 16, 17):
            if board_values[i] == player_chip and board_values[i+8] == player_chip and board_values[i+16] == player_chip and board_values[i+24] == player_chip:
                return True

        # Check for left-down-diagonals
        for i in (3, 4, 5, 6, 10, 11, 12, 13, 17, 18, 19, 20):
            if board_values[i] == player_chip and board_values[i+6] == player_chip and board_values[i+12] == player_chip and board_values[i+18] == player_chip:
                return True

        return False

# tt = texttable.Texttable()
# for i in range(0,6):
    # tt.add_row((i*7, i*7+1, i*7+2, i*7+3, i*7+4, i*7+5, i*7+6))
# print(tt.draw())

# board_values = [' '] * 42 # setup a 42 cell string (6x7 grid)
# player_chip = 'X'
# game_over = False
# 
# display_board("".join(board_values))
# 
# # Loop round while there are still spaces(empty slots) on the board.
# while not game_over:
    # try:
        # column_drop = int(input("which column '" + player_chip + "'? "))
        # column_drop_index = column_drop - 1 # Python as a zero-based indexer, whereas humans prefer to start at 1 :)
        # position = get_column_drop_position(column_drop_index)
        # board_values[position] = player_chip
        # display_board("".join(board_values))
        # if check_for_winner(board_values, player_chip):
            # print(player_chip + " wins!")
            # game_over = True
        # elif not ' ' in board_values:
            # print("Draw!")
            # game_over = True
        # player_chip = 'X' if player_chip == 'O' else 'O'
    # except ValueError as ve:
        # print("Not a number. Must be between a number between 1 and 7")
    # except Exception as ex:
        # print(ex)
g4 = GameFour()
g4game = g4.new_game('10000', '20000', '30001', '30002')
g4.drop_chip('10000', g4game['game_id'], 4)
print(g4.find_active_player_game('10000', '30002'))
g4.update_status('10000', g4game['game_id'], 0)
# game = g4.get_game('10000', game_id)
# g4.drop_chip('10000', game['game_id'], 4)
# print(game['game_id'])
# print(g4.display_board('10000', game['game_id']))
