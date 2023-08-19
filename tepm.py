#chess,
#modularity of bishop, rukh(elephant)
#move validation start to end

class Chess_element:
    def __init__(self, color='black', row=0, col=0):
        self.color = color
        self.row = row
        self.col = col

#modularity of bishop
class Bishop(Chess_element):
    def is_valid_move(self, new_row, new_col):
        return abs(new_row - self.row) == abs(new_col - self.col)

#modularity of rukh
class Rukh(Chess_element):
    def is_valid_move(self, new_row, new_col):
        return new_row == self.row or new_col == self.col

class Chessboard:
    def __init__(self):
        self.board = [[None] * 8 for _ in range(8)]
        self.killed_pieces = []
    
    def place_piece(self, piece, row, col):
        piece.row, piece.col = row, col
        self.board[row][col] = piece
    
    def move_piece(self, piece, new_row, new_col):
        if 0 <= new_row <= 7 and 0 <= new_col <= 7 and piece.is_valid_move(new_row, new_col):
            self.board[piece.row][piece.col] = None
            self.place_piece(piece, new_row, new_col)
            return True
        else:
            return False

    #move_piece_with_obstacles fucntion is same as above move_piece function, but with extra functionality
    #while going from start to end postion, if we find a chess element, if this element is with different color we will kill it and assign this as new postion of our element
    # if we find element which is of same color, then we will assign just before possible postion to our element, since bishop or rukh can't cross an existing element. 
    def move_piece_with_obstacles(self, piece, new_row, new_col):
        if 0 <= new_row <= 7 and 0 <= new_col <= 7 and piece.is_valid_move(new_row, new_col): 
            killed_piece = None
            row_step = 1 if new_row > piece.row else -1 if new_row < piece.row else 0
            col_step = 1 if new_col > piece.col else -1 if new_col < piece.col else 0
            
            row,col = piece.row, piece.col
            while row != new_row or col != new_col:
                row += row_step
                col += col_step                
                if self.board[row][col] is not None:
                    if self.board[row][col].color != piece.color:
                        killed_piece = self.board[row][col]
                        self.board[killed_piece.row][killed_piece.col] = None
                        self.killed_pieces.append(killed_piece)
                        print(f"Killed piece at ({row}, {col})")
                        break
                    else:
                        row -= row_step
                        col -= col_step
                        print(f"changed new positon is ({row}, {col})")
                        break
                
            self.board[piece.row][piece.col] = None
            self.place_piece(piece,row,col)
            return True
        
        return False

# Example
chessboard = Chessboard()
bishop = Bishop("white")
rukh = Rukh("black")

#start positions
chessboard.place_piece(bishop, 0, 2)
chessboard.place_piece(rukh, 6,2)
chessboard.place_piece(rukh, 3,5)
#end positons

print(chessboard.move_piece(rukh, 5, 7))    # False

print(chessboard.move_piece_with_obstacles(bishop, 4, 4))  # False
print(chessboard.move_piece_with_obstacles(bishop, 4, 6))  #Killed piece at (3, 5)     True

