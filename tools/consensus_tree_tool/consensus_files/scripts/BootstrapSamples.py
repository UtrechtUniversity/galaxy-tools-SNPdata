"""
This script:
    makes x (amount of iterations) new SNP lists by bootstrapping with resampling
    over the SNPs in the original .bim file.
    this resampled list with SNPs is put in a new file.
"""
import numpy as np
import os
import csv
import sys


# Function to perform bootstrapping and write to file
def bootstrap_and_write(original_list, iterations, output_dir):
    """
    :param original_list: list with SNPs in original bim file
    :param iterations: number of times a new snp list has to be made
    :param output_dir: the directory to put the new files in
    """

    for i in range(iterations):
        # Perform bootstrapping (sampling with replacement)
        resampled_list = np.random.choice(original_list, size=len(original_list), replace=True)

        # Write the resampled list to a new list file
        new_filename = os.path.join(output_dir, sys.argv[3] + f"_bootstrap_sample_{i + 1}.list")
        with open(new_filename, "w", newline='') as newfile:
            writer = csv.writer(newfile, delimiter=' ')
            for sample in resampled_list:
                split_line = sample.strip().split(':')
                writer.writerow(split_line)


def split_and_strip(line):
    """
    :param line: row of input file
    :return: stripped and split row
    """
    split_line = line.strip().split('\t')
    return split_line


def main():
    """
    makes x (=number of iterations) new files with a list of SNPs by bootstrapping
    """
    bimfile = sys.argv[1]  # plink .bim file
    tool_directory = sys.argv[4]  # tool path Galaxy
    with open(bimfile, mode="r") as DataBim:
        original_list = []
        # get all the SNPs from the original bim file
        for line in DataBim:
            line = split_and_strip(line)
            original_list.append(line[1])

        # Perform bootstrapping and write randomly chosen SNPs to list files
        bootstrap_and_write(original_list, iterations=int(sys.argv[2]), output_dir=f"{tool_directory}/consensus_files/temp_files/bootstrap_datasets")


main()
