
class ScalarKalman:
    """Scalar KF for a single parameter (e.g., detuning estimate in Hz)."""
    def __init__(self, x0=0.0, p0=1e12, q=1e7, r=1e6):
        self.x = float(x0)
        self.p = float(p0)
        self.q = float(q)
        self.r = float(r)

    def predict(self):
        self.p = self.p + self.q
        return self.x

    def update(self, z, H=1.0):
        s = H*self.p*H + self.r
        k = self.p*H/s
        y = z - H*self.x
        self.x = self.x + k*y
        self.p = (1 - k*H)*self.p
        return self.x, self.p, k, y
