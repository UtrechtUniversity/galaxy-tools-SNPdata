"""
This script:
Makes a phylogenetic tree newick file from a distance matrix
Makes an annotation file for which samples need to be colored in the tree, to use in ITOL webpage
If this script is run on Git bash, a png image of the tree is made

"""
from ete3 import Tree, TreeStyle, NodeStyle
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceMatrix
from Bio.Phylo.TreeConstruction import DistanceTreeConstructor
import time
import sys
import csv
# get the start time
st = time.time()


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


def make_tree_newick(sample_names, distances):
    """
    :param sample_names: list with sample IDs
    :param distances: list with distances between samples
    """
    distance_matrix = DistanceMatrix(sample_names, distances)
    constructor = DistanceTreeConstructor()
    tree = constructor.nj(distance_matrix)  # nj = neighbourjoin method
    outgroup = [{'name': 'Coyote_350'}, {'name': 'Coyote_349'}, {'name': 'Coyote_348'}, {'name': 'Coyote_347'}]
    tree.root_with_outgroup(*outgroup)
    Phylo.write(tree, sys.argv[3], 'newick')


def get_new_dogs():
    """
    :return: list with sample ids in .fam file
    """
    new_dogs_file = sys.argv[4]  # .fam file
    with open(new_dogs_file, mode="r") as new_data:
        dogs = []
        # make a list with sample IDs in .fam file
        for line in new_data:
            line = split_and_strip(line)
            dogs.append(line[1])
    return dogs


def make_annotations_file(dogs, writer):
    """
    :param dogs: list with sample IDs of new dogs
    :param writer: which writer to use
    """
    writer.writerow(["TREE_COLORS"])
    writer.writerow(["SEPARATOR", "SPACE"])
    writer.writerow(["DATA"])
    writer.writerow(["#NODE_ID", "TYPE", "COLOR"])
    for dog in dogs:
        writer.writerow([dog, "range", "#00bfff", "new_dogs"])


def main():
    # input files
    dist_matrix = sys.argv[1]  # plink .mdist file (distance matrix)
    samples = sys.argv[2]  # plink .mdist.id file (sample ids for distance matrix)
    new_dogs_file = sys.argv[4]  # .fam file
    # output files
    annotation_file = sys.argv[6]
    with open(dist_matrix, mode="r") as dist_matrix, \
            open(samples, mode="r") as samples,  \
            open(annotation_file, "w", newline='') as NewFileAn:
        writer = csv.writer(NewFileAn, delimiter=' ')

        distances, sample_names = get_distances_and_sample_ids(dist_matrix, samples)
        make_tree_newick(sample_names, distances)
        dogs = get_new_dogs()  # make list with sample ids of new dogs
        make_annotations_file(dogs, writer)  # make annotations file
        return dogs


main()


et = time.time()  # get the end time

elapsed_time = et - st
print('Writing tree execution time:', elapsed_time, 'seconds or ', elapsed_time/60, ' minutes')

st2 = time.time()


def main2():
    print("Using python script MakeTree.py to create a png image of the phylogenetic tree")
    t = Tree(sys.argv[3], format=1)
    dogs = get_new_dogs()  # make list with sample ids of new dogs

    # set style of nodes of new dogs
    def layout_nodes_new_dogs(node):
        if node.name in dogs:
            node.img_style["fgcolor"] = "red"
            node.img_style["size"] = 10
            node.img_style["bgcolor"] = "#00bfff"  # blue

    # set style of all leaf nodes
    for node in t.traverse():
        node_style = NodeStyle()
        node_style['vt_line_width'] = 3
        node_style['hz_line_width'] = 3
        if node.is_leaf():
            node_style['size'] = 8
        node.set_style(node_style)

    # set style for tree
    circular_style = TreeStyle()
    circular_style.mode = 'c'
    circular_style.root_opening_factor = 0.5
    circular_style.min_leaf_separation = 4
    circular_style.allow_face_overlap = True
    circular_style.layout_fn = layout_nodes_new_dogs
    circular_style.branch_vertical_margin = 0.1

    t.render(sys.argv[5], w=1200, units='mm', tree_style=circular_style,  dpi=200)


if sys.argv[7] == "gitbash":  # if gitbash is used, make png tree file.
    main2()
    # get the end time
    et2 = time.time()
    # get the execution time
    elapsed_time2 = et2 - st2
    print('Making tree picture:', elapsed_time2, 'seconds or ', elapsed_time2/60, ' minutes')



