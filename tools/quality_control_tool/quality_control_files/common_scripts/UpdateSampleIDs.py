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
        samples[line[1]] = line[0]  # line[1] = temporary sample id, line[0] = original sample id
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


def make_annotations_file(dogs, writer):
    """
    :param dogs: list with sample ids
    :param writer: which writer to use
    """
    writer.writerow(["TREE_COLORS"])
    writer.writerow(["SEPARATOR", "SPACE"])
    writer.writerow(["DATA"])
    writer.writerow(["#NODE_ID", "TYPE", "COLOR"])
    for dog in dogs:
        writer.writerow([dog, "range", "#00bfff", "new_dogs"])


def get_new_dogs(file):
    """
    :param file: input .fam file
    :return: list with sample ids in .fam file
    """
    dogs = []
    for line in file:
        line = line.strip().split()
        dogs.append(line[1])  # line[1] = sample id
    return dogs


def main():
    """
    This script changes the temporary sample IDs in the newick file to the original sample IDs
    """
    # input files
    sample_ids = sys.argv[1]  # text file with temporary ids and original ids
    newick_file = sys.argv[2]  # newick file
    fam_file = sys.argv[4]  # .fam file

    # output files
    newfile = sys.argv[3]
    annotation_file = sys.argv[5]

    with open(sample_ids, mode="r") as sample_ids, \
            open(newick_file, mode="r") as tree_file, \
            open(fam_file, mode="r") as fam_file, \
            open(newfile, "w", newline='') as newfile, \
            open(annotation_file, "w", newline='') as NewFileAn:
        writer = csv.writer(newfile, delimiter=' ')
        writer_anno = csv.writer(NewFileAn, delimiter=' ')
        samples = get_sample_ids(sample_ids)  # make dictionary of temporary and original sample ids
        update_ids(tree_file, samples, writer)  # change the temporary sample ids to the original ids and make new file
        dogs = get_new_dogs(fam_file)  # make a list of new dog sample IDs
        make_annotations_file(dogs, writer_anno)  # write an annotation file


main()
