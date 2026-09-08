"""
QKD Engine (The Physics Component)
Implements quantum channel transmittance, detection probability, decoy-state gain,
quantum bit error rate (QBER), and asymptotic secret key rate calculations.
Based on Table I hardware parameters and BB84/decoy-state protocols.
"""

import numpy as np

# Hardware Parameters (From Table I)
ETA_BOB_DEFAULT = 0.1      # Bob's receiver detection efficiency
PDC_DEFAULT = 1e-11        # Dark count probability per pulse
E_MIS_DEFAULT = 5e-4       # Intrinsic optical misalignment error rate
VS_DEFAULT = 4e7           # Repetition rate: Laser pulse frequency (40 MHz)
B_DEFAULT = 10**7          # Post-processing block size
F_EC_DEFAULT = 1.16        # Error correction efficiency factor

# Decoy State Parameters
K1_SIGNAL = 0.4            # Signal state intensity
K2_DECOY = 0.1             # Weak decoy state intensity
K3_VACUUM = 0.007          # Vacuum state intensity
PX_DEFAULT = 0.5           # Probability of selecting X-basis


def calculate_transmittance(fiber_length_km: float, attenuation_db_per_km: float = 0.2) -> float:
    """
    Computes optical fiber transmittance eta_tr given distance L in km.
    Standard single-mode telecom fiber attenuation is 0.2 dB/km at 1550 nm.
    """
    return 10.0 ** (-attenuation_db_per_km * fiber_length_km / 10.0)


def calculate_qkd_metrics(
    fiber_length_km: float,
    e_mis_current: float = E_MIS_DEFAULT,
    eta_bob: float = ETA_BOB_DEFAULT,
    pdc: float = PDC_DEFAULT,
    vs: float = VS_DEFAULT,
    px: float = PX_DEFAULT,
    k1: float = K1_SIGNAL,
    f_ec: float = F_EC_DEFAULT,
    qber_threshold: float = 0.11,
) -> dict:
    """
    Calculates detailed QKD physics parameters:
    - Transmittance (eta_tr)
    - Detection rate (r_k)
    - Signal gain
    - Overall Quantum Bit Error Rate (QBER)
    - Binary Shannon Entropy h(e)
    - Secret Key Rate (bits/second)
    - Security Status (Eve threshold check)
    """
    L = max(0.0, float(fiber_length_km))
    e_mis = max(0.0, float(e_mis_current))

    # Eq 6: Optical channel transmittance based on distance L (km)
    eta_tr = calculate_transmittance(L)

    # Eq 5: Expected detection rate at Bob's side
    # r_k = 1 - (1 - 2*pdc) * exp(-eta_tr * eta_bob * k1)
    r_k = 1.0 - (1.0 - 2.0 * pdc) * np.exp(-eta_tr * eta_bob * k1)

    # Eq 15: Gain in X basis
    gain = r_k * (px ** 2)

    # Effective error rate (QBER) = optical misalignment + dark count noise
    if gain > 0:
        error_rate = e_mis + (pdc / gain)
    else:
        error_rate = 0.5

    # Binary Shannon Entropy h(e) for privacy amplification
    if error_rate <= 0.0:
        h_e = 0.0
    elif error_rate >= 0.5:
        h_e = 1.0
    else:
        h_e = -error_rate * np.log2(error_rate) - (1.0 - error_rate) * np.log2(1.0 - error_rate)

    # Secret Key Rate calculation (bits per second)
    # R_sk = vs * gain * [1 - 2 * h(e)]
    eve_detected = (error_rate >= qber_threshold)

    if eve_detected or (1.0 - 2.0 * h_e) <= 0:
        secret_key_rate = 0.0
    else:
        secret_key_rate = vs * gain * (1.0 - 2.0 * h_e)
        secret_key_rate = max(0.0, float(secret_key_rate))

    return {
        "distance_km": L,
        "transmittance": float(eta_tr),
        "detection_rate": float(r_k),
        "gain": float(gain),
        "qber": float(error_rate),
        "entropy_h_e": float(h_e),
        "secret_key_rate_bps": float(secret_key_rate),
        "eve_detected": eve_detected,
        "qber_threshold": float(qber_threshold),
    }


def calculate_key_rate(L: float, e_mis_current: float = E_MIS_DEFAULT) -> float:
    """
    Standard interface matching project specification.
    Returns secret key rate in bits per second.
    """
    metrics = calculate_qkd_metrics(L, e_mis_current)
    return metrics["secret_key_rate_bps"]
