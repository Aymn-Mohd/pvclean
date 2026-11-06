"""Wrote the golden files, on the code before the restructure (tag archive/e1-pes-r1-20261105). Never rerun this to make a test pass."""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cases

if __name__ == "__main__":
    for name, fn in cases.CASES.items():
        t0 = time.time(); s = cases.text(fn())
        open(os.path.join(HERE, "golden", f"{name}.json"), "w").write(s)
        print(name, len(s), "bytes", round(time.time() - t0, 1), "s", flush=True)
