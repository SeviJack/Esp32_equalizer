import pygame, random, pyaudio, numpy, soundfile as sf
pygame.init()

w, h = 32, 32
margin_x, margin_y = 6, 2
led_w, led_h = 12, 4
padding_x, padding_y = 20, 20

cell_x, cell_y = led_w + margin_x, led_h + margin_y
total_w = w * cell_x - margin_x + 2 * padding_x
total_h = h * cell_y - margin_y + 2 * padding_y
screen = pygame.display.set_mode((total_w, total_h))
clock = pygame.time.Clock()

# VFD color palette
core = (0, 255, 180)
edge = (0, 120, 90)
core_red = (255, 60, 40)
edge_red = (120, 20, 10)
bg = (5, 10, 10)

fade_surface = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()

    fade_surface.fill((0, 0, 0, 40))
    screen.blit(fade_surface, (0, 0))

    for y in range(h):
        for x in range(w):
            #audio monitoring logic
            #frequency to leds

            # last row red, others teal
            if y == h - 1:
                edge_c, core_c = edge_red, core_red
            else:
                edge_c, core_c = edge, core

            X = padding_x + x * cell_x
            Y = padding_y + y * cell_y

            pygame.draw.rect(screen, edge_c, (X, Y, led_w, led_h))
            pygame.draw.rect(screen, core_c, (X + 1, Y + 1, led_w - 2, led_h - 2))

    pygame.display.flip()
    clock.tick(30)
