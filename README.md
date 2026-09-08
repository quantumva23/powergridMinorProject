# MICROGRID STABILITY SIMULATOR

An end-to-end physics-to-cyber-physical simulation evaluating the **security and stability effect of transmission distance ($L$)** on quantum key distribution (QKD) encrypted Microgrid Control Center (MGCC) setpoint commands.

---

## 🚀 Quick Start

### 1. Launch the Interactive Web Dashboard (Streamlit)
Features interactive distance testing sliders, dual-curve distance vs security margin plots, dynamic boundary maps, and live microgrid event console:
```bash
python -m streamlit run app_streamlit.py
```

### 2. Launch the Standalone Desktop GUI (Tkinter)
Native desktop application with zero external browser dependencies:
```bash
python app_gui.py
```

### 3. Run the Distance Sensitivity Test Suite (CLI)
Executes distance sensitivity sweeps, failure limits, KPS borrowing, and saves boundary maps:
```bash
python main.py
```

### 4. Run the Automated Unit Test Suite
```bash
python test_simulation.py
```

---

## 🏗️ Architecture & Modules

| File | Component | Description |
|---|---|---|
| [`qkd_engine.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/qkd_engine.py) | **The Physics Engine** | Implements optical fiber transmittance ($\eta_{tr} = 10^{-0.2L/10}$), detection probability ($r_k$), decoy gain, QBER, Shannon entropy $h(e)$, and asymptotic secret key rate ($R_{sk}$). |
| [`grid_controller.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/grid_controller.py) | **The Grid Consumer** | Simulates an MGCC dispatching AES-256 encrypted P/Q commands ($N_{pkt} \times 256\text{ bps}$). Implements Key Pool Sharing (KPS) borrowing between Pool A and Pool B. |
| [`sensitivity_suite.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/sensitivity_suite.py) | **The Analysis Suite** | Sweeps distances ($1-100\text{ km}$) across multiple traffic frequencies, exporting boundary maps. |
| [`app_streamlit.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/app_streamlit.py) | **Web Dashboard** | **MICROGRID STABILITY SIMULATOR** Streamlit application with dedicated Distance Security Testing tab. |
| [`app_gui.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/app_gui.py) | **Desktop GUI** | Tkinter & embedded Matplotlib native desktop interface. |
| [`main.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/main.py) | **CLI Demonstrator** | Automated test harness for short, medium, critical, and long distance links. |
| [`test_simulation.py`](file:///c:/Users/Vishal%20Agrahari/powergridMinorProject/test_simulation.py) | **Unit Test Suite** | 6 automated unit tests validating physics and failure modes. |

---

## 🔬 Hardware Parameters (From Table I)

- **Bob Detector Efficiency ($\eta_{bob}$):** $0.1$ ($10\%$)
- **Dark Count Probability ($p_{dc}$):** $10^{-11}$
- **Optical Misalignment ($e_{mis}$):** $5 \times 10^{-4}$ ($0.05\%$)
- **Laser Pulse Frequency ($\nu_s$):** $40 \text{ MHz}$ ($4 \times 10^7 \text{ pulses/sec}$)
- **Block Size ($B$):** $10^7$
- **Error Correction Factor ($f_{ec}$):** $1.16$
- **Decoy State Intensities:** $\mu_1 = 0.4$ (Signal), $\mu_2 = 0.1$ (Decoy), $\mu_3 = 0.007$ (Vacuum)
- **Basis Selection Probability ($p_x$):** $0.5$

---

## 🎓 Academic Defense & Examiner Guide

### 1. Normal Case ($L = 10\text{ km}$)
- Key rate is robust (~$246\text{ kbps}$), far exceeding moderate MGCC traffic demands ($30\text{ pkts/s} \times 256\text{b} = 7.68\text{ kbps}$).
- Key pool grows steadily; status is **`[SECURE]`**.

### 2. The "Quantum Wall" ($L = 70\text{ km}$)
- Fiber attenuation ($0.2\text{ dB/km}$) reduces transmittance to $0.0398$ ($-14\text{ dB}$).
- Secret key rate drops to ~$15.7\text{ kbps}$.
- At high control frequencies ($100\text{ pkts/s} = 25.6\text{ kbps}$), key demand exceeds generation. The pool drains to zero, triggering **`[FAILED (Key Exhaustion)]`**.

### 3. Eve Intercept-Resend Attack ($e_{mis} \ge 0.10$)
- An active eavesdropper measuring qubits in random bases introduces state disturbances.
- As $e_{mis} \to 10\%$, key rate collapses by $>93\%$.
- When observed QBER crosses the **$11.0\%$ threshold**, Shannon entropy $h(e) \ge 0.5$, making $1 - 2h(e) \le 0$. Privacy amplification fails, and the system logs **`[CRITICAL] Eve Detected! QBER > 11%. Dropping Link`**.

### 4. Key Pool Sharing (KPS) Novelty (Paper 1)
- If Pool A drops below safety threshold ($< 5,000\text{ bits}$), it autonomously borrows $1,000\text{ bits}$ from backup Pool B.
- Prevents MGCC command stalling during transient deficits and rescues microgrid stability.
