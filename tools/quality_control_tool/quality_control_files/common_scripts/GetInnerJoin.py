"""
This script:
    Makes a file with the innerjoin of SNPs between the breed database and the input file
"""

import csv
import sys


def split_and_strip(line, delimiter='\t'):
    """
    :param line: row of input file
    :param delimiter: the delimiter to use
    :return: stripped and split row
    """
    split_line = line.strip().split(delimiter)
    return split_line


def get_snps(file):
    """
    :param file: input file
    :return: set with SNP ids in the input file
    """
    snp_set = set()
    for line in file:
        line = split_and_strip(line)
        snp_set.add(line[1])  # line[1] is SNP id
    return snp_set


def get_innerjoin(database_set, new_file_set, writer):
    """
    :param database_set: set with SNP ids in breed database
    :param new_file_set: set with SNP ids in new bim file
    :param writer: which writer to use
    """
    inner_join = list(database_set & new_file_set)
    for snp in inner_join:
        writer.writerow([snp])


def main():
    # input files
    breed_database = sys.argv[1]  # .bim plink file from breed database
    new_bim_file = sys.argv[2]  # .bim plink file from input SNP dataset
    # output files
    innerjoin_file = sys.argv[3]

    with open(breed_database, mode="r") as breed_database, \
            open(new_bim_file, mode="r") as new_bim_file, \
            open(innerjoin_file, "w", newline='') as NewFileInnerjoin:
        writer = csv.writer(NewFileInnerjoin, delimiter='\t')

        database_set = get_snps(breed_database)
        new_file_set = get_snps(new_bim_file)
        get_innerjoin(database_set, new_file_set, writer)


main()
