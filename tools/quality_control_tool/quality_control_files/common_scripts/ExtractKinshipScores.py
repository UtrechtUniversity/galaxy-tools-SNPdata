"""
This script:
    Extract the kinship scores out of the .kin0 file for samples between the two files, and
    not extract the kinship scores which are between samples within the first input file
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


def get_sample_ids(file):
    """
    :param file: input file
    :return: list with sample ids
    """
    list_ids = []
    for line in file:
        line = split_and_strip(line)
        list_ids.append(line[1])  # line[1] = sample ID
    return list_ids


def extract_ids(ids_file1, Kinship, writer):
    """
    :param ids_file1: list with sample ids of first file
    :param Kinship: .kin0 file with kinship scores
    :param writer: which writer to use
    """
    for line in Kinship:
        line = split_and_strip(line)
        # check if both samples of kinship score in .kin0 file are in the first input file
        if line[1] in ids_file1 and line[3] in ids_file1:  # line[1] and [3] are sample IDs
            continue
        # if the both samples are not in first input file, these are scores between samples of the two files
        else:  # write only kinship scores between samples of the two input files, to new file
            writer.writerow(line)


def main():
    """
    Extract the kinship scores out of the .kin0 file for samples between the two SNP files, and
    not extract the kinship scores which are between samples within the first input file
    """
    # input files
    file_1 = sys.argv[1]  # input plink .fam file
    file_kinship = sys.argv[2]  # input plink .kin0 file

    # Output files
    new_filename_kinship = sys.argv[3]

    with open(file_1, mode="r") as Data1, \
            open(file_kinship, mode="r") as Kinship, \
            open(new_filename_kinship, "w", newline='') as NewFile:
        writer = csv.writer(NewFile, delimiter=' ')
        ids_file1 = get_sample_ids(Data1)
        extract_ids(ids_file1, Kinship, writer)


main()
