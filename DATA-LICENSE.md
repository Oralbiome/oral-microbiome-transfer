# Data & Documentation License

The **non-code** contents of this repository — processed data files, figures,
reports, presentation materials, and documentation (`data/`, `reports/`,
`docs/`, `figures/`) — that are **original to this project** are licensed under
the **Creative Commons Attribution 4.0 International (CC-BY-4.0)** license.

You are free to share and adapt this material for any purpose, provided you give
appropriate credit (see `CITATION.cff`). Full text: https://creativecommons.org/licenses/by/4.0/

Source code is licensed separately under the MIT License; see `LICENSE`.

## Third-party data — NOT covered by the above

This project derives features from external datasets that retain their own
licenses and data-use agreements. Redistribution of derived data may be
restricted. In particular:

- **NHANES oral microbiome data (CDC/NCHS).** This project derives its NHANES
  features from the **public-use** DADA2 genus-level tables (`genus_count.txt`)
  plus the standard public NHANES demographic/lab files (`DEMO`, `BMX`, `GHB`
  XPT files). As of **November 2024**, NCHS classifies the phylum→genus
  relative-abundance and read-count tables as **Public Use**
  (https://wwwn.cdc.gov/Nchs/Nhanes/Omp/Default.aspx). This establishes the
  public-use availability of those input tables, not blanket release clearance
  for every derived matrix or linked artifact in this repository. Permitted
  redistribution, applicable terms, attribution and privacy must be reviewed for
  the exact proposed release. Keying a matrix by SEQN does not, by itself,
  establish that every linkage or disclosure is permitted. Do not attempt
  participant re-identification.
  NOTE: the **raw per-sample 16S FASTQ reads** remain **RDC-restricted** and are
  NOT included here; this project never used them for NHANES (raw-read processing
  applies only to the public SRA cohorts). Guidance predating Nov 2024 that calls
  the genus tables "restricted" is superseded. Consult the current CDC/NCHS
  documentation and the project's release checklist for the applicable scope.

- **SRA / ENA cohorts** (China, India, Portugal, etc.) are publicly available
  under their respective BioProject accessions; see `docs/Dataset_Access_Guide.md`.
  Their sample metadata retains the terms of the originating study.

- **HOMD reference database** (`references/`) retains its original license from
  the Human Oral Microbiome Database.

If any third-party term conflicts with CC-BY-4.0, the third-party term governs
that material.
