
class HardwareSignature:
    """Coarse hardware traits that affect DPD dynamics."""
    def __init__(self, family="superconducting", anharm=-2.0e6, base_freq=5.0e9,
                 t1=80e-6, t2=60e-6, probe_latency=30e-9):
        self.family = family
        self.anharm = anharm
        self.base_freq = base_freq
        self.t1 = t1
        self.t2 = t2
        self.probe_latency = probe_latency

    @classmethod
    def superconducting(cls):
        return cls("superconducting", anharm=-2.5e6, base_freq=5.0e9, t1=90e-6, t2=70e-6, probe_latency=30e-9)

    @classmethod
    def ion_trap(cls):
        return cls("ion_trap", anharm=-1e12, base_freq=3.0e6, t1=5.0, t2=1.0, probe_latency=200e-9)

    @classmethod
    def neutral_atom(cls):
        return cls("neutral_atom", anharm=-1e9, base_freq=1.0e6, t1=0.5, t2=0.01, probe_latency=150e-9)

    @classmethod
    def photonic(cls):
        return cls("photonic", anharm=-1e12, base_freq=2.0e14, t1=1e-3, t2=5e-4, probe_latency=5e-9)
