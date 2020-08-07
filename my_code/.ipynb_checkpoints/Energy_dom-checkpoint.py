from icecube import dataio, dataclasses
import numpy as np
import os

f = dataio.I3File(os.path.expanduser("~/i3/data/l2_00000023.i3"))
frame = f.pop_physics()
frame = f.pop_physics()


recopulseseriesmap = frame["OfflinePulses"]
omkey = icetray.OMKey(3, 53)
recopulseseries = recopulseseriesmap[omkey]
recopulse = recopulseseries[0]

print recopulse

i3f.close()

def beta(E, m):
    return np.sqrt(1-m**2./E**2.)
E = np.logspace(-4., 3., 10001)
index = 1.32
fig = plt.figure()
for p,m in [(r"$e^-$", 0.5e-3), (r"$\mu^-$", 105e-3)]:
    plt.plot(E, 1-beta(E, m), label=p)
plt.axhline(1.-1./index, color="r", label="Speed of light in ice")
plt.fill_between([10., E.max()], 1e-9, 1e0, alpha=0.5, color="grey")
plt.loglog()
plt.legend(loc="best")
plt.xlabel(r"E / GeV")
plt.ylabel(r"$\beta$")
plt.ylim(ymin=1e-9)

from scipy.constants import alpha, pi
def cherenkov_light_per_dist(wmin, wmax):
    wmin *= 1e-9 # conversion nm -> m
    wmax *= 1e-9
    theta = np.arccos(1./index) # beta ~ 1
    return (2*pi*alpha)*np.sin(theta)**2.*((wmin**(-1))-(wmax**(-1)))

wavelengths = np.linspace(200., 800, 61)
yields = np.array([cherenkov_light_per_dist(wmin, wmax) for wmin, wmax in zip(wavelengths[:-1], wavelengths[1:])])
plt.step(wavelengths[:-1], yields*1e-2, color="k")
plt.xlabel("Wavelength / nm")
plt.ylabel("Number of photons per 10nm per cm")
plt.axvline(300, color="r")
plt.axvline(650, color="r")
plt.title("Photons per cm in sensitive range %.1f" %(cherenkov_light_per_dist(300, 650)*1e-2,))
