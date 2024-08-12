"""
This script:
Reformats the distance matrix, so it can be used by the PHYLIP package. A new file with this new format is written.
The phylip format does not allow for sample IDs longer than 10 characters and wants a specific format for the IDs,
so the sample ids are recoded to a temporary id. This is written to a file, so they can be reversed later.
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


def make_temp_ids(file, writer):
    """
    :param file: input file (.mdist.id file)
    :param writer: which writer to use
    :return: a list with the new temporary ids and the number of total samples
    """
    new_ids = []
    for index, line in enumerate(file):
        line = split_and_strip(line)
        index += 1
        zeros = 8 - len(str(index))  # calculate how many zero's should be added to sample ID
        temp_id = 'S'  # the new id starts with an S
        for zero in range(zeros):
            temp_id += '0'  # add zero's to new id, so like: S000000
        new_temp_id = temp_id + str(index)  # add the index number to the id, so like S00000004
        new_ids.append(new_temp_id)
        writer.writerow([line[1], new_temp_id])  # write a file with the original and new IDs
    number_samples = len(new_ids)
    return new_ids, number_samples


def reformat_dist(file, writer, number_samples, new_ids):
    """
    :param file: input .mdist file (distance matrix)
    :param writer: which writer to use
    :param number_samples: number of total samples in distance matrix file
    :param new_ids: list with the new temporary sample ids
    """
    for index_file, line in enumerate(file):
        if index_file == 0:
            writer.writerow([number_samples])  # print the number of samples on row 1 in the new reformatted matrix file
        line = split_and_strip(line)
        # changing the distance values to make them all the same length (otherwise phylip gives error)
        for index, number in enumerate(line):
            if '.' not in number:
                number += '.0'
            missing_zeros = 9 - len(number)
            for zero in range(missing_zeros):
                number += '0'
            line[index] = number
        new_line = [new_ids[index_file]] + line
        writer.writerow(new_line)


def main():
    # input files
    distance_matrix = sys.argv[1] + f".mdist"  # plink .mdist file
    distance_matrix_ids = sys.argv[1] + f".mdist.id"  # plink .mdist.id file
    # output files
    new_file = sys.argv[2]
    new_file_ids = sys.argv[3]

    with open(new_file, "w", newline='') as NewFile, \
            open(distance_matrix_ids, mode="r") as DistID, \
            open(new_file_ids, "w", newline='') as NewFileIDs, \
            open(distance_matrix, mode="r") as Dist:
        writer = csv.writer(NewFile, delimiter=' ')
        writer_ids = csv.writer(NewFileIDs, delimiter=' ')
        new_ids, number_samples = make_temp_ids(DistID, writer_ids)  # make temporary sample ids
        reformat_dist(Dist, writer, number_samples, new_ids)  # reformat the distance matrix and write to new file


main()
