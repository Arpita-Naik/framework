import os
import sys
import time
import subprocess

from system_check.detect_os import OSDetector
from slurm.preprocess_slurm import SlurmPreprocessor
from slurm.install_slurm import SlurmInstaller
from modules.install_python_module import PythonInstaller
from modules.install_openmpi_module import OpenMPIInstaller


class HPCFramework:

    def check_root(self):
        if os.geteuid() != 0:
            print("Run as root: sudo python3 master_setup.py")
            sys.exit(1)

    def verify_munge(self):
        print("Verifying Munge...")

        if subprocess.run(
            ["systemctl", "is-active", "--quiet", "munge"]
        ).returncode != 0:
            subprocess.run(["systemctl", "restart", "munge"])

        if subprocess.run(
            ["systemctl", "is-active", "--quiet", "munge"]
        ).returncode != 0:
            print("Munge failed. Stopping setup.")
            sys.exit(1)

        print("✔ Munge running.")

    def verify_slurm(self):
        print("Verifying Slurm...")
        time.sleep(2)

        result = subprocess.run(
            ["sinfo"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✔ Slurm responding correctly.")
            print(result.stdout)
        else:
            print("Slurm installed but not responding.")

    def setup(self):
        print("===== HPC FRAMEWORK START =====")

        self.check_root()

        detector = OSDetector()
        detector.detect()
        print("===== OS CHECK COMPLETE =====")

        preprocessor = SlurmPreprocessor()
        slurm_status = preprocessor.check()

        print("--------------------------------")

        if slurm_status == "installed":
            print("Slurm fully configured. Skipping installation.")

        elif slurm_status in ["broken_cleaned", "not_installed"]:
            print("Installing Slurm...")
            SlurmInstaller().install()

        else:
            print("Unknown Slurm status.")
            sys.exit(1)

        self.verify_munge()

        print("--------------------------------")
        print("Setting up Python...")
        PythonInstaller().install()

        print("--------------------------------")
        print("Setting up OpenMPI...")
        OpenMPIInstaller().install()

        print("--------------------------------")

        self.verify_slurm()

        print("===== HPC FRAMEWORK SETUP COMPLETE =====")


if __name__ == "__main__":
    HPCFramework().setup()