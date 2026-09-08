"""
Test Suite for QKD Microgrid Stability Simulation
Validates physics calculations, threshold alarms, KPS mechanisms, and boundary sweeps.
"""

import unittest
import numpy as np
from qkd_engine import calculate_transmittance, calculate_key_rate, calculate_qkd_metrics
from grid_controller import MicrogridSimulation, run_grid_simulation
from sensitivity_suite import run_boundary_sweep


class TestQKDMicrogridSimulation(unittest.TestCase):

    def test_transmittance_decay(self):
        # Transmittance should strictly decrease with distance
        t0 = calculate_transmittance(0.0)
        t10 = calculate_transmittance(10.0)
        t70 = calculate_transmittance(70.0)

        self.assertAlmostEqual(t0, 1.0, places=4)
        self.assertTrue(t0 > t10 > t70 > 0.0)

    def test_normal_case_10km(self):
        # At 10km, key rate should be healthy and positive (> 200,000 bps)
        metrics = calculate_qkd_metrics(10.0, e_mis_current=5e-4)
        self.assertFalse(metrics["eve_detected"])
        self.assertGreater(metrics["secret_key_rate_bps"], 100000.0)

        # Simulation with moderate traffic (10 pkts/s = 2560 bps) should be highly stable
        pool_history, status = run_grid_simulation(fiber_length=10.0, data_frequency=10.0)
        self.assertIn("Stable", status)
        self.assertGreater(pool_history[-1], pool_history[0])

    def test_quantum_wall_70km(self):
        # At 70km, transmittance drops significantly and key generation is ~15,714 bps
        rate_10 = calculate_key_rate(10.0)
        rate_70 = calculate_key_rate(70.0)
        self.assertGreater(rate_10, rate_70)

        # With 100 pkts/s (consumption = 25,600 bps > 15,714 bps generation) and 5,000 initial bits,
        # pool A exhausts quickly without KPS
        sim = MicrogridSimulation(
            fiber_length=70.0,
            data_frequency=100.0,
            initial_pool_a=5000.0,
            enable_kps=False,
            time_steps=20,
        )
        res = sim.run()
        self.assertIn("FAILED", res["status"])
        self.assertEqual(res["pool_a_history"][-1], 0.0)

    def test_eve_intercept_resend_attack(self):
        # 1. High misalignment attack e_mis = 0.10:
        # Secret key rate crashes by >90% compared to baseline
        baseline = calculate_qkd_metrics(10.0, e_mis_current=5e-4)["secret_key_rate_bps"]
        attacked = calculate_qkd_metrics(10.0, e_mis_current=0.10)["secret_key_rate_bps"]
        self.assertLess(attacked, baseline * 0.10)

        # 2. Severe attack e_mis = 0.12 exceeds the 11% QBER threshold
        critical_metrics = calculate_qkd_metrics(10.0, e_mis_current=0.12)
        self.assertTrue(critical_metrics["eve_detected"])
        self.assertEqual(critical_metrics["secret_key_rate_bps"], 0.0)

        sim = MicrogridSimulation(fiber_length=10.0, attack_level=0.12, data_frequency=30.0)
        res = sim.run()
        has_eve_log = any("Eve Detected" in log for log in res["logs"])
        self.assertTrue(has_eve_log)

    def test_kps_sharing_feature(self):
        # Set deficit conditions (gen: 15,714 bps, cons: 25,600 bps)
        # With initial pool A = 6,000 bits and threshold = 5,000, KPS must trigger
        sim = MicrogridSimulation(
            fiber_length=70.0,
            data_frequency=100.0,
            initial_pool_a=6000.0,
            initial_pool_b=20000.0,
            enable_kps=True,
            kps_threshold=5000.0,
            kps_borrow_amount=1000.0,
            time_steps=5,
        )
        res = sim.run()
        self.assertGreater(res["kps_borrow_count"], 0)
        has_borrow_log = any("KPS BORROW" in log for log in res["logs"])
        self.assertTrue(has_borrow_log)

    def test_boundary_sweep(self):
        sweep = run_boundary_sweep(distances=np.array([5, 20, 50, 80]), frequencies=[10, 50])
        self.assertEqual(len(sweep["frequencies"]), 2)
        self.assertEqual(len(sweep["results"][10]["scores"]), 4)


if __name__ == "__main__":
    unittest.main()
