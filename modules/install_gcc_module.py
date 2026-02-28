import subprocess
import os
import re
import requests
from pathlib import Path


class GCCInstaller:

    def __init__(self):
        self.home = str(Path.home())
        self.install_dir = f"{self.home}/hpc/gcc"
        self.src_dir = f"{self.home}/hpc_sources"

        self.VERSION = self.get_latest_gcc_version()
        self.tar_name = f"gcc-{self.VERSION}.tar.gz"
        self.src_folder = f"gcc-{self.VERSION}"

    # -----------------------------
    # Fetch Latest GCC Version
    # -----------------------------
    def get_latest_gcc_version(self):
        print("Fetching latest GCC version...")

        url = "https://ftp.gnu.org/gnu/gcc/"
        response = requests.get(url)

        versions = re.findall(r'gcc-(\d+\.\d+\.\d+)/', response.text)

        versions.sort(key=lambda s: list(map(int, s.split("."))))
        latest = versions[-1]

        print(f"Latest GCC version detected: {latest}")
        return latest

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
    # Install Build Dependencies
    # -----------------------------
    def install_dependencies(self, pkg_manager):
        print("Installing GCC build dependencies...")

        if pkg_manager == "apt":
            self.run(["sudo", "apt", "update"])
            self.run([
                "sudo", "apt", "install", "-y",
                "build-essential",
                "libgmp-dev",
                "libmpfr-dev",
                "libmpc-dev",
                "wget",
                "curl"
            ])

        elif pkg_manager == "dnf":
            self.run([
                "sudo", "dnf", "install", "-y",
                "gcc",
                "gcc-c++",
                "make",
                "gmp-devel",
                "mpfr-devel",
                "libmpc-devel",
                "wget",
                "curl"
            ])

    # -----------------------------
    # Download Source
    # -----------------------------
    def download_source(self):
        print("Downloading GCC source...")

        os.makedirs(self.src_dir, exist_ok=True)
        os.chdir(self.src_dir)

        if not os.path.exists(self.tar_name):
            url = f"https://ftp.gnu.org/gnu/gcc/gcc-{self.VERSION}/{self.tar_name}"
            self.run(["wget", url])
        else:
            print("Source already downloaded.")

    # -----------------------------
    # Build & Install
    # -----------------------------
    def build_and_install(self):
        print("Extracting GCC...")

        os.chdir(self.src_dir)

        if not os.path.exists(self.src_folder):
            self.run(["tar", "-xf", self.tar_name])

        os.chdir(self.src_folder)

        print("Downloading prerequisites...")
        if os.path.exists("contrib/download_prerequisites"):
            self.run(["./contrib/download_prerequisites"])

        os.makedirs("build", exist_ok=True)
        os.chdir("build")

        print("Configuring GCC...")
        self.run([
            "../configure",
            f"--prefix={self.install_dir}",
            "--enable-languages=c,c++",
            "--disable-multilib"
        ])

        print("Building GCC (this will take time)...")
        self.run(["make", f"-j{os.cpu_count()}"])

        print("Installing GCC...")
        self.run(["make", "install"])

    # -----------------------------
    # Update PATH
    # -----------------------------
    def update_environment(self):
        bashrc = f"{self.home}/.bashrc"

        if not os.path.exists(bashrc):
            open(bashrc, "w").close()

        with open(bashrc, "r") as f:
            content = f.read()

        if "hpc/gcc/bin" not in content:
            with open(bashrc, "a") as f:
                f.write('\nexport PATH="$HOME/hpc/gcc/bin:$PATH"\n')
            print("PATH updated in ~/.bashrc")
        else:
            print("PATH already configured.")

    # -----------------------------
    # Verify Installation
    # -----------------------------
    def verify(self):
        print("Verifying GCC installation...")

        gcc_path = f"{self.install_dir}/bin/gcc"

        if os.path.exists(gcc_path):
            result = subprocess.run(
                [gcc_path, "--version"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✔ GCC Installed Successfully")
                print(result.stdout.splitlines()[0])
            else:
                raise Exception("GCC verification failed.")
        else:
            raise Exception("GCC installation failed.")

    # -----------------------------
    # Main Install Flow
    # -----------------------------
    def install(self):

        if os.path.exists(f"{self.install_dir}/bin/gcc"):
            print("GCC already installed.")
            self.verify()
            return

        pkg_manager = self.detect_package_manager()

        self.install_dependencies(pkg_manager)
        self.download_source()
        self.build_and_install()
        self.update_environment()
        self.verify()

        print("==== GCC Installation Complete ====")
        print("Run: source ~/.bashrc")

if __name__ == "__main__":
    installer = GCCInstaller()
    installer.install()