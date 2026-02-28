import subprocess
import shutil


class SlurmPreprocessor:

    # -----------------------------
    # Utility Functions
    # -----------------------------

    def command_exists(self, command):
        """Check if a command exists in PATH"""
        return shutil.which(command) is not None

    def is_service_active(self, service):
        """Check if a systemd service is active"""
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", service],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0

    def service_exists(self, service):
        """Check if a systemd service exists"""
        result = subprocess.run(
            ["systemctl", "list-unit-files"],
            capture_output=True,
            text=True
        )
        return service in result.stdout

    # -----------------------------
    # Broken Runtime Cleanup
    # -----------------------------

    def clean_broken_state(self):
        print("⚠ Detected broken Slurm environment.")
        print("Cleaning runtime leftovers (not uninstalling packages)...")

        # Stop services safely (ignore errors)
        subprocess.run(["sudo", "systemctl", "stop", "slurmctld.service"],
                       stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "systemctl", "stop", "slurmd.service"],
                       stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "systemctl", "stop", "munge.service"],
                       stderr=subprocess.DEVNULL)

        # Remove stale runtime directories only
        subprocess.run(["sudo", "rm", "-rf", "/var/spool/slurm"],
                       stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "rm", "-rf", "/var/run/munge"],
                       stderr=subprocess.DEVNULL)

        print("✔ Broken runtime cleaned successfully.")

    # -----------------------------
    # Main Preprocess Logic
    # -----------------------------

    def check(self):
        print("===== CHECKING SLURM STATUS =====")

        # Case 1: Slurm command not found
        if not self.command_exists("sinfo"):
            print("Slurm not installed.")
            return "not_installed"

        print("Slurm command found.")

        # Case 2: Service file missing
        if not self.service_exists("slurmctld.service"):
            print("Slurm partially installed (service file missing).")
            self.clean_broken_state()
            return "broken_cleaned"

        # Case 3: Munge not active
        if not self.is_service_active("munge.service"):
            print("Munge service not running.")
            self.clean_broken_state()
            return "broken_cleaned"

        # Case 4: Slurm fully active
        if self.is_service_active("slurmctld.service"):
            print("✔ Slurm is running properly.")
            return "installed"

        # Case 5: Installed but inactive
        print("Slurm installed but not active.")
        self.clean_broken_state()
        return "broken_cleaned"
    
if __name__ == "__main__":
    preprocessor = SlurmPreprocessor()
    status = preprocessor.check()
    print(f"Detected status: {status}")
