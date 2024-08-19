# Galaxy tools for harmonizing and cleaning SNP data 

This repo contains a collection of Galaxy tools developed for the 'Dogs-in-space' project at the Veterinary Science department. These tools are designed to harmonize and clean SNP data, enabling its integration into a larger dataset.

## Tools

__Convert Tool__: To be able to merge genotype files from different platforms, the files must be in a uniform format. This Galaxy tool creates files which are in the same format, ready to be merged.

__Quality Control Tool__: To ensure clean and good quality data, quality control steps need to be performed. This Galaxy tool can be used to perform multiple quality control checks: sample call rate, sex check, duplicate sample check, breed check.

__Consensus Tree Tool__: To get an overview of relations between different dog breeds, they can be placed in a phylogenetic tree. This Galaxy tool makes a consensus tree of a SNP dataset. This tree can be visualized by programs such as ITOL (online tool), dendroscope, figtree etc.

Additional tool for handling an specific Embark .bed file, which is currently incompatible with the other tools:

__Map-Ped to Bed File__: Generates the required files for the Convert Tool (.bed, .bim, and .fam) from .map and .ped files. This Galaxy tool adds an extra step to the workflow, which can be excluded soon.

## License

This project is licensed under the terms of the [MIT License](/LICENSE).
