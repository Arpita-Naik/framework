import os
import shutil
from pathlib import Path
import re


class PythonRemover:

    def __init__(self):
        self.home = str(Path.home())
        self.install_dir = f"{self.home}/hpc/python"
        self.src_dir = f"{self.home}/hpc_sources"
        self.bashrc = f"{self.home}/.bashrc"

    # -----------------------------
    # Remove Installation Directory
    # -----------------------------
    def remove_installation(self):
        print("Removing Python installation...")

        if os.path.exists(self.install_dir):
            shutil.rmtree(self.install_dir, ignore_errors=True)
            print("✔ Removed install directory.")
        else:
            print("Install directory not found. Skipping.")

    # -----------------------------
    # Remove Source Files
    # -----------------------------
    def remove_sources(self):
        if not os.path.exists(self.src_dir):
            return

        for item in os.listdir(self.src_dir):
            if item.startswith("Python-"):
                path = os.path.join(self.src_dir, item)

                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"✔ Removed source folder: {item}")

                elif item.endswith(".tar.xz"):
                    os.remove(path)
                    print(f"✔ Removed tar file: {item}")

    # -----------------------------
    # Clean PATH from .bashrc
    # -----------------------------
    def clean_bashrc(self):
        if not os.path.exists(self.bashrc):
            return

        with open(self.bashrc, "r") as f:
            lines = f.readlines()

        with open(self.bashrc, "w") as f:
            for line in lines:
                if "hpc/python/bin" not in line:
                    f.write(line)

        print("✔ Removed PATH entry from ~/.bashrc")

    # -----------------------------
    # Main Flow
    # -----------------------------
    def remove(self):
        print("===== Removing Python (HPC Version) =====")

        self.remove_installation()
        self.remove_sources()
        self.clean_bashrc()

        print("===== Python completely removed =====")
        print("Run: source ~/.bashrc")