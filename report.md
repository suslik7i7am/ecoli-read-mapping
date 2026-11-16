# E. coli Read Mapping

## Dataset

- Reference: *E. coli* K-12 MG1655, NC_000913.3, 4,641,652 bp
- Reads: ERR022075_1
- Input: 22,720,100 single-end reads, 100 bp each

## Algorithms

- Bowtie2 2.5.4 with `--very-sensitive -k 2`
- BWA-MEM2 2.2.1 with `-a`
- SAMtools 1.22.1 for BAM sorting, indexing, validation, and coverage

Both aligners processed the complete FASTQ file with eight threads. Secondary
alignments were used to identify multi-mapped reads. Both resulting BAM files
passed `samtools quickcheck`.

## Results

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

*Bowtie2 MAPQ is not meaningful in `-k` mode. MAPQ 255 was excluded; 9.4190
is the mean for the 643,529 primary alignments with defined MAPQ.

## Conclusion

Both algorithms mapped more than 99% of the reads and covered approximately
99.98% of the reference. BWA-MEM2 mapped more reads, had a lower mean edit
distance, and was approximately 1.71 times faster than Bowtie2.
