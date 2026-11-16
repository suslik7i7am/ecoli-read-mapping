import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
DATASET_INFO = RESULTS / "dataset_info.tsv"


def read_dataset_info():
    values = {}
    with DATASET_INFO.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            values[row["metric"]] = int(row["value"])
    return values


def alignment_metrics(bam):
    process = subprocess.Popen(
        ["samtools", "view", str(bam)],
        stdout=subprocess.PIPE,
        text=True,
    )
    mapped_primary = 0
    mapq_sum = 0
    mapq_count = 0
    mapq_unavailable = 0
    nm_sum = 0
    nm_count = 0
    multimapped_names = set()

    for line in process.stdout:
        fields = line.rstrip("\n").split("\t")
        flag = int(fields[1])
        if flag & 0x100 and not flag & 0x800:
            multimapped_names.add(fields[0])
        if flag & (0x4 | 0x100 | 0x800):
            continue
        mapped_primary += 1
        mapq = int(fields[4])
        if mapq == 255:
            mapq_unavailable += 1
        else:
            mapq_sum += mapq
            mapq_count += 1
        for tag in fields[11:]:
            if tag.startswith("NM:i:"):
                nm_sum += int(tag[5:])
                nm_count += 1
                break

    if process.wait() != 0:
        raise RuntimeError(f"samtools view failed for {bam}")

    multi = len(multimapped_names)
    return {
        "mapped_reads": mapped_primary,
        "unique_mapped_reads": mapped_primary - multi,
        "multi_mapped_reads": multi,
        "mean_mapq": mapq_sum / mapq_count if mapq_count else None,
        "mapq_defined_reads": mapq_count,
        "mapq_unavailable_reads": mapq_unavailable,
        "mean_edit_distance": nm_sum / nm_count if nm_count else 0.0,
    }


def coverage_metrics(bam):
    command = [
        "samtools",
        "coverage",
        "--ff",
        "UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY",
        str(bam),
    ]
    output = subprocess.check_output(command, text=True)
    reference_bases = 0
    covered_bases = 0
    depth_sum = 0.0
    for line in output.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        length = int(fields[2]) - int(fields[1]) + 1
        reference_bases += length
        covered_bases += int(fields[4])
        depth_sum += float(fields[6]) * length
    return {
        "genome_coverage_percent": 100.0 * covered_bases / reference_bases,
        "mean_depth": depth_sum / reference_bases,
    }


def analyse(name, bam, runtime_file, total_reads):
    values = alignment_metrics(bam)
    values.update(coverage_metrics(bam))
    values["aligner"] = name
    values["total_reads"] = total_reads
    values["mapping_rate_percent"] = 100.0 * values["mapped_reads"] / total_reads
    values["unique_mapped_percent"] = (
        100.0 * values["unique_mapped_reads"] / total_reads
    )
    values["multi_mapped_percent"] = (
        100.0 * values["multi_mapped_reads"] / total_reads
    )
    values["runtime_seconds"] = float(runtime_file.read_text().strip())
    return values


def main():
    total_reads = read_dataset_info()["reads"]
    candidates = [
        (
            "Bowtie2",
            RESULTS / "bowtie2.sorted.bam",
            RESULTS / "bowtie2_runtime_seconds.txt",
        ),
        (
            "BWA-MEM2",
            RESULTS / "bwa_mem2.sorted.bam",
            RESULTS / "bwa_mem2_runtime_seconds.txt",
        ),
    ]
    rows = [
        analyse(name, bam, runtime_file, total_reads)
        for name, bam, runtime_file in candidates
        if bam.is_file() and runtime_file.is_file()
    ]
    if not rows:
        raise FileNotFoundError("No completed BAM and runtime files were found")
    columns = [
        "aligner",
        "total_reads",
        "mapped_reads",
        "mapping_rate_percent",
        "unique_mapped_reads",
        "unique_mapped_percent",
        "multi_mapped_reads",
        "multi_mapped_percent",
        "mean_mapq",
        "mapq_defined_reads",
        "mapq_unavailable_reads",
        "mean_edit_distance",
        "genome_coverage_percent",
        "mean_depth",
        "runtime_seconds",
    ]
    output_path = RESULTS / "summary.tsv"
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        f"{row[key]:.4f}"
                        if isinstance(row[key], float)
                        else "NA" if row[key] is None else row[key]
                    )
                    for key in columns
                }
            )
    print(output_path.read_text(), end="")


if __name__ == "__main__":
    main()

