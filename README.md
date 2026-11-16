# E. coli DNA read mapping

This project compares Bowtie2 and BWA-MEM2 on the same complete single-end
sequencing dataset and the same *Escherichia coli* K-12 MG1655 reference.
SAMtools is used to create, sort, index, validate, and analyse BAM files.

## Dataset

- Reference: [GCF_000005845.2 ASM584v2](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz)
- Reads: [ERR022075_1.fastq.gz](https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR022/ERR022075/ERR022075_1.fastq.gz)
- Input mode: single-end
- Reads: 22,720,100 reads of 100 bases
- Reference: one 4,641,652-base chromosome, `NC_000913.3`

## Software and environment

The final experiment was performed in Ubuntu 26.04.1 under WSL2 with eight
alignment threads and two BAM-sorting threads.

- Bowtie2 2.5.4
- BWA-MEM2 2.2.1
- SAMtools 1.22.1
- Python 3
- Python 3 and `sudo`

On Windows, WSL can be installed from an Administrator PowerShell window:

```powershell
wsl --install
```

The project is available inside WSL at:

```text
/mnt/c/algorithm_engeniring/bacteria
```

## Reproduce the experiment

Run from the repository root:

```bash
python3 scripts/install_tools.py
python3 scripts/prepare_data.py
python3 scripts/run_mapping.py
python3 scripts/collect_stats.py
```

Thread counts can be changed without editing the script:

```bash
THREADS=4 SORT_THREADS=2 python3 scripts/run_mapping.py
```

One aligner can be run separately when resuming an experiment:

```bash
ALIGNERS=bowtie2 python3 scripts/run_mapping.py
ALIGNERS=bwa_mem2 python3 scripts/run_mapping.py
```

## Results

Both full-dataset BAM files passed `samtools quickcheck`.

| Metric | Bowtie2 | BWA-MEM2 |
|---|---:|---:|
| Total reads | 22,720,100 | 22,720,100 |
| Mapped reads | 22,564,067 | 22,690,612 |
| Mapping rate (%) | 99.3132 | 99.8702 |
| Unique mapped (%) | 96.4808 | 96.8007 |
| Multi-mapped (%) | 2.8324 | 3.0695 |
| Mean defined MAPQ | 9.4190* | 58.6309 |
| Mean edit distance | 0.3387 | 0.2256 |
| Genome coverage (%) | 99.9841 | 99.9849 |
| Mean depth | 486.1110x | 486.2230x |
| Runtime (s) | 346.06 | 202.63 |

*Bowtie2 documents MAPQ as not meaningful in `-k` mode. It emitted MAPQ 255
for 21,920,538 primary alignments. The displayed value is calculated only from
the 643,529 primary alignments with defined MAPQ and is not directly comparable
with the BWA-MEM2 whole-dataset mean.

## Repository contents

- `scripts/install_tools.py`: installs required programs.
- `scripts/prepare_data.py`: downloads, validates, and counts input data.
- `scripts/run_mapping.py`: builds indices, runs both aligners, and validates BAM.
- `scripts/collect_stats.py`: calculates the comparison table.
- `results/summary.tsv`: machine-readable final results.
- `report.md`: final English report.

Large FASTQ, FASTA, BAM, index, temporary, and downloaded-tool files are
excluded by `.gitignore`.
