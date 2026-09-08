"""
Desktop GUI for QKD Microgrid Stability Simulation
Built using native Python Tkinter and Matplotlib.
Zero-dependency, standalone desktop application.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from qkd_engine import calculate_qkd_metrics, E_MIS_DEFAULT
from grid_controller import MicrogridSimulation
from sensitivity_suite import run_boundary_sweep


class QKDMicrogridApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MICROGRID STABILITY SIMULATOR")
        self.geometry("1200x820")
        self.configure(bg="#0f172a")

        # Configure style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#0f172a")
        self.style.configure("TLabelframe", background="#1e293b", foreground="#f8fafc", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe.Label", background="#1e293b", foreground="#38bdf8")
        self.style.configure("TLabel", background="#1e293b", foreground="#f1f5f9", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background="#0284c7", foreground="#ffffff")
        self.style.map("TButton", background=[("active", "#0369a1")])

        self.create_layout()
        self.run_simulation()

    def create_layout(self):
        # Top Header
        header = tk.Frame(self, bg="#0284c7", height=55)
        header.pack(fill=tk.X, side=tk.TOP)
        title_lbl = tk.Label(
            header,
            text="⚡ MICROGRID STABILITY SIMULATOR - Transmission Distance Testing",
            font=("Segoe UI", 14, "bold"),
            bg="#0284c7",
            fg="#ffffff",
        )
        title_lbl.pack(pady=10)

        # Main container with left panel (controls) and right panel (charts & console)
        main_pane = tk.Frame(self, bg="#0f172a")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Left Control Panel
        left_frame = tk.Frame(main_pane, bg="#0f172a", width=340)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Parameters Box
        param_box = ttk.LabelFrame(left_frame, text=" Distance & Load Testing Controls ", padding=12)
        param_box.pack(fill=tk.X, pady=(0, 10))

        # Distance Slider (Primary testing variable)
        ttk.Label(param_box, text="Transmission Distance L (km):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.var_dist = tk.DoubleVar(value=15.0)
        self.lbl_dist = ttk.Label(param_box, text="15.0 km", font=("Segoe UI", 10, "bold"), foreground="#38bdf8")
        self.lbl_dist.pack(anchor=tk.E)
        s_dist = ttk.Scale(param_box, from_=1.0, to=100.0, variable=self.var_dist, command=lambda v: self.lbl_dist.config(text=f"{float(v):.1f} km"))
        s_dist.pack(fill=tk.X, pady=(0, 8))

        # Packet Frequency Slider
        ttk.Label(param_box, text="MGCC Command Traffic (pkts/sec):").pack(anchor=tk.W)
        self.var_freq = tk.DoubleVar(value=30.0)
        self.lbl_freq = ttk.Label(param_box, text="30 pkts/s", font=("Segoe UI", 9, "bold"))
        self.lbl_freq.pack(anchor=tk.E)
        s_freq = ttk.Scale(param_box, from_=5.0, to=120.0, variable=self.var_freq, command=lambda v: self.lbl_freq.config(text=f"{float(v):.0f} pkts/s"))
        s_freq.pack(fill=tk.X, pady=(0, 8))

        # KPS Checkbox
        self.var_kps = tk.BooleanVar(value=True)
        cb_kps = tk.Checkbutton(
            param_box,
            text="Enable Key Pool Sharing (KPS)",
            variable=self.var_kps,
            bg="#1e293b",
            fg="#38bdf8",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#38bdf8",
            font=("Segoe UI", 9, "bold"),
        )
        cb_kps.pack(anchor=tk.W, pady=6)

        # Run Button
        btn_run = ttk.Button(param_box, text="▶  Run Distance Test", command=self.run_simulation)
        btn_run.pack(fill=tk.X, pady=8)

        # Quick Distance Testing Presets
        preset_box = ttk.LabelFrame(left_frame, text=" Distance Testing Presets ", padding=10)
        preset_box.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(preset_box, text="1. Short Link (10 km)", command=lambda: self.load_preset(10.0, 30.0, True)).pack(fill=tk.X, pady=3)
        ttk.Button(preset_box, text="2. Medium Link (40 km)", command=lambda: self.load_preset(40.0, 30.0, True)).pack(fill=tk.X, pady=3)
        ttk.Button(preset_box, text="3. Critical Limit (55 km)", command=lambda: self.load_preset(55.0, 60.0, True)).pack(fill=tk.X, pady=3)
        ttk.Button(preset_box, text="4. Long Link (70 km - Exhaustion)", command=lambda: self.load_preset(70.0, 100.0, False)).pack(fill=tk.X, pady=3)

        # KPI Summary Box
        self.kpi_box = ttk.LabelFrame(left_frame, text=" Security & Stability Telemetry ", padding=10)
        self.kpi_box.pack(fill=tk.X)
        self.lbl_kpi_dist = ttk.Label(self.kpi_box, text="Distance: --")
        self.lbl_kpi_dist.pack(anchor=tk.W, pady=2)
        self.lbl_kpi_rate = ttk.Label(self.kpi_box, text="Key Gen Rate: --")
        self.lbl_kpi_rate.pack(anchor=tk.W, pady=2)
        self.lbl_kpi_cons = ttk.Label(self.kpi_box, text="Consumption: --")
        self.lbl_kpi_cons.pack(anchor=tk.W, pady=2)
        self.lbl_kpi_margin = ttk.Label(self.kpi_box, text="Security Margin: --")
        self.lbl_kpi_margin.pack(anchor=tk.W, pady=2)
        self.lbl_kpi_status = ttk.Label(self.kpi_box, text="Status: --", font=("Segoe UI", 10, "bold"))
        self.lbl_kpi_status.pack(anchor=tk.W, pady=4)

        # Right Panel: Plot Canvas and Console
        right_frame = tk.Frame(main_pane, bg="#0f172a")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Plot Frame
        plot_frame = tk.Frame(right_frame, bg="#1e293b", bd=1, relief=tk.SOLID)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.fig, self.ax = plt.subplots(figsize=(7, 3.8), dpi=100)
        self.fig.patch.set_facecolor("#1e293b")
        self.ax.set_facecolor("#0f172a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Console Frame
        console_frame = ttk.LabelFrame(right_frame, text=" Microgrid Security Console ", padding=6)
        console_frame.pack(fill=tk.X)

        self.console_txt = scrolledtext.ScrolledText(
            console_frame,
            height=8,
            bg="#0b0f19",
            fg="#e2e8f0",
            font=("Consolas", 9),
            insertbackground="white",
        )
        self.console_txt.pack(fill=tk.BOTH, expand=True)
        self.console_txt.tag_config("SECURE", foreground="#34d399")
        self.console_txt.tag_config("CRITICAL", foreground="#f43f5e")
        self.console_txt.tag_config("FAILED", foreground="#ef4444")
        self.console_txt.tag_config("KPS", foreground="#fbbf24")
        self.console_txt.tag_config("INFO", foreground="#38bdf8")

    def load_preset(self, d, f, kps):
        self.var_dist.set(d)
        self.lbl_dist.config(text=f"{d:.1f} km")
        self.var_freq.set(f)
        self.lbl_freq.config(text=f"{f:.0f} pkts/s")
        self.var_kps.set(kps)
        self.run_simulation()

    def run_simulation(self):
        d = self.var_dist.get()
        f = self.var_freq.get()
        kps = self.var_kps.get()

        init_a = 5200.0 if (d >= 65 and f > 60 and kps) else 25000.0
        sim = MicrogridSimulation(
            fiber_length=d,
            attack_level=E_MIS_DEFAULT,
            data_frequency=f,
            initial_pool_a=init_a,
            initial_pool_b=40000.0,
            enable_kps=kps,
            kps_threshold=5000.0,
            kps_borrow_amount=1000.0,
            time_steps=80,
        )
        res = sim.run()
        qkd = res["qkd_metrics"]

        # Update KPIs
        self.lbl_kpi_dist.config(text=f"Distance L: {d:.1f} km (-{0.2*d:.1f} dB)")
        self.lbl_kpi_rate.config(text=f"Key Gen Rate: {res['key_gen_rate']:,.1f} bps")
        self.lbl_kpi_cons.config(text=f"Consumption: {res['consumption_rate']:,.1f} bps")
        margin_color = "#34d399" if res['net_rate'] >= 0 else "#ef4444"
        self.lbl_kpi_margin.config(text=f"Security Margin: {res['net_rate']:+,.1f} bps")

        status_text = res["status"]
        if "Stable" in status_text:
            self.lbl_kpi_status.config(text=f"Status: {status_text}", foreground="#34d399")
        else:
            self.lbl_kpi_status.config(text=f"Status: {status_text}", foreground="#ef4444")

        # Update Matplotlib Plot
        self.ax.clear()
        self.ax.set_facecolor("#0f172a")
        t_axis = list(range(len(res["pool_a_history"])))
        self.ax.plot(t_axis, res["pool_a_history"], label="Pool A (MGCC)", color="#10b981", linewidth=2.2)
        if kps:
            self.ax.plot(t_axis, res["pool_b_history"], label="Pool B (Reserve)", color="#38bdf8", linestyle="--")
            self.ax.axhline(y=5000.0, color="#fbbf24", linestyle=":", label="5k Threshold")

        if res["failure_time"] is not None:
            self.ax.axvline(x=res["failure_time"], color="#ef4444", linestyle="-.", label="Failure")

        self.ax.set_title(f"Dynamic Key Pool (L={d:.1f}km, Traffic={f:.0f}pkts/s)", color="#f8fafc", fontsize=11, fontweight="bold")
        self.ax.set_xlabel("Time (s)", color="#94a3b8")
        self.ax.set_ylabel("Key Balance (bits)", color="#94a3b8")
        self.ax.tick_params(colors="#94a3b8")
        for spine in self.ax.spines.values():
            spine.set_color("#334155")
        self.ax.grid(True, linestyle="--", alpha=0.3, color="#475569")
        self.ax.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#f8fafc", loc="upper right")
        self.fig.tight_layout()
        self.canvas.draw()

        # Update Console Text
        self.console_txt.delete("1.0", tk.END)
        for line in res["logs"]:
            tag = "INFO"
            if "[CRITICAL]" in line:
                tag = "CRITICAL"
            elif "[FAILED]" in line:
                tag = "FAILED"
            elif "[KPS BORROW]" in line:
                tag = "KPS"
            elif "[SECURE]" in line:
                tag = "SECURE"
            self.console_txt.insert(tk.END, line + "\n", tag)
        self.console_txt.see(tk.END)


if __name__ == "__main__":
    app = QKDMicrogridApp()
    app.mainloop()
