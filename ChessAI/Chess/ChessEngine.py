"""
this class is responsible for storing all the info about the current state of the chess game. It will also be responsible for determinig the valid moves at the current state.
 It will also keep a move log
"""


class GameState():
    def __init__(self):
        # board is an 8*8 2d list , each element of the list has 2 characters.
        # The first character reps the color of the pieces
        # The second character reps the type of pieces
        # The -- reps the empty spaces
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        self.moveLog = []
        self.whiteToMove = True
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.inCheck = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False
        self.enpassantPossible = ()
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]

    '''
    Takes a move as a parameter and executes it(will not work with castling, en_passant and pawn  promotion)'''

    def makeMove(self, move):
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.board[move.startRow][move.startCol] = "--"
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove  # swap players
        # update kings location
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)
        # pawn promotion choice
        if move.pawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'
        # if en passant move, must update the board to capture the pawn
        if move.enPassant:
            self.board[move.startRow][move.endCol] = "--"  # capturing piece
        # if pawn moves twice, next move can capture en passant
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.endCol)
        else:
            self.enpassantPossible = ()

        self.enpassantPossibleLog.append(self.enpassantPossible)

        # castle moves
        if move.castle:
            if move.endCol - move.startCol == 2:  # kingside
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]  # move rook
                self.board[move.endRow][move.endCol + 1] = '--'  # empty space where rook was
            else:  # queenside
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]  # move rook
                self.board[move.endRow][move.endCol - 2] = '--'  # empty space where rook was

        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                                 self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

    '''
    undo last move'''

    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove
            # update kings location
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

            # undo en passant move
            if move.enPassant:
                self.board[move.endRow][move.endCol] = '--'
                self.board[move.startRow][move.endCol] = move.pieceCaptured

            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]

            self.castleRightsLog.pop()
            newRights = self.castleRightsLog[-1]
            self.currentCastlingRight = CastleRights(newRights.wks, newRights.wqs, newRights.bks, newRights.bqs)

            if move.castle:
                if move.endCol - move.startCol == 2:
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = '--'
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = '--'

            self.checkmate = False
            self.stalemate = False

    '''
    all moves considering checks'''

    def getValidMoves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = []
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i)
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else:
                self.getKingMoves(kingRow, kingCol, moves)
        else:
            moves = self.getAllPossibleMoves()

        if len(moves) == 0:
            if self.inCheck:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.stalemate = False
            self.checkmate = False
        return moves

    def checkForPinsAndChecks(self):

        pins = []  # squares pinned and the direction its pinned from
        checks = []  # squares where enemy is applying a check
        inCheck = False
        if self.whiteToMove:
            enemyColor = 'b'
            allyColor = 'w'
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = 'w'
            allyColor = 'b'
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        # check outwards from king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possiblePin = ()  # reset possible pins
            for i in range(1, 8):
                endRow = startRow + direction[0] * i
                endCol = startCol + direction[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == ():  # first allied piece could be pinned
                            possiblePin = (endRow, endCol, direction[0], direction[1])
                        else:  # 2nd allied piece - no check or pin from this direction
                            break
                    elif endPiece[0] == enemyColor:
                        pieceType = endPiece[1]
                        if (0 <= j <= 3 and pieceType == 'R') or (4 <= j <= 7 and pieceType == 'B') or (
                                i == 1 and pieceType == 'p' and (
                                (enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or (
                                pieceType == 'Q') or (i == 1 and pieceType == 'K'):
                            if possiblePin == ():  # no piece blocking, so check
                                inCheck = True
                                checks.append((endRow, endCol, direction[0], direction[1]))
                                break
                            else:  # piece blocking so pin
                                pins.append(possiblePin)
                                break
                        else:  # enemy piece not applying checks
                            break
                else:
                    break  # off board
        # check for knight checks
        knightMoves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knightMoves:
            endRow = startRow + move[0]
            endCol = startCol + move[1]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':  # enemy knight attacking a king
                    inCheck = True
                    checks.append((endRow, endCol, move[0], move[1]))
        return inCheck, pins, checks

        # pins = []
        # checks = []
        # inCheck = False
        # if self.whiteToMove:
        #     enemyColor = "b"
        #     allyColor = "w"
        #     startRow = self.whiteKingLocation[0]
        #     startCol = self.whiteKingLocation[1]
        # else:
        #     enemyColor = "w"
        #     allyColor = "b"
        #     startRow = self.blackKingLocation[0]
        #     startCol = self.blackKingLocation[1]
        #
        # directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        # for j in range(len(directions)):
        #     d = directions[j]
        #     possiblePin = ()
        #     for i in range(1, 8):
        #         endRow = startRow + d[0] * i
        #         endCol = startCol + d[1] * i
        #         if 0 <= endRow < 8 and 0 <= endCol < 8:
        #             endPiece = self.board[endRow][endCol]
        #             if endPiece[0] == allyColor and endPiece[1] != 'K':
        #                 if possiblePin == ():
        #                     possiblePin = (endRow, endCol, d[0], d[1])
        #                 else:
        #                     break
        #             elif endPiece[0] == enemyColor:
        #                 type = endPiece[1]
        #                 if (0 <= j <= 3 and type == 'R') or \
        #                         (4 <= j <= 7 and type == 'B') or \
        #                         (i == 1 and type == 'p' and (
        #                                 (enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
        #                         (type == 'Q') or (i == 1 and type == 'K'):
        #                     if possiblePin == ():
        #                         inCheck = True
        #                         checks.append((endRow, endCol, d[0], d[1]))
        #                         break
        #                     else:
        #                         pins.append(possiblePin)
        #                         break
        #                 else:
        #                     break
        #
        # knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        # for m in knightMoves:
        #     endRow = startRow + m[0]
        #     endCol = startCol + m[1]
        #     if 0 <= endRow < 8 and 0 <= endCol < 8:
        #         endPiece = self.board[endRow][endCol]
        #         if endPiece[0] == enemyColor and endPiece[1] == 'N':
        #             inCheck = True
        #             checks.append((endRow, endCol, m[0], m[1]))
        #
        # return inCheck, pins, checks

    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        return moves

    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()

        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            enemyColor = 'b'
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmount = 1
            startRow = 1
            enemyColor = 'w'
            kingRow, kingCol = self.blackKingLocation

        if self.board[r + moveAmount][c] == "--":  # 1 square advance
            if not piecePinned or pinDirection == (moveAmount, 0):
                moves.append(Move((r, c), (r + moveAmount, c), self.board))
                if r == startRow and self.board[r + 2 * moveAmount][c] == "--":  # 2 square advance
                    moves.append(Move((r, c), (r + 2 * moveAmount, c), self.board))
        if c - 1 >= 0:  # capture to the left
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[r + moveAmount][c - 1][0] == enemyColor:  # enemy piece to capture
                    moves.append(Move((r, c), (r + moveAmount, c - 1), self.board))
                if (r + moveAmount, c - 1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c - 1)
                            outsideRange = range(c + 1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, - 1)
                            outsideRange = range(c - 2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmount, c - 1), self.board, enPassant=True))
        if c + 1 <= 7:  # captures to the right
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[r + moveAmount][c + 1][0] == enemyColor:  # enemy piece to capture
                    moves.append(Move((r, c), (r + moveAmount, c + 1), self.board))
                if (r + moveAmount, c + 1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r + moveAmount, c + 1), self.board, enPassant=True))

    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # up, left, down, right
        enemyColor = "b" if self.whiteToMove else "w"
        for direction in directions:
            for i in range(1, 8):
                endRow = r + direction[0] * i
                endCol = c + direction[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    if (not piecePinned or pinDirection == direction or
                            pinDirection == (-direction[0], -direction[1])):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:  # capture enemy piece
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break

        # directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        # enemyColor = "b" if self.whiteToMove else "w"
        # for d in directions:
        #     for i in range(1, 8):
        #         endRow = r + d[0] * i
        #         endcol = c + d[1] * i
        #         if 0 <= endRow < 8 and 0 <= endcol < 8:  # on board
        #             endPiece = self.board[endRow][endcol]
        #             if endPiece == "--":  # empty space is valid
        #                 moves.append(Move((r, c), (endRow, endcol), self.board))
        #             elif endPiece[0] == enemyColor:  # enemy piece is valid
        #                 moves.append(Move((r, c), (endRow, endcol), self.board))
        #                 break
        #             else:  # friendly piece is invalid
        #                 break
        #         else:  # off board
        #
        #             break

    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        knightMoves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        allyColor = "w" if self.whiteToMove else "b"
        for move in knightMoves:
            endRow = r + move[0]
            endCol = c + move[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:  # so its either enemy piece or empty square
                        moves.append(Move((r, c), (endRow, endCol), self.board))

        # piecePinned = False
        # for i in range(len(self.pins) - 1, -1, -1):
        #     if self.pins[i][0] == r and self.pins[i][1] == c:
        #         piecePinned = True
        #         self.pins.remove(self.pins[i])
        #         break
        # knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        # allyColor = "w" if self.whiteToMove else "b"
        # for m in knightMoves:
        #     endRow = r + m[0]
        #     endCol = c + m[1]
        #     if 0 <= endRow < 8 and 0 <= endCol < 8:
        #         endPiece = self.board[endRow][endCol]
        #         if endPiece[0] != allyColor:
        #             moves.append(Move((r, c), (endRow, endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # diagonals: up/left up/right down/right down/left
        enemyColor = "b" if self.whiteToMove else "w"
        for direction in directions:
            for i in range(1, 8):
                endRow = r + direction[0] * i
                endCol = c + direction[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # check if the move is on board
                    if not piecePinned or pinDirection == direction or pinDirection == (
                            -direction[0], -direction[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":  # empty space is valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:  # capture enemy piece
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break

        # piecePinned = False
        # pinDirection = ()
        # for i in range(len(self.pins) - 1, -1, -1):
        #     if self.pins[i][0] == r and self.pins[i][1] == c:
        #         piecePinned = True
        #         pinDirection = (self.pins[i][2], self.pins[i][3])
        #         self.pins.remove(self.pins[i])
        #         break
        # directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        # enemyColor = "b" if self.whiteToMove else "w"
        # for d in directions:
        #     for i in range(1, 8):
        #         endRow = r + d[0] * i
        #         endcol = c + d[1] * i
        #         if 0 <= endRow < 8 and 0 <= endcol < 8:  # on board
        #             endPiece = self.board[endRow][endcol]
        #             if endPiece == "--":  # empty space is valid
        #                 moves.append(Move((r, c), (endRow, endcol), self.board))
        #             elif endPiece[0] == enemyColor:  # enemy piece is valid
        #                 moves.append(Move((r, c), (endRow, endcol), self.board))
        #                 break
        #             else:
        #                 break
        #         else:  # off board
        #             break

    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        kingRow = (-1, -1, -1, 0, 0, 1, 1, 1)
        kingCol = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + kingRow[i]
            endCol = c + kingCol[i]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:  # not an ally piece - empty or enemy
                    # place king on end square and check for checks
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    # place king back on original location
                    if allyColor == "w":
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)

        # kingMoves = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        # allyColor = "w" if self.whiteToMove else "b"
        # for i in range(8):
        #     endRow = r + kingMoves[i][0]
        #     endCol = c + kingMoves[i][1]
        #     if 0 <= endRow < 8 and 0 <= endCol < 8:
        #         endPiece = self.board[endRow][endCol]
        #         if endPiece[0] != allyColor:
        #             moves.append(Move((r, c), (endRow, endCol), self.board))

    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return
        if (self.whiteToMove and self.currentCastlingRight.wks) or (
                not self.whiteToMove and self.currentCastlingRight.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (
                not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove  # switch to opponent's turn
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove  # switch turns back
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:  # square is under attack
                return True
        return False

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c + 1] == '--' and self.board[r][c + 2] == '--' and \
                not self.squareUnderAttack(r, c + 1) and not self.squareUnderAttack(r, c + 2):
            moves.append(Move((r, c), (r, c + 2), self.board, castle=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c - 1] == '--' and self.board[r][c - 2] == '--' and self.board[r][c - 3] == '--' and \
                not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
            moves.append(Move((r, c), (r, c - 2), self.board, castle=True))

    def updateCastleRights(self, move):
        if move.pieceMoved == 'wK':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.bks = False

        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.endRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, enPassant=False, castle=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.pawnPromotion = self.pieceMoved[1] == 'bp' and (self.endRow == 0 or self.endRow == 7)
        self.castle = castle
        self.enPassant = enPassant
        if enPassant:
            self.pieceCaptured = 'bp' if self.pieceMoved == 'wp' else 'wp'
        self.isCapture = self.pieceCaptured != '--'
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    '''
    Overriding the equals method'''

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startRow) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def __str__(self):
        if self.castle:
            return "O-O" if self.endCol == 6 else "O-O-O"

        endSquare = self.getRankFile(self.endRow, self.endCol)

        if self.pieceMoved[1] == 'p':
            if self.isCapture:
                return self.colsToFiles[self.startCol] + "x" + endSquare
            else:
                return endSquare

        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += 'x'
        return moveString + endSquare
