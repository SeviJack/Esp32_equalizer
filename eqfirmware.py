import pygame, random
pygame.init()

w, h = 32, 32
margin_x, margin_y = 4, 2
led_w, led_h = 12, 4
padding_x, padding_y = 4, 2  # spacing from screen edges

cell_x, cell_y = led_w + margin_x, led_h + margin_y
total_w = w * cell_x - margin_x + 2 * padding_x
total_h = h * cell_y - margin_y + 2 * padding_y
screen = pygame.display.set_mode((total_w, total_h))
clock = pygame.time.Clock()

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()
    screen.fill((0, 0, 0))
    for y in range(h):
        for x in range(w):
            c = (255, 0, 0) if y == 31 else (0, 255, 120)
            rect = (
                padding_x + x * cell_x,
                padding_y + y * cell_y,
                led_w,
                led_h
            )
            pygame.draw.rect(screen, c, rect)
    pygame.display.flip()
    clock.tick(30)
