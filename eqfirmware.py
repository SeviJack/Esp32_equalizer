import pygame, random, pyaudio
import numpy as np
import sounddevice as sd
pygame.init()

SCALE_VALUE = 1  # adjust as needed  # 0.1 = small bars, 1.0 = full height
GATE = 0.02         # adjust as needed  # 0.02 = ignore <2% of max power

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
# audio parameters
samplerate = 48000
blocksize = 1024
input_device = 9  # Stereo Mix

bars = np.zeros(w)
smoothed = np.zeros(w)

def audio_callback(indata, frames, time, status):
    global bars
    # convert stereo to mono
    mono = np.mean(indata, axis=1)
    # FFT magnitude (skip DC)
    fft = np.fft.rfft(mono)
    mag = np.abs(fft)[1:]        # drop bin 0
    mag = np.log10(mag + 1)     # compress bass dominance

    
    # choose frequency window
    fmin, fmax = 20, 8000   # adjust as needed

    freqs = np.fft.rfftfreq(len(mono), 1.0 / samplerate)[1:]

    mask = (freqs >= fmin) & (freqs <= fmax)
    mag = mag[mask]
    freqs = freqs[mask]

    # map trimmed range to display width
    bins = np.array_split(np.arange(len(mag)), w)
    # values = [np.mean(mag[b]) for b in bins]
    weights = np.linspace(1.0, 5.0, w)  # 1x gain low → 3x gain high
    values = [np.mean(mag[b]) * weights[i] for i, b in enumerate(bins)]


    # normalize and noise gate
    values = np.array(values)
    values /= np.max(values + 1e-6)
    values[values < GATE] = 0     # gate: ignore <2 % of max power
    scale = SCALE_VALUE
    values *= h * scale

    # # values = np.log10(np.array(values) + 1)
    # values /= np.max(values + 1e-6)
    # values[values < 0.05] = 0
    # values *= h
    bars = values



stream = sd.InputStream(device=input_device,
                        samplerate=samplerate,
                        channels=2,
                        blocksize=blocksize,
                        callback=audio_callback)
stream.start()

# smoothing factor (lower = slower)
alpha = 0.15 #4
peak_bars = np.zeros

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            stream.stop()
            stream.close()
            exit()

    fade_surface.fill((0, 0, 0, 40))
    screen.blit(fade_surface, (0, 0))

    # exponential smoothing
    smoothed = alpha * bars + (1 - alpha) * smoothed

    for x in range(w):
        height = int(smoothed[x])
        X = padding_x + x * cell_x

        # draw main column
        for y in range(height):
            Y = total_h - padding_y - (y + 1) * cell_y
            edge_c, core_c = edge, core
            pygame.draw.rect(screen, edge_c, (X, Y, led_w, led_h))
            pygame.draw.rect(screen, core_c, (X + 1, Y + 1, led_w - 2, led_h - 2))

        # permanent red base
        Y_base = total_h - padding_y - cell_y
        pygame.draw.rect(screen, edge_red, (X, Y_base, led_w, led_h))
        pygame.draw.rect(screen, core_red, (X + 1, Y_base + 1, led_w - 2, led_h - 2))

    pygame.display.flip()
    clock.tick(30)