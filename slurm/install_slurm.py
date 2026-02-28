import subprocess
import os
from system_check.detect_os import OSDetector


class SlurmInstaller:

    VERSION = "24.11.1"
    WORKDIR = "/root"

    # -----------------------------
    # Utility Runner
    # -----------------------------

    def run(self, command):
        print("Running:", " ".join(command))
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

        if not os.path.exists(tar_file):
            self.run([
                "sudo", "wget",
                f"https://download.schedmd.com/slurm/{tar_file}"
            ])

        if not os.path.exists(source_dir):
            self.run(["sudo", "tar", "-xjf", tar_file])

        os.chdir(os.path.join(self.WORKDIR, source_dir))

        print("==== Building Slurm ====")

        self.run(["sudo", "./configure", "--sysconfdir=/etc/slurm","--without-cgroup","--disable-cgroup"])
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
            "/var/log/slurm",
            "/run/slurm"
        ]

        for d in dirs:
            self.run(["sudo", "mkdir", "-p", d])

        self.run(["sudo", "chown", "-R", "slurm:slurm", "/var/spool/slurmctld"])
        self.run(["sudo", "chown", "-R", "slurm:slurm", "/var/spool/slurmd"])
        self.run(["sudo", "chown", "-R", "slurm:slurm", "/var/log/slurm"])
        self.run(["sudo", "chown", "-R", "slurm:slurm", "/run/slurm"])

    # -----------------------------
    # Create slurm.conf
    # -----------------------------

    def create_slurm_conf(self):
        print("==== Creating slurm.conf ====")

        hostname = subprocess.check_output(["hostname"], text=True).strip()
        cpu_count = os.cpu_count()

        config = f"""
ClusterName=cluster
SlurmctldHost={hostname}

SlurmUser=slurm
StateSaveLocation=/var/spool/slurmctld
SlurmdSpoolDir=/var/spool/slurmd

AuthType=auth/munge
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
JobAcctGatherType=jobacct_gather/none
CgroupPlugin=disabled

SlurmctldPidFile=/run/slurm/slurmctld.pid
SlurmdPidFile=/run/slurm/slurmd.pid

SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log

SelectType=select/cons_tres
SchedulerType=sched/backfill

NodeName={hostname} CPUs={cpu_count} State=UNKNOWN
PartitionName=debug Nodes={hostname} Default=YES MaxTime=INFINITE State=UP
"""

        with open("/tmp/slurm.conf", "w") as f:
            f.write(config)

        self.run(["sudo", "mv", "/tmp/slurm.conf", "/etc/slurm/slurm.conf"])
        self.run(["sudo", "chown", "slurm:slurm", "/etc/slurm/slurm.conf"])
        self.run(["sudo", "chmod", "644", "/etc/slurm/slurm.conf"])

    # -----------------------------
    # Install systemd service files
    # -----------------------------

    def install_systemd_services(self):
        print("==== Installing systemd service files ====")

        source_dir = f"{self.WORKDIR}/slurm-{self.VERSION}"

        self.run([
            "sudo", "cp",
            f"{source_dir}/etc/slurmctld.service",
            "/etc/systemd/system/"
        ])

        self.run([
            "sudo", "cp",
            f"{source_dir}/etc/slurmd.service",
            "/etc/systemd/system/"
        ])

        self.run(["sudo", "systemctl", "daemon-reload"])
        self.run(["sudo", "systemctl", "daemon-reexec"])

    # -----------------------------
    # Enable Services
    # -----------------------------

    def enable_services(self):
        print("==== Enabling Slurm Services ====")

        self.run(["sudo", "systemctl", "enable", "slurmctld"])
        self.run(["sudo", "systemctl", "enable", "slurmd"])

        self.run(["sudo", "systemctl", "restart", "munge"])
        self.run(["sudo", "systemctl", "start", "slurmctld"])
        self.run(["sudo", "systemctl", "start", "slurmd"])

    # -----------------------------
    # Verify Using sinfo
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
    # Main Install Flow
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
        self.create_slurm_conf()
        self.install_systemd_services()
        self.enable_services()
        self.verify()

        print("==== Slurm Installation Complete ====")


if __name__ == "__main__":
    installer = SlurmInstaller()
    installer.install()