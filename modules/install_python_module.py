import subprocess
import os
import re
import requests
from pathlib import Path
from utils.os_detector import OSDetector


class PythonInstaller:

    def __init__(self):
        self.home = str(Path.home())
        self.install_dir = f"{self.home}/hpc/python"
        self.src_dir = f"{self.home}/hpc_sources"

        # 🔥 Fetch latest version automatically
        self.VERSION = self.get_latest_python_version()

        self.tar_name = f"Python-{self.VERSION}.tar.xz"
        self.src_folder = f"Python-{self.VERSION}"

    # -----------------------------
    # Fetch Latest Python Version
    # -----------------------------
    def get_latest_python_version(self):
        print("Fetching latest Python version...")

        url = "https://www.python.org/ftp/python/"
        response = requests.get(url)

        versions = re.findall(r'href="(\d+\.\d+\.\d+)/"', response.text)

        # Sort properly by numeric value
        versions.sort(key=lambda s: list(map(int, s.split("."))))

        latest = versions[-1]
        print(f"Latest Python version detected: {latest}")
        return latest

    # -----------------------------
    # Utility Runner
    # -----------------------------
    def run(self, command):
        subprocess.run(command, check=True)

    # -----------------------------
    # Install Build Dependencies
    # -----------------------------
    def install_dependencies(self, pkg_manager):
        print("==== Installing Build Dependencies ====")

        if pkg_manager == "apt":
            self.run(["sudo", "apt", "update"])
            self.run([
                "sudo", "apt", "install", "-y",
                "build-essential",
                "libssl-dev",
                "zlib1g-dev",
                "libncurses5-dev",
                "libncursesw5-dev",
                "libreadline-dev",
                "libsqlite3-dev",
                "libgdbm-dev",
                "libdb5.3-dev",
                "libbz2-dev",
                "libexpat1-dev",
                "liblzma-dev",
                "tk-dev",
                "wget",
                "curl"
            ])

        elif pkg_manager == "dnf":
            self.run([
                "sudo", "dnf", "install", "-y",
                "gcc",
                "make",
                "openssl-devel",
                "bzip2-devel",
                "libffi-devel",
                "zlib-devel",
                "readline-devel",
                "sqlite-devel",
                "xz-devel",
                "tk-devel",
                "wget",
                "curl"
            ])

        else:
            raise Exception("Unsupported package manager.")

    # -----------------------------
    # Download Source
    # -----------------------------
    def download_source(self):
        print("==== Downloading Python Source ====")

        os.makedirs(self.src_dir, exist_ok=True)
        os.chdir(self.src_dir)

        if not os.path.exists(self.tar_name):
            url = f"https://www.python.org/ftp/python/{self.VERSION}/{self.tar_name}"
            self.run(["wget", url])
        else:
            print("Source already downloaded.")

    # -----------------------------
    # Build & Install
    # -----------------------------
    def build_and_install(self):
        print("==== Extracting Source ====")

        os.chdir(self.src_dir)

        if not os.path.exists(self.src_folder):
            self.run(["tar", "-xf", self.tar_name])

        os.chdir(self.src_folder)

        print("==== Configuring Python ====")
        self.run([
            "./configure",
            f"--prefix={self.install_dir}",
            "--enable-optimizations"
        ])

        print("==== Building Python ====")
        self.run(["make", f"-j{os.cpu_count()}"])

        print("==== Installing Python ====")
        self.run(["make", "install"])

    # -----------------------------
    # Update PATH
    # -----------------------------
    def update_bashrc(self):
        bashrc_path = f"{self.home}/.bashrc"

        if not os.path.exists(bashrc_path):
            open(bashrc_path, "w").close()

        with open(bashrc_path, "r") as f:
            content = f.read()

        if "hpc/python/bin" not in content:
            with open(bashrc_path, "a") as f:
                f.write('\nexport PATH="$HOME/hpc/python/bin:$PATH"\n')

            print("PATH updated in ~/.bashrc")
        else:
            print("PATH already configured.")

    # -----------------------------
    # Verification
    # -----------------------------
    def verify(self):
        print("==== Verifying Python Installation ====")

        python_path = f"{self.install_dir}/bin/python3"

        if os.path.exists(python_path):
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✔ Installed Version:", result.stdout.strip())
            else:
                raise Exception("Python verification failed.")
        else:
            raise Exception("Python installation failed.")

    # -----------------------------
    # Main Install Flow
    # -----------------------------
    def install(self):
        detector = OSDetector()
        system_info = detector.detect()
        pkg_manager = system_info["package_manager"]

        if os.path.exists(f"{self.install_dir}/bin/python3"):
            print("Python already installed.")
            self.verify()
            return

        self.install_dependencies(pkg_manager)
        self.download_source()
        self.build_and_install()
        self.update_bashrc()
        self.verify()

        print("==== Python Installation Complete ====")
        print("Run: source ~/.bashrc")