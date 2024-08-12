"""
This script:
    checks if there are duplicate IDs between the two input files
    changes duplicate ID of first file to a unique ID
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
    """""
    # make list of sample IDs
    list_ids = []
    for line in file:
        line = split_and_strip(line)
        list_ids.append(line[1])  # line[1] = sample ID
    return list_ids


def compare_ids(ids_file1, ids_database):
    """
    :param ids_file1: list with sample ids of first input file
    :param ids_database: list with sample ids of second input file
    :return: list with duplicate ids
    """
    # check if sample IDs of first file are present in list of IDs of second input file
    duplicate_ids = []
    for sample_id in ids_file1:
        if sample_id in ids_database:
            duplicate_ids.append(sample_id)
    return duplicate_ids


def report_duplicates(duplicate_ids, ids_file1, ids_database, writer_fam, file_1):
    """
    :param duplicate_ids: list with duplicate ids
    :param ids_file1: list with sample ids of first input file
    :param ids_database: list with sample ids of second input file
    :param writer_fam: which writer to use
    :param file_1: name of first input file
    """
    if len(duplicate_ids) != 0:  # check if duplicate ids are found (list not empty)
        print("\nDuplicate sample IDs found (present in both files):")
        for sample_id in duplicate_ids:
            print(sample_id)
        print("\nThese sample IDs from", file_1, "are assigned a unique ID to be able to continue the duplicate check:")
        for index, sample_id in enumerate(ids_file1):
            dup_number = 1
            unique_ids = False
            if sample_id in duplicate_ids:
                ids_changed = [sample_id]
                "while duplicate sample id in first file is not unique (still duplicate name), change sample id" \
                    "sample id is changed to e.g. dog1 --> dog1_dupid1. Again is checked if this new name is unique." \
                    "if name still not unique, increase dupid number by 1 --> dog1_dupid2. etc."
                while not unique_ids:
                    sample_dup = sample_id + '_dupid' + str(dup_number)
                    if sample_dup in ids_database:
                        unique_ids = False
                        dup_number += 1
                    else:  # if new sample id is unique, use this id in .fam file and print new name to terminal
                        unique_ids = True
                        ids_file1[index] = sample_dup
                        ids_changed += [sample_dup]
                        print(ids_changed[0], ids_changed[1])
        print("\n")
    for sample in ids_file1:
        writer_fam.writerow([sample, sample, '0', '0', '0', '-9'])


def main():
    """
    Checks if there are duplicate IDs between the two input files
    Changes duplicate ID of first file to a unique ID
    """
    # input files
    file_1 = sys.argv[1]  # input .fam file
    file_database = sys.argv[2]  # .fam file of database

    # Output files
    new_filename_fam = sys.argv[3]

    with open(file_1, mode="r") as Data1, \
            open(file_database, mode="r") as Database, \
            open(new_filename_fam, "w", newline='') as NewFileFAM:
        writer_fam = csv.writer(NewFileFAM, delimiter=' ')
        # make lists of sample ids
        ids_file1 = get_sample_ids(Data1)
        ids_database = get_sample_ids(Database)
        # check if duplicate ids between the two lists are present
        duplicate_ids = compare_ids(ids_file1, ids_database)
        # report duplicate ids, make duplicate ids unique and update .fam file
        report_duplicates(duplicate_ids, ids_file1, ids_database, writer_fam, file_1)


main()
