"""Offline checks: real serial/IMU hardware is not simulated by these tests."""
import csv, tempfile, unittest
from pathlib import Path
import numpy as np
from rekam_serial import parse_sample, export
from analisis_langkah import analyze

class LabTests(unittest.TestCase):
    def signal(self,walking):
        t=np.arange(1150)*20
        z=9.80665+np.where(t>=3000,2*np.sin(2*np.pi*2*(t/1000-3)),0) if walking else np.full(1150,9.80665)
        return [[int(ts),0,0,float(v),0,0,0] for ts,v in zip(t,z)]
    def test_stationary_and_walk(self):
        with tempfile.TemporaryDirectory() as folder:
            for active,expected in [(False,0),(True,40)]:
                raw,ei,meta=export(self.signal(active),Path(folder)/str(active),{})
                self.assertEqual(analyze(raw)[-1]['predicted_steps'],expected)
                self.assertTrue(meta['timing_ok'])
                with ei.open() as f:rows=list(csv.reader(f))
                self.assertEqual(len(rows),1001)
                self.assertEqual(float(rows[1][0]),0)
                self.assertEqual(len(rows[1]),4)
    def test_bad_rows_and_gap(self):
        for value in ['1,2,3','0,0,0,nan,0,0,0']:
            with self.assertRaises(ValueError):parse_sample(value)
        with tempfile.TemporaryDirectory() as folder:
            rows=self.signal(True);del rows[200]
            raw,_,meta=export(rows,Path(folder)/'gap',{})
            self.assertFalse(meta['timing_ok'])
            with self.assertRaises(ValueError):analyze(raw)
    def test_reject_out_of_order(self):
        with tempfile.TemporaryDirectory() as folder:
            rows=self.signal(False);rows[3][0]=rows[2][0]
            with self.assertRaises(ValueError):export(rows,Path(folder)/'bad',{})

if __name__=='__main__':unittest.main()
