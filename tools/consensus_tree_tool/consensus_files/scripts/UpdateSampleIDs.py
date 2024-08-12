"""
This script:
changes the temporary sample IDs in the newick file to the original sample IDs
"""
import csv
import sys
import re


def split_and_strip(line, delimiter=' '):
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
    :return: dictionary with format: temporary_sample_id : original_sample_id
    """
    samples = {}
    for line in file:
        line = split_and_strip(line)
        samples[line[1]] = line[0]
    return samples


def update_ids(file, samples, writer):
    """
    :param file: input newick file
    :param samples: dictionary with temporary and original sample ids
    :param writer: which writer to use
    """
    for line in file:
        for sample_id in samples.keys():
            line = line.strip()
            if re.search(sample_id, line):
                line = re.sub(sample_id, samples[sample_id], line)  # replace temporary sample id with original id
        writer.writerow([line])


def main():
    """
    This script changes the temporary sample IDs in the newick file to the original sample IDs
    """
    # input files
    sample_ids = sys.argv[1]  # text file with temporary sample IDs and original sample IDs
    newick_file = sys.argv[2]  # newick tree file with the temporary sample IDs
    # output files
    newfile = sys.argv[3]  # newick tree file with the original sample IDs
    with open(sample_ids, mode="r") as sample_ids, \
            open(newick_file, mode="r") as tree_file, \
            open(newfile, "w", newline='') as newfile:
        writer = csv.writer(newfile, delimiter=' ')
        samples = get_sample_ids(sample_ids)  # make dictionary of temporary and original sample ids
        update_ids(tree_file, samples, writer)  # change the temporary sample ids to the original ids and make new file


main()
