"""
This script for MyDogDNA data:
makes a new 'SNPsToExclude' file with:
    unknown SNP names
    snps that are on SNPsToExcludeMerge.list
    this file can be used in the --exclude in plink
creates a new bim file with these changes:
    removes the rs numbers from the snp names
    makes the SNP names uppercase
creates a new fam file with these changes:
    if family id is 0, change this value to individual id
input file is bim file
"""

import csv
import re
import sys
import time
# get the start time
st = time.time()


def split_and_strip(line):
    """
    :param line: row of input file
    :return: stripped and split row
    """
    split_line = line.strip().split(' ')
    return split_line


def get_excluded_snps_merge(file):
    """
    :param file: input file
    :return: list with snps that have different locations between arrays
    """
    snps_exclude_merge = []
    for line in file:
        split_line = [line.strip()]
        snps_exclude_merge.append(split_line)
    return snps_exclude_merge


def get_unknown_snps(line, count_unknown, snps_to_exclude):
    """
    :param line: row of the input bim file
    :param count_unknown: counter for how many unknown snps
    :param snps_to_exclude: list with snps to exclude
    :return: line with updated snp id, counts of how many unknown snps, and updated list with snps to exclude
    """
    split_line = line.strip().split("\t")
    if split_line[1].startswith('unknown'):  # split_line[1] is SNP id
        split_line[1] = [split_line[1].upper()]
        count_unknown += 1
        if split_line[1] not in snps_to_exclude:
            snps_to_exclude.append(split_line[1])
    return split_line, count_unknown, snps_to_exclude


def remove_rs(line):
    """
    :param line: row of the input bim file
    :return: row with SNP id in uppercase without rs_number
    """
    split_line = line.strip().split("\t")
    split_line[1] = re.sub("_rs.*", "", split_line[1]).upper()  # split_line[1] is SNP id
    return split_line


def change_family_id(line):
    """
    :param line: row of input fam file
    :return: row with the same family id as individual id
    """
    if line[0] == '0':  # if family id is 0, change this to individual id
        line[0] = line[1]
    return line


def get_snps_to_exclude(line, snps_to_exclude, snps_exclude_merge, count_exclude_merge):
    """
    :param line: input row
    :param snps_to_exclude: list with snps to exclude, to which to append new snps
    :param snps_exclude_merge: list with snps that have a different location between arrays
    :param count_exclude_merge: counter for how many snps to exclude because location differs between arrays
    :return: list with snps that have to be excluded
    """
    if line[1] in snps_exclude_merge:  # line[1] is SNP id
        if line[1] not in snps_to_exclude:
            snps_to_exclude.append(line[1])
            count_exclude_merge += 1
    return snps_to_exclude, count_exclude_merge


def main():
    """ Creates the new BIM file and the MDDSNPsToExclude list """
    # input files
    filename_bim = sys.argv[1]  # input plink .bim file
    filename_fam = sys.argv[2]  # input plink .fam file
    tool_directory = sys.argv[5]  # tool path Galaxy
    snps_to_exclude_merge = f'{tool_directory}/convert_files/common_files/SNPsToExcludeMerge.list'  # file with SNPids to exclude when merging files

    # output files
    new_filename_bim = sys.argv[4] + '.bim'
    new_filename_fam = sys.argv[4] + '.fam'
    mdd_snps_to_exclude = sys.argv[3]  # file with a list of SNPs to use in --exclude plink

    with open(filename_bim, mode="r") as DataBim, \
            open(filename_fam, mode="r") as DataFam, \
            open(snps_to_exclude_merge, mode="r") as DataExcludeMerge, \
            open(mdd_snps_to_exclude, "w", newline='') as NewFileExcludedSNPs, \
            open(new_filename_bim, "w", newline='') as NewFileBim, \
            open(new_filename_fam, "w", newline='') as NewFileFam:
        writer_bim = csv.writer(NewFileBim, delimiter='\t')
        writer_fam = csv.writer(NewFileFam, delimiter='\t')
        writer_exclude = csv.writer(NewFileExcludedSNPs, delimiter='\t')

        count_unknown = 0
        count_exclude = 0
        count_exclude_merge = 0
        snps_to_exclude = []
        # put the SNPs on the SNPsToExcludeMerge.list in a list
        new_line, snps_exclude_merge = get_excluded_snps_merge(DataExcludeMerge)

        for line in DataBim:
            # remove the _rs number in SNP id name and write new bim file
            new_line = remove_rs(line)
            writer_bim.writerow(new_line)
            # write the unknown SNPs to the new file with SNPs that have to be excluded
            line, count_unknown, snps_to_exclude = get_unknown_snps(line, count_unknown, snps_to_exclude)
            snps_to_exclude, count_exclude_merge = get_snps_to_exclude(line, snps_to_exclude, snps_exclude_merge, count_exclude_merge)

        # if family id is 0, change this value to the individual id
        for line in DataFam:
            line = split_and_strip(line)
            line = change_family_id(line)
            writer_fam.writerow(line)

        for snp in snps_to_exclude:
            writer_exclude.writerow(snp)

        print("Number of SNPs to be deleted: ", len(snps_to_exclude))
        print("\t- Number of Unknown SNPs: ", count_unknown)
        print("\t- Number of SNPs of which no correct location is available, or location differs between arrays: ", count_exclude)


main()

# get the end time
et = time.time()
# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')
