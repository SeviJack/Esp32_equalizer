import pygame, sys
import numpy as np
import sounddevice as sd
import win32gui, win32con

#todo
# custom window frame
# - transparent background button
# - click to toggle topmost
# - click and drag to move window
# - resize handle
# fix the damn logscale for bass

pygame.display.set_caption("ESP32 Audio Visualizer Emulator")
pygame.init()
font = pygame.font.SysFont("Consolas", 10)  # small, clear font

fmin, fmax = 40, 6000  # Hz range
SCALE_VALUE = 1  # adjust as needed  # 0.1 = small gain_nodes, 1.0 = full height
GATE = 0.02         # adjust as needed  # 0.02 = ignore <2% of max power
DC_CUTTOFF = 0

# display parameters
w, h = 32, 32
margin_x, margin_y = 6, 2
led_w, led_h = 12, 4
padding_x, padding_y_top, padding_y_bottom = 20, 20, 30

cell_x, cell_y = led_w + margin_x, led_h + margin_y
total_w = w * cell_x - margin_x + 2 * padding_x
total_h = h * cell_y - margin_y + padding_y_top + padding_y_bottom
clock = pygame.time.Clock()

# VFD color palette
core = (0, 255, 180)
edge = (0, 120, 90)
core_red = (255, 60, 40)
edge_red = (120, 20, 10)
bg = (5, 10, 10)
label_color = (100, 100, 100)


screen = pygame.display.set_mode((total_w, total_h), pygame.RESIZABLE) #noframe
base_surface = pygame.Surface((total_w, total_h))  # offscreen render
fade_surface = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

# audio parameters
samplerate = 48000
blocksize = 8192*2  # ~0.16s latency

gain_nodes = np.zeros(w)
smoothed = np.zeros(w)

# find default output and its loopback
default_output = sd.default.device[1]
output_name = sd.query_devices(default_output)['name']

# look for "(loopback)" version of that device (maybe thread this?)
devices = sd.query_devices()
loopback_index = None
for i, d in enumerate(devices):
    if "Loopback" in d['name'] and output_name.split(' (')[0] in d['name']:
        loopback_index = i
        break
if loopback_index is None:
    loopback_index = sd.default.device[0]

input_device = loopback_index

def make_top_level_window(N, cutoff=DC_CUTTOFF):
    hwnd = pygame.display.get_wm_info()["window"]
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                           win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_TOPMOST)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | cutoff)
make_top_level_window(screen, DC_CUTTOFF)

def audio_callback(indata, frames, time, status):
    global gain_nodes, fmin, fmax
    
    # stereo → mono
    mono = np.mean(indata, axis=1)
    # --- Dual-FFT hybrid for low + high frequencies ---

    # long FFT for low end
    low_block = 8192     # ~0.17 s latency @48k
    low_window = np.hanning(min(len(mono), low_block))
    low_fft = np.fft.rfft(mono[:low_block] * low_window)
    mag_low = np.abs(low_fft)
    freqs_low = np.fft.rfftfreq(low_block, 1.0 / samplerate)

    # short FFT for highs
    high_block = 2048    # ~0.043 s latency
    high_window = np.hanning(min(len(mono), high_block))
    high_fft = np.fft.rfft(mono[:high_block] * high_window)
    mag_high = np.abs(high_fft)
    freqs_high = np.fft.rfftfreq(high_block, 1.0 / samplerate)

    # merge around crossover frequency
    split = 300  # Hz
    mask_low = freqs_low < split
    mask_high = freqs_high >= split

    freqs = np.concatenate((freqs_low[mask_low], freqs_high[mask_high]))
    mag = np.concatenate((mag_low[mask_low], mag_high[mask_high]))


    # magnitude spectrum
    mag = np.log10(mag + 1)
    # A-weighting style correction
    a_weight = (freqs**2) / (freqs**2 + 200**2)
    mag *= a_weight

    # restrict to frequency window
    mask = (freqs >= fmin) & (freqs <= fmax)
    mag = mag[mask]
    freqs = freqs[mask]

    # combine first few low bins to smooth bass
    if len(mag) > 5:
        mag[:5] = np.mean(mag[:5])

    # --- LOG-SPACED BINS ---
    freq_bins = np.geomspace(fmin, fmax, w + 1)
    values = []
    for i in range(w):
        band = (freqs >= freq_bins[i]) & (freqs < freq_bins[i + 1])
        if np.any(band):
            values.append(np.mean(mag[band]))
        else:
            values.append(0.0)
    values = np.array(values)
    
    # normalize + noise gate
    values /= np.max(values + 1e-6)
    values[values < GATE] = 0
    values *= h * SCALE_VALUE
    gain_nodes = values




stream = sd.InputStream(device=input_device,
                        samplerate=samplerate,
                        channels=2,
                        blocksize=blocksize,
                        callback=audio_callback)
stream.start()

# smoothing factor (lower = slower)
alpha = 0.15 #4
peak_gain_nodes = np.zeros

freq_bins = np.geomspace(fmin, fmax, w + 1)
freq_labels = [(freq_bins[i] + freq_bins[i+1]) / 2 for i in range(w)]

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            stream.stop(); stream.close(); sys.exit()
        elif e.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(e.size, pygame.RESIZABLE)
            pygame.event.pump()
            hwnd = pygame.display.get_wm_info()["window"]
            make_top_level_window(hwnd)
    # clear base surface    
    fade_surface.fill((0, 0, 0, 40))
    base_surface.blit(fade_surface, (0, 0))

    # exponential smoothing
    smoothed = alpha * gain_nodes + (1 - alpha) * smoothed 

    # draw gain_nodes and labels
    for x in range(w):
        height = int(smoothed[x])
        X = padding_x + x * cell_x
        for y in range(height):
            Y = total_h - padding_y_bottom - (y + 1) * cell_y
            pygame.draw.rect(base_surface, edge, (X, Y, led_w, led_h))
            pygame.draw.rect(base_surface, core, (X+1, Y+1, led_w-2, led_h-2))
        # red base
        Y_base = total_h - padding_y_bottom - cell_y
        pygame.draw.rect(base_surface, edge_red, (X, Y_base, led_w, led_h))
        pygame.draw.rect(base_surface, core_red, (X+1, Y_base+1, led_w-2, led_h-2))

        # draw vertical frequency label for every bar
        label_val = round(freq_labels[x], -1)
        label = f"{int(label_val)}"
        text_surface = font.render(label, True, label_color)
        text_surface = pygame.transform.rotate(text_surface, -90)
        text_rect = text_surface.get_rect(center=(X + led_w / 2, Y_base + led_h + 14))
        base_surface.blit(text_surface, text_rect)

    
    # after all drawing done on base_surface:
    scaled = pygame.transform.smoothscale(base_surface, screen.get_size())
    screen.blit(scaled, (0, 0))
    make_top_level_window(screen, DC_CUTTOFF)
    pygame.display.flip()
    clock.tick(30)