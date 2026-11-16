import csv
import gzip
import shutil
import subprocess
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"
REF_GZ = DATA_DIR / "GCF_000005845.2_ASM584v2_genomic.fna.gz"
REF = DATA_DIR / "GCF_000005845.2_ASM584v2_genomic.fna"
FASTQ = DATA_DIR / "ERR022075_1.fastq.gz"
REF_URL = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz"
FASTQ_URL = "https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR022/ERR022075/ERR022075_1.fastq.gz"


def download_if_missing(url, output):
    if output.is_file() and output.stat().st_size > 0:
        print(f"Using existing {output}")
        return
    partial = output.with_name(output.name + ".part")
    start = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(url)
    if start:
        request.add_header("Range", f"bytes={start}-")
    with urllib.request.urlopen(request) as response:
        append = start > 0 and response.status == 206
        mode = "ab" if append else "wb"
        with partial.open(mode) as handle:
            shutil.copyfileobj(response, handle, length=8 * 1024 * 1024)
    partial.replace(output)


def check_gzip(path):
    with gzip.open(path, "rb") as handle:
        while handle.read(8 * 1024 * 1024):
            pass


def count_reads(path):
    lines = 0
    with gzip.open(path, "rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            lines += chunk.count(b"\n")
    if lines % 4:
        raise ValueError("FASTQ line count is not divisible by four")
    return lines // 4


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    download_if_missing(REF_URL, REF_GZ)
    download_if_missing(FASTQ_URL, FASTQ)

    print("Checking gzip integrity...")
    check_gzip(REF_GZ)
    check_gzip(FASTQ)

    if not REF.is_file() or REF.stat().st_size == 0:
        temporary = REF.with_name(REF.name + ".tmp")
        with gzip.open(REF_GZ, "rb") as source, temporary.open("wb") as target:
            shutil.copyfileobj(source, target)
        temporary.replace(REF)

    subprocess.run(["samtools", "faidx", str(REF)], check=True)
    reads = count_reads(FASTQ)
    with Path(str(REF) + ".fai").open() as handle:
        reference_bases = sum(int(line.split("\t")[1]) for line in handle)

    with (RESULTS_DIR / "dataset_info.tsv").open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["reads", reads])
        writer.writerow(["reference_bases", reference_bases])

    print(f"Reads: {reads}")
    print(f"Reference bases: {reference_bases}")


if __name__ == "__main__":
    main()
