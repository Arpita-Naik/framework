import subprocess
import os
from pathlib import Path


class OpenMPIInstaller:

    def __init__(self):
        # Default version (can override via env variable)
        self.VERSION = os.getenv("OPENMPI_VERSION", "4.1.6")

        self.home = str(Path.home())
        self.install_dir = f"{self.home}/hpc/openmpi"
        self.src_dir = f"{self.home}/hpc_sources"

        self.tar_name = f"openmpi-{self.VERSION}.tar.gz"
        self.src_folder = f"openmpi-{self.VERSION}"

    # -----------------------------
    # Utility Runner
    # -----------------------------
    def run(self, command):
        subprocess.run(command, check=True)

    # -----------------------------
    # Detect Package Manager
    # -----------------------------
    def detect_package_manager(self):
        if subprocess.run(["which", "apt"], stdout=subprocess.DEVNULL).returncode == 0:
            return "apt"
        elif subprocess.run(["which", "dnf"], stdout=subprocess.DEVNULL).returncode == 0:
            return "dnf"
        else:
            raise Exception("Unsupported Linux distribution.")

    # -----------------------------
    # Install Dependencies
    # -----------------------------
    def install_dependencies(self, pkg_manager):
        print("==== Installing Dependencies ====")

        if pkg_manager == "apt":
            self.run(["sudo", "apt", "update"])
            self.run(["sudo", "apt", "install", "-y",
                      "build-essential", "gcc", "g++", "make", "wget", "curl"])

        elif pkg_manager == "dnf":
            self.run(["sudo", "dnf", "install", "-y",
                      "gcc", "gcc-c++", "make", "wget", "curl"])

    # -----------------------------
    # Download Source
    # -----------------------------
    def download_source(self):
        print("==== Downloading OpenMPI ====")

        os.makedirs(self.src_dir, exist_ok=True)
        os.chdir(self.src_dir)

        if not os.path.exists(self.tar_name):
            url = f"https://download.open-mpi.org/release/open-mpi/v4.1/{self.tar_name}"
            self.run(["wget", url])
        else:
            print("Source already downloaded.")

    # -----------------------------
    # Build & Install
    # -----------------------------
    def build_and_install(self):
        print("==== Extracting ====")

        os.chdir(self.src_dir)

        if not os.path.exists(self.src_folder):
            self.run(["tar", "-xf", self.tar_name])

        os.chdir(self.src_folder)

        print("==== Configuring ====")
        self.run(["./configure", f"--prefix={self.install_dir}"])

        print("==== Building ====")
        self.run(["make", f"-j{os.cpu_count()}"])

        print("==== Installing ====")
        self.run(["make", "install"])

    # -----------------------------
    # Update Environment
    # -----------------------------
    def update_environment(self):
        bashrc = f"{self.home}/.bashrc"

        if not os.path.exists(bashrc):
            open(bashrc, "w").close()

        with open(bashrc, "r") as f:
            content = f.read()

        if "hpc/openmpi/bin" not in content:
            with open(bashrc, "a") as f:
                f.write('\nexport PATH="$HOME/hpc/openmpi/bin:$PATH"\n')
                f.write('export LD_LIBRARY_PATH="$HOME/hpc/openmpi/lib:$LD_LIBRARY_PATH"\n')

            print("Environment variables added to ~/.bashrc")
        else:
            print("Environment already configured.")

    # -----------------------------
    # Verify Installation
    # -----------------------------
    def verify(self):
        print("==== Verifying Installation ====")

        mpirun_path = f"{self.install_dir}/bin/mpirun"

        if os.path.exists(mpirun_path):
            result = subprocess.run(
                [mpirun_path, "--version"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✔ OpenMPI Installed Successfully")
                print(result.stdout.splitlines()[0])
            else:
                raise Exception("Verification failed.")
        else:
            raise Exception("OpenMPI installation failed.")

    # -----------------------------
    # Main Install Flow
    # -----------------------------
    def install(self):

        # Skip if already installed
        if os.path.exists(f"{self.install_dir}/bin/mpirun"):
            print("OpenMPI already installed.")
            self.verify()
            return

        pkg_manager = self.detect_package_manager()
        self.install_dependencies(pkg_manager)
        self.download_source()
        self.build_and_install()
        self.update_environment()
        self.verify()

        print("==== OpenMPI Installation Complete ====")
        print("Run: source ~/.bashrc")