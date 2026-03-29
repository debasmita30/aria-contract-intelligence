"""
ARIA — Main Entry Point

Usage:
    # Launch Streamlit UI
    streamlit run app/streamlit_app.py

    # CLI demo
    python app/main.py

    # CLI demo with failure simulation
    python app/main.py --failure

    # Benchmark simulation
    python app/main.py --benchmark --runs 100
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="ARIA — Autonomous Reliability & Intelligence Architecture"
    )
    parser.add_argument("--failure",   action="store_true",        help="Simulate failure + recovery")
    parser.add_argument("--benchmark", action="store_true",        help="Run Monte Carlo benchmark")
    parser.add_argument("--runs",      type=int,   default=100,    help="Benchmark runs (default 100)")
    parser.add_argument("--contract",  type=str,   default=None,   help="Path to contract .txt")
    parser.add_argument("--json",      action="store_true",        help="Print raw JSON result")
    parser.add_argument("--verbose",   action="store_true",        help="Verbose output")
    args = parser.parse_args()

    if args.benchmark:
        from evaluation.simulation import main as sim_main
        sim_main(n_runs=args.runs, verbose=args.verbose)
    else:
        # Patch sys.argv for demo runner
        sys.argv = ["run_demo.py"]
        if args.failure:   sys.argv.append("--failure")
        if args.contract:  sys.argv += ["--contract", args.contract]
        if args.json:      sys.argv.append("--json")

        from demo.run_demo import main as demo_main
        demo_main()


if __name__ == "__main__":
    main()
