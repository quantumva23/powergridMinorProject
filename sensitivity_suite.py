"""
Sensitivity Suite (The Analysis Component)
Executes multi-dimensional sweeps over fiber distances, control packet frequencies,
and eavesdropping attack levels to establish quantum-grid stability boundaries.
"""

from typing import Dict, List, Optional
import numpy as np
import matplotlib.pyplot as plt
from grid_controller import run_grid_simulation
from qkd_engine import calculate_qkd_metrics, E_MIS_DEFAULT


def run_boundary_sweep(
    distances: Optional[np.ndarray] = None,
    frequencies: Optional[List[int]] = None,
    attack_level: float = E_MIS_DEFAULT,
    time_steps: int = 100,
    enable_kps: bool = False,
) -> Dict:
    """
    Sweeps distances and packet frequencies to compute stability outcomes.
    Returns structured data for visualization.
    """
    if distances is None:
        distances = np.arange(1, 101, 5)
    if frequencies is None:
        frequencies = [10, 30, 60, 100]

    sweep_results = {}
    for freq in frequencies:
        status_list = []
        scores = []
        for d in distances:
            _, status = run_grid_simulation(
                fiber_length=d,
                attack_level=attack_level,
                data_frequency=freq,
                time_steps=time_steps,
                enable_kps=enable_kps,
            )
            is_stable = 1 if "Stable" in status else 0
            status_list.append(status)
            scores.append(is_stable)
        sweep_results[freq] = {
            "status_list": status_list,
            "scores": scores,
        }

    return {
        "distances": distances,
        "frequencies": frequencies,
        "results": sweep_results,
    }


def generate_boundary_map(
    save_path: Optional[str] = "boundary_map.png",
    show: bool = False,
    attack_level: float = E_MIS_DEFAULT,
    enable_kps: bool = False,
) -> plt.Figure:
    """
    Generates the Quantum-Grid Boundary Map: Distance vs. Control Frequency.
    """
    data = run_boundary_sweep(
        attack_level=attack_level,
        enable_kps=enable_kps,
    )
    distances = data["distances"]
    frequencies = data["frequencies"]
    results = data["results"]

    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    palette = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"]

    for idx, freq in enumerate(frequencies):
        color = palette[idx % len(palette)]
        scores = results[freq]["scores"]
        ax.plot(
            distances,
            scores,
            marker="o",
            linewidth=2.2,
            label=f"{freq} pkts/sec ({freq*256:,} bps)",
            color=color,
        )

    ax.set_xlabel("Fiber Distance L (km)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Grid Stability (1 = Secure, 0 = Failed)", fontsize=12, fontweight="bold")
    ax.set_title("Quantum-Grid Boundary Map: Distance vs. Control Frequency", fontsize=14, fontweight="bold")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Failed (Exhaustion)", "Secure (Stable)"], fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(title="MGCC Traffic", frameon=True, fontsize=10)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()

    return fig


def generate_attack_analysis(
    distance_km: float = 10.0,
    save_path: Optional[str] = "attack_sensitivity.png",
    show: bool = False,
) -> plt.Figure:
    """
    Sweeps optical misalignment / error rate e_mis from 0.0005 to 0.15
    to demonstrate Eve Intercept-Resend collapse and QBER cutoff.
    """
    e_mis_values = np.linspace(0.0005, 0.15, 60)
    key_rates = []
    qbers = []

    for e in e_mis_values:
        res = calculate_qkd_metrics(distance_km, e_mis_current=e)
        key_rates.append(res["secret_key_rate_bps"])
        qbers.append(res["qber"] * 100.0)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, dpi=100)

    # Subplot 1: Secret Key Rate
    ax1.plot(e_mis_values * 100, key_rates, color="#3b82f6", linewidth=2.5, label="Secret Key Rate (bps)")
    ax1.axvline(x=11.0, color="#ef4444", linestyle="--", linewidth=1.8, label="Eve Detection Cutoff (11%)")
    ax1.set_ylabel("Key Rate (bps)", fontsize=11, fontweight="bold")
    ax1.set_title(f"QKD Performance under Eve Optical Attack (L={distance_km} km)", fontsize=13, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()

    # Subplot 2: QBER
    ax2.plot(e_mis_values * 100, qbers, color="#f97316", linewidth=2.5, label="Observed QBER (%)")
    ax2.axhline(y=11.0, color="#ef4444", linestyle="--", linewidth=1.8, label="11% QBER Threshold")
    ax2.set_xlabel("Induced Error Rate e_mis (%)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("QBER (%)", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()

    return fig
