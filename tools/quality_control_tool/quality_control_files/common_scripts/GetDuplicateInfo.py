"""
This script:
Makes a new txt file with the number of snps per duplicate sample, and their kinship
"""
import sys
import csv


def split_and_strip(line, delimiter=None):
    """
    :param line: row of input file
    :param delimiter: the delimiter to use
    :return: stripped and split row
    """
    split_line = line.strip().split(delimiter)
    return split_line


def get_snpcount(file):
    """
    :param file: input file
    :return: number of successful snps per sample
    """
    snpcount = {}
    for index, line in enumerate(file):
        if index == 0:
            continue
        line = split_and_strip(line)
        # calculate number of snps: nr total snps - nr of failed snps
        snpcount[line[1]] = int(line[3]) - int(line[2])  # line[1] = sample id
    return snpcount


def make_summary(file, snpcount, writer):
    """
    :param file: input file
    :param snpcount: number of successful snps per sample
    :param writer: which writer to use
    """
    header = ['Family_ID1', 'Sample_ID1', 'SNP_count_ID1', 'Family_ID2', 'Sample_ID2', 'SNP_count_ID2', 'Kinship_score',
              'Sample_ID_most_SNPs']
    writer.writerow(header)
    for line in file:
        line = split_and_strip(line)
        # summary = Family_ID1, Sample_ID1, SNP_count_ID1, Family_ID2,
        # Sample_ID2, SNP_count_ID2, Kinship_score, Sample_ID_most_SNPs
        summary = [line[0], line[1], snpcount[line[1]], line[2], line[3], snpcount[line[3]], line[4]]
        # compare snp counts between each duplicate and show which sample has highest snp count
        if snpcount[line[1]] > snpcount[line[3]]:
            summary = [line[0], line[1], snpcount[line[1]], line[2], line[3], snpcount[line[3]], line[4], line[1]]
        elif snpcount[line[1]] < snpcount[line[3]]:
            summary = [line[0], line[1], snpcount[line[1]], line[2], line[3], snpcount[line[3]], line[4], line[3]]
        elif snpcount[line[1]] == snpcount[line[3]]:
            summary = [line[0], line[1], snpcount[line[1]], line[2], line[3], snpcount[line[3]], line[4],
                       'identical_snp_count']
        writer.writerow(summary)


def main():
    """ Makes a new txt file with the number of snps per duplicate sample, and their kinship
    """
    # input files
    file_dup = sys.argv[1]  # text file with kinship scores
    file_missing = sys.argv[2]  # plink .smiss file
    # Output files
    new_filename = sys.argv[3]

    with open(file_missing, mode="r") as DataMissing, \
            open(file_dup, mode="r") as DataDup, \
            open(new_filename, "w", newline='') as NewFile:
        writer = csv.writer(NewFile, delimiter='\t')
        snpcount = get_snpcount(DataMissing)
        make_summary(DataDup, snpcount, writer)


main()
