"""
Grid Controller (The Consumer & Key Pool Manager)
Simulates a Microgrid Control Center (MGCC) dispatching active/reactive (P/Q) power
commands to distributed energy resources (DERs) encrypted using AES-256 keys.
Includes the novel Key Pool Sharing (KPS) mechanism between Pool A and Pool B.
"""

from typing import Dict, List, Tuple, Optional
from qkd_engine import calculate_qkd_metrics, E_MIS_DEFAULT


class MicrogridSimulation:
    def __init__(
        self,
        fiber_length: float,
        attack_level: float = E_MIS_DEFAULT,
        data_frequency: float = 30.0,
        initial_pool_a: float = 50000.0,
        initial_pool_b: float = 50000.0,
        bits_per_packet: int = 256,
        time_steps: int = 100,
        enable_kps: bool = True,
        kps_threshold: float = 5000.0,
        kps_borrow_amount: float = 1000.0,
    ):
        self.fiber_length = float(fiber_length)
        self.attack_level = float(attack_level)
        self.data_frequency = float(data_frequency)
        self.initial_pool_a = float(initial_pool_a)
        self.initial_pool_b = float(initial_pool_b)
        self.bits_per_packet = bits_per_packet
        self.time_steps = int(time_steps)
        self.enable_kps = enable_kps
        self.kps_threshold = kps_threshold
        self.kps_borrow_amount = kps_borrow_amount

        # Calculate physics metrics
        self.qkd_metrics = calculate_qkd_metrics(self.fiber_length, self.attack_level)
        self.key_gen_rate = self.qkd_metrics["secret_key_rate_bps"]
        self.consumption_rate = self.data_frequency * self.bits_per_packet

    def run(self) -> Dict:
        """
        Executes the time-step microgrid simulation.
        Returns a dictionary containing full time series, status, and console logs.
        """
        pool_a = self.initial_pool_a
        pool_b = self.initial_pool_b

        pool_a_history = []
        pool_b_history = []
        logs = []
        borrow_events = []
        status = "Stable"
        failure_time: Optional[int] = None

        # Check for immediate Eve intercept-resend attack
        if self.qkd_metrics["eve_detected"]:
            status = "CRITICAL (Eve Detected)"
            logs.append(
                f"[CRITICAL] Eve Detected! QBER = {self.qkd_metrics['qber']*100:.2f}% "
                f"> 11.0% limit. Quantum link dropped! Secret key generation halted."
            )
        else:
            logs.append(
                f"[INIT] Link established: L={self.fiber_length:.1f} km | "
                f"Key Gen: {self.key_gen_rate:.1f} bps | "
                f"Consumption: {self.consumption_rate:.1f} bps ({self.data_frequency} pkts/s * {self.bits_per_packet}b)"
            )

        kps_borrow_count = 0

        for t in range(self.time_steps):
            # QKD key generation influx
            pool_a += self.key_gen_rate

            # P/Q control command encryption key consumption
            pool_a -= self.consumption_rate

            # KPS: Key Pool Sharing Novelty Feature
            # If Pool A falls below safety threshold, borrow from secondary Pool B
            if self.enable_kps and (pool_a < self.kps_threshold) and (pool_b > 0):
                borrow_qty = min(self.kps_borrow_amount, pool_b)
                pool_a += borrow_qty
                pool_b -= borrow_qty
                kps_borrow_count += 1
                borrow_events.append((t, pool_a, pool_b, borrow_qty))
                logs.append(
                    f"[KPS BORROW] t={t:03d}s | Pool A ({max(0.0, pool_a - borrow_qty):,.0f}b) < {self.kps_threshold:,.0f}b threshold! "
                    f"Borrowed {borrow_qty:,.0f}b from Pool B (Pool B remaining: {pool_b:,.0f}b). New Pool A: {max(0.0, pool_a):,.0f}b"
                )

            # Check for Key Exhaustion
            if pool_a <= 0:
                pool_a = 0.0
                status = "FAILED (Key Exhaustion)"
                if failure_time is None:
                    failure_time = t
                    logs.append(
                        f"[FAILED] t={t:03d}s | Key Exhaustion! Pool A reached 0 bits. "
                        f"MGCC P/Q commands stalled! Microgrid stability lost."
                    )
            else:
                # Log periodic status
                if t % 10 == 0 and t > 0:
                    status_tag = "[SECURE]" if not self.qkd_metrics["eve_detected"] else "[DEGRADED]"
                    logs.append(
                        f"{status_tag} t={t:03d}s | Pool A: {pool_a:,.0f} bits | "
                        f"Pool B: {pool_b:,.0f} bits | Delta: {self.key_gen_rate - self.consumption_rate:+,.1f} bps"
                    )

            pool_a_history.append(pool_a)
            pool_b_history.append(pool_b)

        if status == "Stable" and kps_borrow_count > 0:
            status = "Stable (KPS Rescued)"

        return {
            "status": status,
            "failure_time": failure_time,
            "pool_a_history": pool_a_history,
            "pool_b_history": pool_b_history,
            "logs": logs,
            "borrow_events": borrow_events,
            "kps_borrow_count": kps_borrow_count,
            "key_gen_rate": self.key_gen_rate,
            "consumption_rate": self.consumption_rate,
            "net_rate": self.key_gen_rate - self.consumption_rate,
            "qkd_metrics": self.qkd_metrics,
            "time_steps": self.time_steps,
        }


def run_grid_simulation(
    fiber_length: float,
    attack_level: float = E_MIS_DEFAULT,
    data_frequency: float = 30.0,
    time_steps: int = 100,
    enable_kps: bool = False,
) -> Tuple[List[float], str]:
    """
    Standard function matching the project specification:
    returns (pool_history, status)
    """
    sim = MicrogridSimulation(
        fiber_length=fiber_length,
        attack_level=attack_level,
        data_frequency=data_frequency,
        time_steps=time_steps,
        enable_kps=enable_kps,
    )
    res = sim.run()
    return res["pool_a_history"], res["status"]
