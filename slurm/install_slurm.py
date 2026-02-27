import subprocess
import os
from utils.os_detector import OSDetector


class SlurmInstaller:

    VERSION = "24.11.1"
    WORKDIR = "/root"

    # -----------------------------
    # Utility Runner
    # -----------------------------

    def run(self, command):
        subprocess.run(command, check=True)

    # -----------------------------
    # Install Dependencies
    # -----------------------------

    def install_dependencies(self, pkg_manager):
        print("==== Installing Required Packages ====")

        if pkg_manager == "apt":
            self.run(["sudo", "apt", "update"])

            packages = [
                "build-essential",
                "munge",
                "libmunge-dev",
                "libssl-dev",
                "libpam0g-dev",
                "libmariadb-dev",
                "libjson-c-dev",
                "libhwloc-dev",
                "pkg-config",
                "bison",
                "flex",
                "mariadb-server",
                "curl",
                "wget"
            ]

            self.run(["sudo", "apt", "install", "-y"] + packages)

        elif pkg_manager == "dnf":
            packages = [
                "gcc",
                "gcc-c++",
                "make",
                "munge",
                "munge-devel",
                "openssl-devel",
                "pam-devel",
                "mariadb-devel",
                "json-c-devel",
                "hwloc-devel",
                "pkgconfig",
                "bison",
                "flex",
                "mariadb-server",
                "curl",
                "wget"
            ]

            self.run(["sudo", "dnf", "install", "-y"] + packages)

        else:
            raise Exception("Unsupported package manager.")

    # -----------------------------
    # Enable Munge
    # -----------------------------

    def enable_munge(self):
        print("==== Enabling Munge ====")
        self.run(["sudo", "systemctl", "enable", "munge"])
        self.run(["sudo", "systemctl", "restart", "munge"])

    # -----------------------------
    # Download & Build Slurm
    # -----------------------------

    def download_and_build(self):
        print("==== Downloading Slurm Source ====")

        os.chdir(self.WORKDIR)

        tar_file = f"slurm-{self.VERSION}.tar.bz2"
        source_dir = f"slurm-{self.VERSION}"

        # Download
        self.run([
            "sudo", "wget", "-q",
            f"https://download.schedmd.com/slurm/{tar_file}"
        ])

        # Extract
        self.run(["sudo", "tar", "-xjf", tar_file])

        os.chdir(os.path.join(self.WORKDIR, source_dir))

        print("==== Building Slurm ====")

        self.run(["sudo", "./configure", "--sysconfdir=/etc/slurm"])
        self.run(["sudo", "make", f"-j{os.cpu_count()}"])
        self.run(["sudo", "make", "install"])

    # -----------------------------
    # Create Slurm User
    # -----------------------------

    def create_slurm_user(self):
        print("==== Creating Slurm User ====")

        result = subprocess.run(
            ["id", "slurm"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if result.returncode != 0:
            self.run(["sudo", "useradd", "-r", "-m", "slurm"])

    # -----------------------------
    # Setup Directories
    # -----------------------------

    def setup_directories(self):
        print("==== Creating Directories ====")

        dirs = [
            "/etc/slurm",
            "/var/spool/slurmctld",
            "/var/spool/slurmd",
            "/var/log/slurm"
        ]

        for d in dirs:
            self.run(["sudo", "mkdir", "-p", d])

        self.run(["sudo", "chown", "-R", "slurm:slurm", "/var/spool/slurmctld"])
        self.run(["sudo", "chown", "-R", "slurm:slurm", "/var/spool/slurmd"])
        self.run(["sudo", "chown", "-R", "slurm:slurm", "/var/log/slurm"])

    # -----------------------------
    # Enable Services
    # -----------------------------

    def enable_services(self):
        print("==== Enabling Slurm Services ====")

        self.run(["sudo", "systemctl", "daemon-reload"])
        self.run(["sudo", "systemctl", "enable", "slurmctld"])
        self.run(["sudo", "systemctl", "enable", "slurmd"])

        self.run(["sudo", "systemctl", "restart", "munge"])
        self.run(["sudo", "systemctl", "start", "slurmctld"])
        self.run(["sudo", "systemctl", "start", "slurmd"])

    # -----------------------------
    # Verification Using sinfo
    # -----------------------------

    def verify(self):
        print("==== Verifying Slurm Installation ====")

        result = subprocess.run(
            ["sinfo"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✔ Slurm is responding correctly.\n")
            print(result.stdout)
        else:
            print("✖ Slurm verification failed.")
            print(result.stderr)
            raise Exception("Slurm installation verification failed.")

    # -----------------------------
    # Main Installer
    # -----------------------------

    def install(self):
        detector = OSDetector()
        system_info = detector.detect()

        pkg_manager = system_info["package_manager"]

        self.install_dependencies(pkg_manager)
        self.enable_munge()
        self.download_and_build()
        self.create_slurm_user()
        self.setup_directories()
        self.enable_services()
        self.verify()

        print("==== Slurm Installation Complete ====")