import pygame, random
pygame.init()

w, h = 32, 32

margin_x, margin_y = 6, 2  # margin between cells
led_w, led_h = 12, 4      # pixel size (3×1 ratio example)
cell_x, cell_y = led_w + margin_x, led_h + margin_y   # grid spacing

screen = pygame.display.set_mode((w*cell_x, h*cell_y), pygame.SCALED)
pygame.transform.set_smoothscale_backend("GENERIC")    
clock = pygame.time.Clock()

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()
    screen.fill((0, 0, 0))
    for y in range(h):
        for x in range(w):
            if y == 31 :
                c = (255, 0, 0)
            else:
                c = (0,255,0)
            rect = (x * cell_x, y * cell_y, led_w, led_h)

            pygame.draw.rect(screen, c, rect)
    pygame.display.flip()
    clock.tick(30)
