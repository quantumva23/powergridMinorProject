"""
MICROGRID STABILITY SIMULATOR
Main Runner for Distance Sensitivity & Cyber-Physical Stability Testing
Demonstrating the security effects of varying quantum transmission distance (L):
1. Short Link Scenario (L = 10 km, High Security Margin)
2. The "Quantum Wall" Effect (L = 70 km, Key Exhaustion)
3. Optical Misalignment Robustness (e_mis threshold)
4. Key Pool Sharing (KPS) Deficit Protection
5. Multi-Distance Stability Boundary Mapping
"""

import os
from qkd_engine import calculate_qkd_metrics, E_MIS_DEFAULT
from grid_controller import MicrogridSimulation
from sensitivity_suite import generate_boundary_map, generate_attack_analysis


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  {title.upper()}")
    print("=" * 75)


def run_demo_normal():
    print_banner("Scenario 1: Normal Operation (L = 10 km, Baseline Noise)")
    L = 10.0
    freq = 30.0  # 30 pkts/s -> 7,680 bps
    sim = MicrogridSimulation(
        fiber_length=L,
        attack_level=E_MIS_DEFAULT,
        data_frequency=freq,
        initial_pool_a=50000.0,
        enable_kps=False,
        time_steps=20,
    )
    res = sim.run()
    m = res["qkd_metrics"]

    print(f"Fiber Distance L         : {L} km")
    print(f"Channel Transmittance    : {m['transmittance']:.4f} (-2.0 dB loss)")
    print(f"Link QBER                : {m['qber']*100:.4f}% (Threshold: 11.0%)")
    print(f"Secret Key Gen Rate      : {res['key_gen_rate']:,.1f} bits/second")
    print(f"MGCC Consumption Rate    : {res['consumption_rate']:,.1f} bits/second ({freq} pkts/s * 256b)")
    print(f"Net Margin               : {res['net_rate']:+,.1f} bits/second")
    print(f"Final Grid Status        : {res['status']}")
    print(f"Initial Pool A           : {res['pool_a_history'][0]:,.0f} bits")
    print(f"Final Pool A (t=20s)     : {res['pool_a_history'][-1]:,.0f} bits")
    print("\nConsole Output:")
    for line in res["logs"][:6]:
        print(f"  {line}")


def run_demo_quantum_wall():
    print_banner("Scenario 2: The 'Quantum Wall' (L = 70 km, High Traffic Exhaustion)")
    L = 70.0
    freq = 100.0  # 100 pkts/s -> 25,600 bps
    sim = MicrogridSimulation(
        fiber_length=L,
        attack_level=E_MIS_DEFAULT,
        data_frequency=freq,
        initial_pool_a=5000.0,
        enable_kps=False,
        time_steps=20,
    )
    res = sim.run()
    m = res["qkd_metrics"]

    print(f"Fiber Distance L         : {L} km")
    print(f"Channel Transmittance    : {m['transmittance']:.6f} (-14.0 dB loss)")
    print(f"Secret Key Gen Rate      : {res['key_gen_rate']:,.1f} bits/second")
    print(f"MGCC Consumption Rate    : {res['consumption_rate']:,.1f} bits/second ({freq} pkts/s * 256b)")
    print(f"Net Deficit              : {res['net_rate']:+,.1f} bits/second")
    print(f"Final Grid Status        : {res['status']}")
    print(f"Failure Time             : t = {res['failure_time']}s")
    print("\nConsole Output:")
    for line in res["logs"][:6]:
        print(f"  {line}")


def run_demo_attack():
    print_banner("Scenario 3: Eve Intercept-Resend Attack (Misalignment e_mis = 0.12)")
    L = 10.0
    attack_e_mis = 0.12
    sim = MicrogridSimulation(
        fiber_length=L,
        attack_level=attack_e_mis,
        data_frequency=30.0,
        initial_pool_a=10000.0,
        enable_kps=False,
        time_steps=10,
    )
    res = sim.run()
    m = res["qkd_metrics"]

    print(f"Fiber Distance L         : {L} km")
    print(f"Induced Optical Error    : {attack_e_mis*100:.1f}%")
    print(f"Observed Link QBER       : {m['qber']*100:.2f}%")
    print(f"Eve Alarm Triggered?     : {m['eve_detected']} (QBER >= 11.0%)")
    print(f"Secret Key Gen Rate      : {res['key_gen_rate']:.1f} bps (Crashed to zero!)")
    print(f"Final Grid Status        : {res['status']}")
    print("\nConsole Output:")
    for line in res["logs"][:5]:
        print(f"  {line}")


def run_demo_kps():
    print_banner("Scenario 4: Key Pool Sharing (KPS) Novelty - Paper 1 Demonstration")
    L = 70.0
    # Generation at 70km is ~15,714 bps.
    # At 63 pkts/s, consumption is 63 * 256 = 16,128 bps -> Deficit of -414 bps.
    freq = 63.0
    initial_a = 5200.0
    initial_b = 30000.0

    print(f"Fiber Distance L         : {L} km")
    print(f"Traffic Demand           : {freq} pkts/s (Consumption: {freq*256:,.0f} bps)")
    print(f"Key Generation Rate      : {calculate_qkd_metrics(L)['secret_key_rate_bps']:,.1f} bps")
    print(f"Deficit per second       : {calculate_qkd_metrics(L)['secret_key_rate_bps'] - freq*256:,.1f} bps\n")

    # Case A: WITHOUT KPS
    sim_no_kps = MicrogridSimulation(
        fiber_length=L,
        data_frequency=freq,
        initial_pool_a=initial_a,
        initial_pool_b=initial_b,
        enable_kps=False,
        time_steps=20,
    )
    res_no_kps = sim_no_kps.run()
    print(f"--- [WITHOUT KPS (Standard BB84 System)] ---")
    print(f"Status                   : {res_no_kps['status']}")
    print(f"Failure Time             : t = {res_no_kps['failure_time']}s")
    print(f"Final Pool A Balance     : {res_no_kps['pool_a_history'][-1]:,.0f} bits")

    # Case B: WITH KPS
    sim_kps = MicrogridSimulation(
        fiber_length=L,
        data_frequency=freq,
        initial_pool_a=initial_a,
        initial_pool_b=initial_b,
        enable_kps=True,
        kps_threshold=5000.0,
        kps_borrow_amount=1000.0,
        time_steps=20,
    )
    res_kps = sim_kps.run()
    print(f"\n--- [WITH KPS ENABLED (Paper 1 Novel Sharing Scheme)] ---")
    print(f"Status                   : {res_kps['status']}")
    print(f"Total Borrow Events      : {res_kps['kps_borrow_count']}")
    print(f"Final Pool A Balance     : {res_kps['pool_a_history'][-1]:,.0f} bits (PROTECTED)")
    print(f"Final Pool B Balance     : {res_kps['pool_b_history'][-1]:,.0f} bits")

    print("\nConsole Output (KPS Enabled):")
    for line in res_kps["logs"][:6]:
        print(f"  {line}")


def run_generate_charts():
    print_banner("Scenario 5: Generating Publication Sensitivity & Boundary Plots")
    print("Computing Quantum-Grid Boundary Map (1-100 km across 10, 30, 60, 100 pkts/s)...")
    fig_b = generate_boundary_map(save_path="boundary_map.png")
    print("  -> Saved 'boundary_map.png'")

    print("Computing Eve Optical Attack Sensitivity Curve...")
    fig_a = generate_attack_analysis(save_path="attack_sensitivity.png")
    print("  -> Saved 'attack_sensitivity.png'")


def main():
    print("===========================================================================")
    print("  MICROGRID STABILITY SIMULATOR")
    print("  Quantum Transmission Distance & Cyber-Physical Stability Testing")
    print("===========================================================================")
    run_demo_normal()
    run_demo_quantum_wall()
    run_demo_attack()
    run_demo_kps()
    run_generate_charts()
    print("\n" + "=" * 75)
    print("  ALL DEMONSTRATION PHASES COMPLETED SUCCESSFULLY!")
    print("  Interactive Streamlit App : python -m streamlit run app_streamlit.py")
    print("  Native Desktop GUI        : python app_gui.py")
    print("=" * 75)


if __name__ == "__main__":
    main()
