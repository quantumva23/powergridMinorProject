"""
MICROGRID STABILITY SIMULATOR
Physics-to-Cyber-Physical Security Modeling of Quantum Key Distribution & MGCC Command Encryption
Focus: Security and Stability Effect of Transmission Distance (L)
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from qkd_engine import calculate_qkd_metrics, E_MIS_DEFAULT
from grid_controller import MicrogridSimulation
from sensitivity_suite import run_boundary_sweep

# Page Configuration
st.set_page_config(
    page_title="MICROGRID STABILITY SIMULATOR",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main {
        background-color: #0b0f19;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 14px;
    }
    .terminal-container {
        background-color: #030712;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 16px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.88rem;
        max-height: 420px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar Controls - Cleaned of irrelevant knobs, focused on Distance and Grid Load
st.sidebar.title("⚡ Simulation Controls")
st.sidebar.markdown("---")

st.sidebar.subheader("📍 Primary Variable Under Test")
distance = st.sidebar.slider(
    "Transmission Distance L (km)",
    min_value=1.0,
    max_value=100.0,
    value=15.0,
    step=1.0,
    help="Primary testing parameter: Distance between Quantum Transmitter (QKD Alice) and Microgrid Substation (Bob)",
)

st.sidebar.subheader("🔌 Microgrid Dispatch Load")
freq = st.sidebar.slider(
    "P/Q Command Traffic (pkts/sec)",
    min_value=5,
    max_value=120,
    value=30,
    step=5,
    help="Packet generation frequency for active/reactive power dispatch commands.",
)
bits_per_packet = 256  # Fixed AES-256 encryption standard
time_steps = st.sidebar.slider("Simulation Time (seconds)", min_value=20, max_value=200, value=100, step=10)

st.sidebar.subheader("🔄 Key Pool Sharing (KPS)")
enable_kps = st.sidebar.checkbox("Enable KPS Buffer", value=True, help="Enables dynamic key borrowing between Pool A and Reserve Pool B")
col_p1, col_p2 = st.sidebar.columns(2)
with col_p1:
    init_pool_a = st.number_input("Pool A (bits)", min_value=1000, max_value=100000, value=25000, step=5000)
    kps_threshold = st.number_input("Threshold (bits)", min_value=500, max_value=10000, value=5000, step=500)
with col_p2:
    init_pool_b = st.number_input("Pool B (bits)", min_value=1000, max_value=100000, value=40000, step=5000)
    kps_borrow = st.number_input("Borrow (bits)", min_value=200, max_value=5000, value=1000, step=200)

# Quick Distance Testing Presets
st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Quick Distance Test Cases")
c1, c2 = st.sidebar.columns(2)
if c1.button("Short Link (10 km)"):
    distance = 10.0
if c2.button("Medium Link (40 km)"):
    distance = 40.0
c3, c4 = st.sidebar.columns(2)
if c3.button("Critical Link (55 km)"):
    distance = 55.0
if c4.button("Long Link (70 km)"):
    distance = 70.0

# Run Simulation
sim = MicrogridSimulation(
    fiber_length=distance,
    attack_level=E_MIS_DEFAULT,
    data_frequency=freq,
    initial_pool_a=init_pool_a,
    initial_pool_b=init_pool_b,
    bits_per_packet=bits_per_packet,
    time_steps=time_steps,
    enable_kps=enable_kps,
    kps_threshold=kps_threshold,
    kps_borrow_amount=kps_borrow,
)
results = sim.run()
qkd = results["qkd_metrics"]

# Calculate Critical Distance for Current Traffic
# Consumption rate = freq * 256
consumption_rate = freq * bits_per_packet
dist_range = np.linspace(1.0, 100.0, 300)
gen_rates_sweep = [calculate_qkd_metrics(d)["secret_key_rate_bps"] for d in dist_range]
crit_idx = np.where(np.array(gen_rates_sweep) < consumption_rate)[0]
crit_distance = dist_range[crit_idx[0]] if len(crit_idx) > 0 else 100.0

# App Header
st.title("⚡ MICROGRID STABILITY SIMULATOR")
st.markdown(
    f"**Testing Impact of Quantum Transmission Distance on Microgrid Cyber-Physical Stability** | "
    f"Tested Distance: **{distance:.1f} km** | Traffic Demand: **{freq} pkts/s ({consumption_rate:,.0f} bps)**"
)

# Live Status Banner
status_str = results["status"]
if "Stable" in status_str:
    st.success(f"✅ SYSTEM SECURE & STABLE | Status: {status_str} | Key generation exceeds command consumption.")
else:
    st.error(f"❌ GRID CONTROLLER COLLAPSE | Status: {status_str} | Key Pool exhausted at t={results['failure_time']}s due to fiber loss.")

# Real-Time Telemetry KPI Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Tested Distance", f"{distance:.1f} km", delta=f"Transmittance: {qkd['transmittance']*100:.2f}%")
with kpi2:
    st.metric("Key Generation Rate", f"{results['key_gen_rate']:,.1f} bps", delta=f"-0.2 dB/km fiber loss")
with kpi3:
    st.metric("MGCC Consumption", f"{results['consumption_rate']:,.1f} bps", delta=f"{freq} pkts/s * 256b")
with kpi4:
    st.metric(
        "Security Margin",
        f"{results['net_rate']:+,.1f} bps",
        delta="Positive (Surplus)" if results['net_rate'] >= 0 else "Negative (Deficit)",
        delta_color="normal" if results['net_rate'] >= 0 else "inverse",
    )
with kpi5:
    st.metric("Critical Limit (L_crit)", f"{crit_distance:.1f} km", delta="Max Sustainable Dist")

st.markdown("---")

# Main Testing Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Distance Security Testing (My Testing)",
    "📈 Dynamic Key Pool Evolution",
    "🗺️ Distance vs. Traffic Boundary Map",
    "💻 Microgrid Security Console",
])

# Tab 1: Distance Security Testing (User's Primary Focus)
with tab1:
    st.subheader("🔬 Distance Sensitivity & Security Boundary Analysis")
    st.caption(
        "Evaluation of how increasing transmission distance degrades quantum key rates, "
        "erodes the security margin, and leads to microgrid command stalling."
    )

    fig_test, (ax_t1, ax_t2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True, dpi=120)
    plt.style.use("dark_background")

    # Plot 1: Key Generation vs Consumption Line
    ax_t1.plot(dist_range, gen_rates_sweep, color="#38bdf8", linewidth=2.8, label="QKD Secret Key Rate (bps)")
    ax_t1.axhline(y=consumption_rate, color="#f59e0b", linestyle="--", linewidth=2, label=f"Grid Demand ({consumption_rate:,.0f} bps)")
    
    # Mark Critical Distance
    ax_t1.axvline(x=crit_distance, color="#ef4444", linestyle=":", linewidth=2, label=f"Critical Distance Limit ({crit_distance:.1f} km)")
    
    # Highlight current operating point
    ax_t1.plot(
        [distance],
        [results["key_gen_rate"]],
        marker="o",
        markersize=10,
        color="#10b981" if results["net_rate"] >= 0 else "#ef4444",
        label=f"Current Test Point ({distance:.1f} km, {results['key_gen_rate']:,.0f} bps)",
    )

    ax_t1.set_ylabel("Key Rate (bps)", fontsize=11, fontweight="bold")
    ax_t1.set_title(f"Impact of Distance (L) on Key Generation vs Grid Consumption Demand", fontsize=12, fontweight="bold")
    ax_t1.grid(True, linestyle="--", alpha=0.3)
    ax_t1.legend(loc="upper right", framealpha=0.8)

    # Plot 2: Net Security Margin (Surplus vs Deficit)
    net_margins = np.array(gen_rates_sweep) - consumption_rate
    ax_t2.plot(dist_range, net_margins, color="#a855f7", linewidth=2.5, label="Net Security Margin (Gen - Demand)")
    ax_t2.axhline(y=0, color="#ffffff", linestyle="-", linewidth=1.2, alpha=0.6)
    
    # Shade Secure vs Exhaustion zones
    ax_t2.fill_between(dist_range, 0, net_margins, where=(net_margins >= 0), color="#10b981", alpha=0.25, label="Secure Stability Zone")
    ax_t2.fill_between(dist_range, 0, net_margins, where=(net_margins < 0), color="#ef4444", alpha=0.25, label="Deficit / Exhaustion Zone")
    
    # Mark current test point on margin curve
    ax_t2.plot(
        [distance],
        [results["net_rate"]],
        marker="X",
        markersize=10,
        color="#facc15",
        label=f"Current Margin ({results['net_rate']:+,.0f} bps)",
    )

    ax_t2.set_xlabel("Transmission Distance L (km)", fontsize=11, fontweight="bold")
    ax_t2.set_ylabel("Security Margin (bps)", fontsize=11, fontweight="bold")
    ax_t2.grid(True, linestyle="--", alpha=0.3)
    ax_t2.legend(loc="upper right", framealpha=0.8)

    fig_test.tight_layout()
    st.pyplot(fig_test)

    # Summary Insights Box for My Testing
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.info(
            f"**1. Fiber Attenuation Effect:**\n\n"
            f"At **{distance:.1f} km**, optical transmittance is **{qkd['transmittance']*100:.2f}%** "
            f"(-{(0.2 * distance):.1f} dB optical power loss). Key generation is **{results['key_gen_rate']:,.1f} bps**."
        )
    with col_t2:
        if distance <= crit_distance:
            st.success(
                f"**2. Security Assessment:**\n\n"
                f"Tested distance **{distance:.1f} km** is within the sustainable zone (< {crit_distance:.1f} km). "
                f"Security margin is **{results['net_rate']:+,.1f} bps**, guaranteeing stable MGCC operation."
            )
        else:
            st.error(
                f"**2. Security Assessment:**\n\n"
                f"Tested distance **{distance:.1f} km** exceeds critical limit of **{crit_distance:.1f} km**. "
                f"Net deficit is **{results['net_rate']:+,.1f} bps**, causing key pool exhaustion."
            )
    with col_t3:
        st.warning(
            f"**3. Engineering Finding:**\n\n"
            f"For MGCC dispatch at **{freq} pkts/s**, maximum distance must not exceed **{crit_distance:.1f} km**. "
            f"Beyond this boundary, QKD key production cannot replenish consumed AES-256 tokens."
        )

# Tab 2: Dynamic Pool Evolution Over Time
with tab2:
    st.subheader("Key Pool Dynamics Over Time")
    st.caption("Tracks real-time key pool balance under the tested distance and traffic conditions.")

    fig_pool, ax_p = plt.subplots(figsize=(10, 4.8), dpi=120)
    plt.style.use("dark_background")

    time_axis = list(range(len(results["pool_a_history"])))
    ax_p.plot(time_axis, results["pool_a_history"], label="Primary Key Pool A", color="#10b981", linewidth=2.5)

    if enable_kps:
        ax_p.plot(time_axis, results["pool_b_history"], label="Reserve Key Pool B", color="#38bdf8", linewidth=2, linestyle="--")
        ax_p.axhline(y=kps_threshold, color="#f59e0b", linestyle=":", label=f"KPS Threshold ({kps_threshold:,.0f}b)")

    if results["failure_time"] is not None:
        ax_p.axvline(x=results["failure_time"], color="#ef4444", linestyle="-.", linewidth=2, label=f"Exhaustion Time (t={results['failure_time']}s)")

    ax_p.set_xlabel("Time (seconds)", fontsize=11)
    ax_p.set_ylabel("Key Balance (bits)", fontsize=11)
    ax_p.set_title(f"Key Pool Balance History (L = {distance:.1f} km | Traffic = {freq} pkts/s)", fontsize=12, fontweight="bold")
    ax_p.grid(True, linestyle="--", alpha=0.3)
    ax_p.legend(loc="upper right", framealpha=0.7)
    fig_pool.tight_layout()
    st.pyplot(fig_pool)

# Tab 3: Distance vs Traffic Boundary Map
with tab3:
    st.subheader("Quantum-Grid Boundary Map: Distance vs. Traffic Demand")
    st.caption("Boundary curves showing the stability envelope across multiple traffic levels (10 to 100 pkts/s).")

    if st.button("🔄 Recompute Boundary Sweep"):
        with st.spinner("Computing multi-distance sweep..."):
            st.session_state["cached_boundary"] = run_boundary_sweep(enable_kps=enable_kps)

    if "cached_boundary" not in st.session_state:
        st.session_state["cached_boundary"] = run_boundary_sweep(enable_kps=enable_kps)

    b_data = st.session_state["cached_boundary"]
    fig_b, ax_b = plt.subplots(figsize=(10, 5), dpi=120)
    plt.style.use("dark_background")
    palette = ["#34d399", "#60a5fa", "#fbbf24", "#f87171"]

    for idx, f_val in enumerate(b_data["frequencies"]):
        ax_b.plot(
            b_data["distances"],
            b_data["results"][f_val]["scores"],
            marker="o",
            markersize=4,
            linewidth=2.2,
            label=f"{f_val} pkts/s ({f_val*256:,} bps)",
            color=palette[idx % len(palette)],
        )

    # Plot current test point
    curr_score = 1 if "Stable" in results["status"] else 0
    ax_b.plot([distance], [curr_score], marker="*", markersize=14, color="#e11d48", label=f"Current Test ({distance}km, {freq}pkts/s)")

    ax_b.set_xlabel("Transmission Distance L (km)", fontsize=11, fontweight="bold")
    ax_b.set_ylabel("Stability State", fontsize=11, fontweight="bold")
    ax_b.set_yticks([0, 1])
    ax_b.set_yticklabels(["Failed (0)", "Stable (1)"], fontsize=10)
    ax_b.set_title("Operational Stability Boundary (Distance vs Frequency)", fontsize=12, fontweight="bold")
    ax_b.grid(True, linestyle="--", alpha=0.3)
    ax_b.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    fig_b.tight_layout()
    st.pyplot(fig_b)

# Tab 4: Microgrid Security Console
with tab4:
    st.subheader("💻 Microgrid Security Console")
    st.caption("Live event stream logging key consumption, threshold triggers, and KPS buffer transfers.")

    console_markup = "<div class='terminal-container'>"
    for log in results["logs"]:
        if "[FAILED]" in log or "[CRITICAL]" in log:
            col = "#ef4444"
        elif "[KPS BORROW]" in log:
            col = "#fbbf24"
        elif "[SECURE]" in log:
            col = "#34d399"
        else:
            col = "#38bdf8"
        console_markup += f"<div style='color: {col}; margin-bottom: 4px;'>{log}</div>"
    console_markup += "</div>"

    st.markdown(console_markup, unsafe_allow_html=True)

st.markdown("---")
st.caption("MICROGRID STABILITY SIMULATOR | Distance Sensitivity & QKD Security Analysis")
