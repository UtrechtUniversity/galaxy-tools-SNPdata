"""
This script:
Makes a phylogenetic tree newick file from a distance matrix
"""
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceMatrix
from Bio.Phylo.TreeConstruction import DistanceTreeConstructor
import sys


def split_and_strip(line):
    """
    :param line: row of input file
    :return: stripped and split row
    """
    split_line = line.strip().split()
    return split_line


def get_distances_and_sample_ids(dist_matrix, samples):
    """
    :param dist_matrix: distance matrix file
    :param samples: file with sample IDs
    :return: list of distance matrix distances and a list with sample IDs
    """
    distances = [[0]]  # first line in distance matrix is 0
    # make a list of the distance matrix, in which each line ends with 0
    for line in dist_matrix:
        line = split_and_strip(line)
        line = [float(i) for i in line]
        line += [0]  # make line end with 0
        distances.append(line)
    # make a list of the sample IDs
    sample_names = []
    for line in samples:
        line = split_and_strip(line)
        sample_names.append(line[1])
    return distances, sample_names


def make_tree_newick(sample_names, distances, outgroup):
    """
    :param sample_names: list with sample IDs
    :param outgroup: sample id of outgroup sample
    :param distances: list with distances between samples
    """
    distance_matrix = DistanceMatrix(sample_names, distances)
    constructor = DistanceTreeConstructor()
    tree = constructor.nj(distance_matrix)  # nj = neighbourjoin method
    tree.root_with_outgroup({'name': outgroup})
    Phylo.write(tree, sys.argv[3], 'newick')


def main():
    """
    Makes tree of distance matrices and writes trees to newick file
    """
    # input files
    dist_matrix = sys.argv[1]  # plink .mdist file (distance matrix)
    samples = sys.argv[2]  # plink .mdist.id file (sample ids for distance matrix)
    outgroup = sys.argv[4]  # outgroup sample ID

    with open(dist_matrix, mode="r") as dist_matrix, \
            open(samples, mode="r") as samples:

        distances, sample_names = get_distances_and_sample_ids(dist_matrix, samples)
        make_tree_newick(sample_names, distances, outgroup)


main()

