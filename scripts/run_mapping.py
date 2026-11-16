import os
import shutil
import subprocess
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
REF = ROOT_DIR / "data" / "GCF_000005845.2_ASM584v2_genomic.fna"
FASTQ = ROOT_DIR / "data" / "ERR022075_1.fastq.gz"
RESULTS_DIR = ROOT_DIR / "results"
INDEX_DIR = RESULTS_DIR / "indexes"
THREADS = int(os.environ.get("THREADS", "8"))
SORT_THREADS = int(os.environ.get("SORT_THREADS", "2"))
ALIGNERS = os.environ.get("ALIGNERS", "both")


def require_command(name):
    path = shutil.which(name)
    if path is None:
        raise FileNotFoundError(f"Missing command: {name}")
    return Path(path)


def run(command, stdout=None, stderr=None):
    subprocess.run(
        [str(item) for item in command],
        stdout=stdout,
        stderr=stderr,
        check=True,
    )


def run_alignment(name, command, bam):
    log_path = RESULTS_DIR / f"{name}.log"
    runtime_path = RESULTS_DIR / f"{name}_runtime_seconds.txt"
    with log_path.open("wb") as log:
        start = time.perf_counter()
        aligner = subprocess.Popen(
            [str(item) for item in command],
            stdout=subprocess.PIPE,
            stderr=log,
        )
        sorter = subprocess.Popen(
            [
                "samtools",
                "sort",
                "-@",
                str(SORT_THREADS),
                "-m",
                "512M",
                "-o",
                str(bam),
                "-",
            ],
            stdin=aligner.stdout,
        )
        aligner.stdout.close()
        aligner_code = aligner.wait()
        elapsed = time.perf_counter() - start
        sorter_code = sorter.wait()
    if aligner_code != 0:
        raise subprocess.CalledProcessError(aligner_code, command)
    if sorter_code != 0:
        raise subprocess.CalledProcessError(sorter_code, "samtools sort")
    runtime_path.write_text(f"{elapsed:.2f}\n")
    run(["samtools", "index", "-@", SORT_THREADS, bam])
    run(["samtools", "quickcheck", "-v", bam])
    with (RESULTS_DIR / f"{name}.flagstat.txt").open("wb") as output:
        run(["samtools", "flagstat", "-@", SORT_THREADS, bam], stdout=output)


def find_bwa_mem2():
    installed = shutil.which("bwa-mem2")
    if installed:
        return Path(installed)
    local = ROOT_DIR / "tools" / "bwa-mem2-2.2.1_x64-linux" / "bwa-mem2"
    if local.is_file():
        return local
    raise FileNotFoundError("bwa-mem2 was not found. Run install_tools.py first.")


def main():
    if ALIGNERS not in {"both", "bowtie2", "bwa_mem2"}:
        raise ValueError("ALIGNERS must be both, bowtie2, or bwa_mem2")

    require_command("samtools")
    if ALIGNERS in {"both", "bowtie2"}:
        require_command("bowtie2")
        require_command("bowtie2-build")
    bwa_mem2 = find_bwa_mem2() if ALIGNERS in {"both", "bwa_mem2"} else None

    if not REF.is_file():
        raise FileNotFoundError(f"Missing reference: {REF}")
    if not FASTQ.is_file():
        raise FileNotFoundError(f"Missing reads: {FASTQ}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    bowtie_index = INDEX_DIR / "bowtie2"
    bwa_index = INDEX_DIR / "bwa_mem2"
    bowtie_index.mkdir(parents=True, exist_ok=True)
    bwa_index.mkdir(parents=True, exist_ok=True)
    bowtie_prefix = bowtie_index / "ecoli"
    bwa_prefix = bwa_index / "ecoli"

    if ALIGNERS in {"both", "bowtie2"}:
        small_index = Path(str(bowtie_prefix) + ".1.bt2")
        large_index = Path(str(bowtie_prefix) + ".1.bt2l")
        if not small_index.is_file() and not large_index.is_file():
            with (RESULTS_DIR / "bowtie2_index.log").open("wb") as log:
                run(
                    ["bowtie2-build", "--threads", THREADS, REF, bowtie_prefix],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )

    if ALIGNERS in {"both", "bwa_mem2"}:
        bwa_index_file = Path(str(bwa_prefix) + ".bwt.2bit.64")
        if not bwa_index_file.is_file():
            with (RESULTS_DIR / "bwa_mem2_index.log").open("wb") as log:
                run(
                    [bwa_mem2, "index", "-p", bwa_prefix, REF],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )

    if ALIGNERS in {"both", "bowtie2"}:
        print("Running Bowtie2 on the full FASTQ...")
        run_alignment(
            "bowtie2",
            [
                "bowtie2",
                "--very-sensitive",
                "-k",
                "2",
                "-p",
                THREADS,
                "-x",
                bowtie_prefix,
                "-U",
                FASTQ,
            ],
            RESULTS_DIR / "bowtie2.sorted.bam",
        )

    if ALIGNERS in {"both", "bwa_mem2"}:
        print("Running BWA-MEM2 on the full FASTQ...")
        run_alignment(
            "bwa_mem2",
            [bwa_mem2, "mem", "-a", "-t", THREADS, bwa_prefix, FASTQ],
            RESULTS_DIR / "bwa_mem2.sorted.bam",
        )

    print("Selected BAM files passed samtools quickcheck.")


if __name__ == "__main__":
    main()
