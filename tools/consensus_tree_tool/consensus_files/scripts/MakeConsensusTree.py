"""
This script:
Makes a consensus phylogenetic tree newick file from multiple trees
"""
from Bio import Phylo
from Bio.Phylo.Consensus import *
import sys

# Load the 100 trees
trees = []
for i in range(int(sys.argv[1])):  # for i in number of iterations
    filename = sys.argv[2] + f'{i + 1}.newick'
    tree = Phylo.read(filename, 'newick')  # read tree from newick file
    trees.append(tree)  # append trees

# Create a consensus tree
consensus_tree = majority_consensus(trees, 0.5)

# Save the consensus tree to a newick file
Phylo.write(consensus_tree, sys.argv[3], 'newick')