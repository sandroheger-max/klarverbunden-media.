import numpy as np, sys
from scipy.io import wavfile
# Eigene, synthetisch erzeugte Musik (keine Lizenzfragen). Args: out.wav seed transpose
out, seed, tr = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rng = np.random.default_rng(seed)
SR = 44100
DUR = float(sys.argv[4]) if len(sys.argv)>4 else 12.8
t = np.arange(int(SR*DUR))/SR
def f(n): return 440*2**((n-69+tr)/12)
# I–V–vi–IV in C, je 3.2 s
progs = [[[48,55,60,64],[43,55,59,62],[45,57,60,64],[41,53,57,60]],
 [[45,57,60,64],[41,53,57,60],[48,55,60,64],[43,55,59,62]],
 [[41,53,57,60],[48,55,60,64],[43,55,59,62],[45,57,60,64]]]
chords = progs[seed % 3]
mix = np.zeros_like(t)
seg = DUR/4
for i,ch in enumerate(chords):
    s, e = int(i*seg*SR), int(min((i+1)*seg+0.6, DUR)*SR)
    tt = t[s:e]-t[s]
    env = np.minimum(1, tt/0.8) * np.exp(-np.maximum(0, tt-seg)/0.3)
    for n in ch:
        for h,a in [(1,1),(2,.25),(3,.08)]:
            mix[s:e] += a*np.sin(2*np.pi*f(n)*h*tt + rng.uniform(0,6)) * env * 0.05
# sanfte Klavier-artige Töne (Arpeggio)
step = 0.4
for k in range(int(DUR/step)):
    ch = chords[min(int(k*step/seg),3)]
    n = ch[rng.integers(1,4)] + 12
    s = int(k*step*SR); e = min(s+int(1.6*SR), len(t))
    tt = t[s:e]-t[s]
    env = np.exp(-tt*3) * np.minimum(1, tt/0.005)
    mix[s:e] += (np.sin(2*np.pi*f(n)*tt) + .3*np.sin(4*np.pi*f(n)*tt)) * env * 0.09
# Bass
for i,ch in enumerate(chords):
    s, e = int(i*seg*SR), int((i+1)*seg*SR)
    tt = t[s:e]-t[s]
    mix[s:e] += np.sin(2*np.pi*f(ch[0]-12)*tt) * np.minimum(1,tt/0.05) * np.exp(-tt*0.6) * 0.12
# Ein-/Ausblenden, normalisieren
fade = np.minimum(1, np.minimum(t/0.5, (DUR-t)/1.2))
mix *= fade
mix = mix/np.max(np.abs(mix))*0.7
wavfile.write(out, SR, (np.stack([mix,mix],1)*32767).astype(np.int16))
