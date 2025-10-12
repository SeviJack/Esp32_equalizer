import pygame, socket, struct

# grid parameters
w, h = 32, 32
margin_x, margin_y = 6, 2
led_w, led_h = 12, 4
padding_x, padding_y = 20, 20
cell_x, cell_y = led_w + margin_x, led_h + margin_y
total_w = w * cell_x - margin_x + 2 * padding_x
total_h = h * cell_y - margin_y + 2 * padding_y

pygame.init()
screen = pygame.display.set_mode((total_w, total_h))
clock = pygame.time.Clock()

# color palette
core = (0, 255, 180)
edge = (0, 120, 90)
core_red = (255, 60, 40)
edge_red = (120, 20, 10)
bg = (5, 10, 10)

# socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 9999))
sock.setblocking(False)

# LED state buffer
grid = [0]*(w*h)

def draw_grid():
    screen.fill(bg)
    for y in range(h):
        for x in range(w):
            idx = y*w + (x if y % 2 == 0 else (w - 1 - x))  # serpentine
            val = grid[idx]
            edge_c, core_c = (edge_red, core_red) if y == h - 1 else (edge, core)
            X = padding_x + x * cell_x
            Y = padding_y + y * cell_y
            if val:
                pygame.draw.rect(screen, edge_c, (X, Y, led_w, led_h))
                pygame.draw.rect(screen, core_c, (X+1, Y+1, led_w-2, led_h-2))

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()
    try:
        data, _ = sock.recvfrom(w*h)
        grid = list(data)
    except BlockingIOError:
        pass

    draw_grid()
    pygame.display.flip()
    clock.tick(30)
