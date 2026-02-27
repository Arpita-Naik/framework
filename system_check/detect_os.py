import os


class OSDetector:
    def __init__(self):
        self.os_name = None
        self.os_version = None
        self.os_id = None
        self.package_manager = None

    def detect(self):
        print("Detecting Operating System...")

        if not os.path.exists("/etc/os-release"):
            raise Exception("Cannot detect OS. /etc/os-release not found.")

        with open("/etc/os-release") as f:
            lines = f.readlines()

        os_info = {}
        for line in lines:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os_info[key] = value.strip('"')

        self.os_name = os_info.get("NAME")
        self.os_version = os_info.get("VERSION_ID")
        self.os_id = os_info.get("ID")

        print(f"OS Name: {self.os_name}")
        print(f"OS Version: {self.os_version}")

        if self.os_id in ["ubuntu", "debian"]:
            self.package_manager = "apt"
        elif self.os_id in ["centos", "rhel", "fedora", "rocky", "almalinux"]:
            # Prefer dnf, fallback handled later if needed
            self.package_manager = "dnf"
        else:
            raise Exception("Unsupported OS")

        print(f"Package Manager: {self.package_manager}")

        return {
            "os_name": self.os_name,
            "os_version": self.os_version,
            "os_id": self.os_id,
            "package_manager": self.package_manager
        }