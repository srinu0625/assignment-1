import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 480, 480
SQUARE = WIDTH // 8

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")

# Load images
pieces = {}
names = ["wp","wr","wn","wb","wq","wk","bp","br","bn","bb","bq","bk"]

for name in names:
    pieces[name] = pygame.transform.scale(
        pygame.image.load(f"images/{name}.png"), (SQUARE, SQUARE)
    )

# Board setup
board = [
    ["br","bn","bb","bq","bk","bb","bn","br"],
    ["bp","bp","bp","bp","bp","bp","bp","bp"],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["wp","wp","wp","wp","wp","wp","wp","wp"],
    ["wr","wn","wb","wq","wk","wb","wn","wr"]
]

selected = None

def draw_board():
    colors = [(240,217,181), (181,136,99)]
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, (col*SQUARE, row*SQUARE, SQUARE, SQUARE))

            piece = board[row][col]
            if piece:
                screen.blit(pieces[piece], (col*SQUARE, row*SQUARE))


def get_square(pos):
    x, y = pos
    return y // SQUARE, x // SQUARE


# Game loop
while True:
    draw_board()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            row, col = get_square(pygame.mouse.get_pos())

            if selected is None:
                if board[row][col] != "":
                    selected = (row, col)
            else:
                r, c = selected
                board[row][col] = board[r][c]
                board[r][c] = ""
                selected = None