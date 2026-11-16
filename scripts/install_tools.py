import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT_DIR / "tools"
BWA_VERSION = "2.2.1"
BWA_DIR = TOOLS_DIR / f"bwa-mem2-{BWA_VERSION}_x64-linux"
BWA_URL = (
    "https://github.com/bwa-mem2/bwa-mem2/releases/download/"
    f"v{BWA_VERSION}/bwa-mem2-{BWA_VERSION}_x64-linux.tar.bz2"
)


def run(command):
    subprocess.run([str(item) for item in command], check=True)


def main():
    privilege = [] if os.geteuid() == 0 else ["sudo"]
    run(privilege + ["apt-get", "update"])
    run(
        privilege
        + [
            "apt-get",
            "install",
            "-y",
            "bowtie2",
            "samtools",
            "curl",
            "bzip2",
            "time",
            "python3",
        ]
    )

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    bwa_executable = BWA_DIR / "bwa-mem2"
    if not bwa_executable.is_file():
        with tempfile.NamedTemporaryFile(suffix=".tar.bz2", delete=False) as handle:
            archive = Path(handle.name)
        try:
            urllib.request.urlretrieve(BWA_URL, archive)
            with tarfile.open(archive, "r:bz2") as bundle:
                bundle.extractall(TOOLS_DIR, filter="data")
        finally:
            archive.unlink(missing_ok=True)

    run(["bowtie2", "--version"])
    run(["samtools", "--version"])
    run([bwa_executable, "version"])


if __name__ == "__main__":
    main()
