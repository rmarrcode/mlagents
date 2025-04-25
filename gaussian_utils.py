import numpy as np
from scipy.stats import multivariate_normal
from scipy.optimize import curve_fit

class Gaussian2D:
    """
    2D Gaussian:  f(x,y) = A * N([x,y] | mean, cov) + B
    """
    def __init__(
        self,
        mean: np.ndarray=(0.0,0.0),
        cov:  np.ndarray=None,
        amplitude: float=1.0,
        offset: float=0.0
    ):
        self.mean = np.asarray(mean, dtype=float).reshape(2,)
        if cov is None:
            cov = np.eye(2)
        self.cov = np.asarray(cov, dtype=float).reshape(2,2)
        self.amplitude = float(amplitude)
        self.offset = float(offset)
        self._rebuild_rv()

    def _rebuild_rv(self):
        self._rv = multivariate_normal(mean=self.mean, cov=self.cov)

    def pdf(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """
        Evaluate the Gaussian on the meshgrid defined by xs, ys.
        xs, ys must be 1D arrays.  Returns a (len(ys), len(xs)) array.
        """
        X, Y = np.meshgrid(xs, ys, indexing="xy")
        pts  = np.stack([X.ravel(), Y.ravel()], axis=1)
        gz   = self._rv.pdf(pts).reshape(X.shape)
        return self.amplitude * gz + self.offset

    def translate(self, dx: float, dy: float):
        """Shift the mean by (dx, dy)."""
        self.mean += np.array([dx, dy])
        self._rebuild_rv()

    def rotate(self, theta: float):
        """
        Rotate both mean and covariance by angle theta (radians)
        about the origin.
        """
        R = np.array([[np.cos(theta), -np.sin(theta)],
                      [np.sin(theta),  np.cos(theta)]])
        self.mean = R.dot(self.mean)
        self.cov  = R.dot(self.cov).dot(R.T)
        self._rebuild_rv()

    def scale(self, sx: float, sy: float):
        """
        Scale the covariance axes by (sx, sy).
        """
        S = np.diag([sx, sy])
        self.cov = S.dot(self.cov).dot(S)
        self._rebuild_rv()

    def update(
        self,
        mean:      np.ndarray=None,
        cov:       np.ndarray=None,
        amplitude: float=None,
        offset:    float=None
    ):
        """Bulk‐update parameters."""
        if mean      is not None:
            self.mean = np.asarray(mean, dtype=float).reshape(2,)
        if cov       is not None:
            self.cov  = np.asarray(cov, dtype=float).reshape(2,2)
        if amplitude is not None:
            self.amplitude = float(amplitude)
        if offset    is not None:
            self.offset    = float(offset)
        self._rebuild_rv()


def fit_gaussian_moments(
    pos2:    np.ndarray,
    weights: np.ndarray
):
    """
    Closed‐form MLE for a single 2D Gaussian given positions pos2 (N×2)
    and non‐negative weights (N,).
    Returns (mean (2,), cov (2×2)).
    """
    w = weights.clip(min=0)
    W = w.sum()
    if W <= 0:
        raise ValueError("All weights are zero or negative!")
    mu   = np.average(pos2, axis=0, weights=w)
    diff = pos2 - mu
    cov  = (diff * w[:,None]).T.dot(diff) / W
    return mu, cov


def fit_parametric_gauss2d(
    pos2: np.ndarray,
    z:    np.ndarray
) -> np.ndarray:
    """
    Fit an axis‐aligned 2D Gaussian + offset:
        f(x,y) = A * exp(-((x-x0)^2/(2 sx^2) + (y-y0)^2/(2 sy^2))) + B
    via least‐squares (curve_fit).  pos2 is (N×2), z is (N,).
    Returns popt = [A, x0, y0, sx, sy, B].
    """
    X = pos2[:,0]
    Y = pos2[:,1]
    Z = z

    def gauss2d(xy, A, x0, y0, sx, sy, B):
        x, y = xy
        return A * np.exp(
            -((x - x0)**2/(2*sx*sx) + (y - y0)**2/(2*sy*sy))
        ) + B

    p0 = [Z.max(), X.mean(), Y.mean(), 1.0, 1.0, Z.min()]
    popt, _ = curve_fit(gauss2d, (X, Y), Z, p0=p0)
    return popt