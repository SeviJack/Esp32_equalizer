import pygame, random, pyaudio
import numpy as np
import sounddevice as sd
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

# audio setup
samplerate = 48000
blocksize = 1024

# sd.default.device = ("Microsoft Sound Mapper - Output", "Microsoft Sound Mapper - Output (loopback)")

bars = np.zeros(w)

def audio_callback(indata, frames, time, status):
    global bars
    # stereo to mono
    mono = np.mean(indata, axis=1)
    # FFT
    spectrum = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), 1.0/samplerate)
    # Log-scale bins mapped to grid width
    freq_bins = np.logspace(np.log10(20), np.log10(20000), w+1)
    values = []
    for i in range(w):
        idx = np.where((freqs >= freq_bins[i]) & (freqs < freq_bins[i+1]))[0]
        if len(idx):
            values.append(np.mean(spectrum[idx]))
        else:
            values.append(0)
    # Normalize to fit LED grid height
    values = np.array(values)
    values = np.clip(values / np.max(values + 1e-6) * h, 0, h)
    bars = values

    

input_device = 25  # Stereo Mix under WASAPI
stream = sd.InputStream(device=input_device,
                        samplerate=44100,
                        channels=2,
                        callback=audio_callback)
stream.start()

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            stream.stop()
            stream.close()
            exit()

    fade_surface.fill((0, 0, 0, 40))
    screen.blit(fade_surface, (0, 0))
    for x in range(w):
        height = int(bars[x])
        X = padding_x + x * cell_x

        # draw bar (teal)
        for y in range(height):
            Y = total_h - padding_y - (y + 1) * cell_y
            edge_c, core_c = edge, core
            pygame.draw.rect(screen, edge_c, (X, Y, led_w, led_h))
            pygame.draw.rect(screen, core_c, (X + 1, Y + 1, led_w - 2, led_h - 2))

        # always draw red base row
        Y_base = total_h - padding_y - cell_y
        pygame.draw.rect(screen, edge_red, (X, Y_base, led_w, led_h))
        pygame.draw.rect(screen, core_red, (X + 1, Y_base + 1, led_w - 2, led_h - 2))


    pygame.display.flip()
    clock.tick(30)
