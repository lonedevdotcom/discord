import texttable
import dbutils
import time
from PIL import Image, ImageDraw, ImageFont

class GameFour():
    STATUSES = ('Start Timed Out', 'Player 1 to play', 'Player 2 to play', 'GAME OVER: Player 1 wins!', 'GAME OVER: Player 2 wins!', 'GAME OVER: Draw')

    def __init__(self, dbref):
        self.dbserver = dbref


    def new_game(self, server_id, channel_id, player1_id, player2_id):
        if (player1_id == player2_id):
            raise Exception("Player id's are identical. Are you trying to play against yourself?")
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

    def end_inactive_games(self, older_than_seconds):
        older_time = int(time.time()) - older_than_seconds
        terminated_games = []
        for inactive_game in self.dbserver.get_inactive_game_four_games(older_time):
            if not 'X' in inactive_game['board']:
                # Game was never started.
                self.update_status(inactive_game['server_id'], inactive_game['game_id'], 0)
                terminated_games.append((inactive_game['server_id'], inactive_game['game_id'], inactive_game['channel_id'], "GAME OVER: Timed out before started."))
            elif inactive_game['status'] == 1:
                # Player 1 timed out. Player 2 wins!
                self.update_status(inactive_game['server_id'], inactive_game['game_id'], 4)
                terminated_games.append((inactive_game['server_id'], inactive_game['game_id'], inactive_game['channel_id'], "GAME OVER: Player 1 timed out. Player 2 wins!"))
            elif inactive_game['status'] == 2:
                # Player 2 timed out. Player 1 wins!
                self.update_status(inactive_game['server_id'], inactive_game['game_id'], 3)
                terminated_games.append((inactive_game['server_id'], inactive_game['game_id'], inactive_game['channel_id'], "GAME OVER: Player 2 timed out. Player 1 wins!"))
        return terminated_games


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


    def draw_board_image(self, board, player1_name, player2_name, status_text, ellipse_size=30, ellipse_padding=4, font_size=24):
        save_file = 'images/img01.png'
        board_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', font_size)
        box_size = ellipse_size + (ellipse_padding * 2)
        text_space = int(font_size * 4 * 1.2) # 4 rows of text. 1.20 is 20% either side of the text (I hope)
        img = Image.new('RGB', (box_size*7, box_size*6+text_space), color = 'blue')
        draw = ImageDraw.Draw(img)
        row1_y = box_size*6
        row2_y = box_size*6 + (font_size * 1.20)
        row3_y = box_size*6 + (font_size * 2 * 1.20)
        row4_y = box_size*6 + (font_size * 3 * 1.20)

        for column in range(0,7):
            for row in range(0,6):
                board_index = row * 7 + column

                fill_color = '#cdc9c9'
                if board[board_index] == 'X':
                    fill_color = 'red'
                elif board[board_index] == 'O':
                    fill_color = 'yellow'

                top_left_x = column * box_size + ellipse_padding
                top_left_y = row * box_size + ellipse_padding
                bottom_left_x = ((column+1) * box_size) - ellipse_padding
                bottom_left_y = ((row+1) * box_size) - ellipse_padding
                draw.ellipse((top_left_x, top_left_y, bottom_left_x, bottom_left_y), fill=fill_color)
            draw.text((column*box_size+(box_size/2)-8, row1_y), str(column+1), font=board_font)
        draw.ellipse((0, row2_y, font_size, row2_y+font_size), fill='red')
        draw.text((font_size+5, row2_y), player1_name, font=board_font)
    
        draw.ellipse((0, row3_y, font_size, row3_y+font_size), fill='yellow')
        draw.text((font_size+5, row3_y), player2_name, font=board_font)

        draw.text((0, row4_y), status_text, font=board_font)
        img.save(save_file)
        return save_file

