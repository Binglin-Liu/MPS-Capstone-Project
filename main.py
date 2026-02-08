# main.py
# -*- coding: utf-8 -*-

"""
Main Orchestrator (System Architect)

This script connects three independent modules:

STEP 1: Get_data.py
    - Extract plan names from Form 5500 dataset
    - Filter 401(k) / 403(b)
    - Deduplicate
    - Output: filtered_401k_403b_plans.csv

STEP 2: MPS Capstone Project - Automating to web and searching by plan.py
    - Open efast website
    - Filter Plan Year = 2024
    - Search each plan name using Selenium

STEP 3: DownloadFile.py
    - Download 2024 file from efast website

This file does NOT modify any teammate code.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path


# -------------------------------------------------
# Utility: dynamically load a .py file as module
# -------------------------------------------------
def load_module(py_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(py_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


# -------------------------------------------------
# STEP 1: Extract & clean plan names
# -------------------------------------------------
def run_step1(form5500_csv: Path) -> Path:
    """
    Run Get_data.py -> process_form5500()
    """
    print("\n===== STEP 1: Extract & clean plan names =====")

    step1_script = Path("Get_data.py")
    if not step1_script.exists():
        raise FileNotFoundError("Get_data.py not found")

    mod = load_module(step1_script, "get_data_mod")

    if not hasattr(mod, "process_form5500"):
        raise AttributeError("Get_data.py must define process_form5500(file_path)")

    mod.process_form5500(str(form5500_csv))

    output_csv = Path("filtered_401k_403b_plans.csv")
    if not output_csv.exists():
        raise FileNotFoundError("STEP 1 failed: output CSV not found")

    print(f"STEP 1 completed. Output: {output_csv}")
    return output_csv


# -------------------------------------------------
# STEP 2: Search each plan on efast (script-style)
# -------------------------------------------------
def run_step2():
    """
    Run Selenium search script directly.
    This script executes on import / run.
    """
    print("\n===== STEP 2: Search plans on efast =====")

    step2_script = Path("MPS Capstone Project - Automating to web and searching by plan.py")
    if not step2_script.exists():
        raise FileNotFoundError("Step 2 search script not found")

    # Run as a subprocess to avoid namespace / side-effect issues
    subprocess.run([sys.executable, str(step2_script)], check=True)

    print("STEP 2 completed (search executed).")


# -------------------------------------------------
# STEP 3: Download 2024 file
# -------------------------------------------------
def run_step3(download_dir: Path):
    """
    Call download_2024_file(download_path)
    """
    print("\n===== STEP 3: Download 2024 file =====")

    step3_script = Path("DownloadFile.py")
    if not step3_script.exists():
        raise FileNotFoundError("DownloadFile.py not found")

    download_dir.mkdir(parents=True, exist_ok=True)

    mod = load_module(step3_script, "download_mod")

    if not hasattr(mod, "download_2024_file"):
        raise AttributeError("DownloadFile.py must define download_2024_file(download_path)")

    mod.download_2024_file(str(download_dir))

    print(f"STEP 3 completed. Files saved to: {download_dir}")


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    """
    Orchestrates STEP 1 -> STEP 2 -> STEP 3
    """

    # 🔧 CHANGE THIS to your real CSV file path
    form5500_csv = Path("form5500.csv")

    if not form5500_csv.exists():
        raise FileNotFoundError(f"Form 5500 CSV not found: {form5500_csv}")

    download_dir = Path("outputs/downloads")

    print("\n========== PIPELINE START ==========")

    run_step1(form5500_csv)
    run_step2()
    run_step3(download_dir)

    print("\n========== PIPELINE FINISHED ==========")


if __name__ == "__main__":
    main()

