
import pygame
import numpy as np
import sounddevice as sd

pygame.init()

SCALE_VALUE = 1  # adjust as needed  # 0.1 = small bars, 1.0 = full height
GATE = 0.02         # adjust as needed  # 0.02 = ignore <2% of max power
DC_CUTTOFF = 0


# find default output and its loopback
default_output = sd.default.device[1]
output_name = sd.query_devices(default_output)['name']

# look for "(loopback)" version of that device
devices = sd.query_devices()
# print(devices)
loopback_index = None
for i, d in enumerate(devices):
    if "Loopback" in d['name'] and output_name.split(' (')[0] in d['name']:
        loopback_index = i
        break
if loopback_index is None:
    # print("No matching loopback device found. Using default input.")
    loopback_index = sd.default.device[0]

input_device = loopback_index
# print(f"Using loopback: {sd.query_devices(input_device)['name']}")


w, h = 32, 32
margin_x, margin_y = 6, 2
led_w, led_h = 12, 4
padding_x, padding_y = 20, 20

cell_x, cell_y = led_w + margin_x, led_h + margin_y
total_w = w * cell_x - margin_x + 2 * padding_x
total_h = h * cell_y - margin_y + 2 * padding_y
clock = pygame.time.Clock()

silence_timer = 0.0
silence_threshold = 0.001   # adjust
silence_timeout = 3.0       # seconds before turning off
active = True

# VFD color palette
core = (0, 255, 180)
edge = (0, 120, 90)
core_red = (255, 60, 40)
edge_red = (120, 20, 10)
bg = (5, 10, 10)

screen = pygame.display.set_mode((total_w, total_h), pygame.RESIZABLE)
base_surface = pygame.Surface((total_w, total_h))  # offscreen render
fade_surface = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
# audio parameters
samplerate = 48000
blocksize = 1024
# input_device = 30

bars = np.zeros(w)
smoothed = np.zeros(w)



def audio_callback(indata, frames, time, status):
    global bars
    # convert stereo to mono
    mono = np.mean(indata, axis=1)
    # FFT magnitude (skip DC) + mild compression + equalization
    fft = np.fft.rfft(mono)
    mag = np.abs(fft)[DC_CUTTOFF:]
    mag = np.log10(mag + 1)
    freqs = np.fft.rfftfreq(len(mono), 1.0 / samplerate)[DC_CUTTOFF:]
    a_weight = (freqs**2) / (freqs**2 + 200**2)
    mag *= a_weight

    # choose frequency window
    fmin, fmax = 20, 8000   # adjust as needed

    freqs = np.fft.rfftfreq(len(mono), 1.0 / samplerate)[DC_CUTTOFF:]

    mask = (freqs >= fmin) & (freqs <= fmax)
    mag = mag[mask]
    freqs = freqs[mask]


    # map trimmed range to display width
    bins = np.array_split(np.arange(len(mag)), w)
    # values = [np.mean(mag[b]) for b in bins]
    weights = np.linspace(0.9, 5.0, w)  # 1.5x gain low → 5x gain high
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

    global silence_timer, active
    # measure overall power
    power = np.mean(np.abs(mono))

    if power < silence_threshold:
        silence_timer += blocksize / samplerate
    else:
        silence_timer = 0

    # deactivate after sustained silence
    # if silence_timer > silence_timeout:
    #     active = False
    # else:
    #     active = True



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
            stream.stop(); stream.close(); exit()
        elif e.type == pygame.VIDEORESIZE:
            # Optional: handle aspect ratio or update variables if needed
            screen = pygame.display.set_mode(e.size, pygame.RESIZABLE)


    fade_surface.fill((0, 0, 0, 40))
    base_surface.blit(fade_surface, (0, 0))

    # exponential smoothing
    smoothed = alpha * bars + (1 - alpha) * smoothed 
    if not active:
        base_surface.fill(bg)  
    else:
        # draw bars on base_surface
        for x in range(w):
            height = int(smoothed[x])
            X = padding_x + x * cell_x
            for y in range(height):
                Y = total_h - padding_y - (y + 1) * cell_y
                pygame.draw.rect(base_surface, edge, (X, Y, led_w, led_h))
                pygame.draw.rect(base_surface, core, (X+1, Y+1, led_w-2, led_h-2))
            # red base
            Y_base = total_h - padding_y - cell_y
            pygame.draw.rect(base_surface, edge_red, (X, Y_base, led_w, led_h))
            pygame.draw.rect(base_surface, core_red, (X+1, Y_base+1, led_w-2, led_h-2))

    # after all drawing done on base_surface:
    scaled = pygame.transform.smoothscale(base_surface, screen.get_size())
    screen.blit(scaled, (0, 0))
    pygame.display.flip()
    clock.tick(30)

