import subprocess
import os
import shutil


class SlurmRemover:

    def run(self, command, ignore_error=False):
        try:
            subprocess.run(command, check=not ignore_error)
        except subprocess.CalledProcessError:
            if not ignore_error:
                raise

    
    def check_root(self):
        if os.geteuid() != 0:
            print("Run as root (sudo).")
            exit(1)

    
    def detect_package_manager(self):
        if shutil.which("apt"):
            return "apt"
        elif shutil.which("dnf"):
            return "dnf"
        else:
            return None

    def stop_services(self):
        print("Stopping services...")

        services = [
            "slurmctld",
            "slurmd",
            "slurmdbd",
            "munge"
        ]

        for service in services:
            self.run(["systemctl", "stop", service], ignore_error=True)
            self.run(["systemctl", "disable", service], ignore_error=True)

    def remove_packages(self, pkg_manager):
        print("Removing Slurm and Munge packages...")

        if pkg_manager == "apt":
            self.run([
                "apt", "purge", "-y",
                "slurm-wlm",
                "munge",
                "slurmctld",
                "slurmd",
                "slurmdbd"
            ], ignore_error=True)

            self.run(["apt", "autoremove", "-y"], ignore_error=True)

        elif pkg_manager == "dnf":
            self.run([
                "dnf", "remove", "-y",
                "slurm",
                "munge",
                "slurm-slurmctld",
                "slurm-slurmd",
                "slurm-slurmdbd"
            ], ignore_error=True)

    def remove_directories(self):
        print("Removing configuration directories...")

        paths = [
            "/etc/slurm",
            "/etc/munge",
            "/var/lib/munge",
            "/var/log/munge",
            "/run/munge",
            "/var/spool/slurmctld",
            "/var/spool/slurmd"
        ]

        for path in paths:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)

    def remove_users(self):
        print("Removing users...")

        users = ["slurm", "munge"]

        for user in users:
            self.run(["userdel", user], ignore_error=True)

    def reload_systemd(self):
        print("Reloading systemd...")
        self.run(["systemctl", "daemon-reload"], ignore_error=True)

    def remove(self):
        print("===== FULL HPC RESET START =====")

        self.check_root()

        pkg_manager = self.detect_package_manager()

        self.stop_services()

        if pkg_manager:
            self.remove_packages(pkg_manager)
        else:
            print("Package manager not detected. Skipping package removal.")

        self.remove_directories()
        self.remove_users()
        self.reload_systemd()

        print("===== FULL HPC RESET COMPLETE =====")
        print("You may reboot now.")

if __name__ == "__main__":
    remover = SlurmRemover()
    remover.remove()