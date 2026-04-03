import numpy as np
from scipy.optimize import curve_fit

# Load data
x, y = np.loadtxt("gaussian.txt", unpack=True)

# Gaussian function
def gauss(x, A, mu, sigma, y0):
    return A * np.exp(-(x - mu)**2 / (2*sigma**2)) + y0

# Initial guesses
A0 = y.max() - y.min()
mu0 = x[np.argmax(y)]
sigma0 = (x.max() - x.min()) / 6
y00 = y.min()

p0 = [A0, mu0, sigma0, y00]

# Fit
params, _ = curve_fit(gauss, x, y, p0=p0)
A, mu, sigma, y0 = params

dx = np.mean(np.diff(x))

x_extra = np.arange(x.max() + dx, 45 + dx, dx)
y_extra = gauss(x_extra, A, mu, sigma, y0)


x_full = np.concatenate([x, x_extra])
y_full = np.concatenate([y, y_extra])


# Save as TAB-delimited
np.savetxt(
    "gaussian_extrapolated.txt",
    np.column_stack((x_full, y_full)),
    delimiter="\t"
)