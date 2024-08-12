"""
This script:
creates a bim file with these changes:
    changes chromosome coding:
        for SNPs in the pseudo autosomal region, change chromosome 39 to 41
        for SNPs NOT in the pseudo autosomal region chromosome remains 39
    updates the snp location and chromosome, from canfam 2 to 3.1
creates a new file with a list of SNP names to be excluded:
    SNPs that could not be lift over to canfam 3.1
    SNPs that can't be converted to TOP calling
    SNPs on SNPsToExcludeMerge.list
"""
import csv
import time
import sys
# get the start time
st = time.time()


def split_and_strip(line, delimiter="\t"):
    """
    :param line: row of input file
    :param delimiter: which delimiter to use
    :return: stripped and split row
    """
    split_line = line.strip().split(delimiter)
    return split_line


def get_excluded_snps(file):
    """
    :param file: input file
    :return: list with snps that are in the file
    """
    new_list = []
    for line in file:
        line = split_and_strip(line)
        new_list.append(line[0])  # line[0] is SNP id
    return new_list


def get_cf3_locations(file):
    """
    :param file: input file with snps in canfam 3.1
    :return: dictionary of snps in cf3 (snp_id: [chromosome, location]
    """
    snps_cf3_info = {}
    for line in file:
        line = split_and_strip(line)
        snps_cf3_info[line[1]] = [line[0], line[3]]
    return snps_cf3_info


def update_location(line, snps_cf3_info, snps_to_exclude_list, count_no_correct_location):
    """
    :param line: row of input bim file
    :param snps_cf3_info: dictionary of snps in canfam 3
    :param snps_to_exclude_list: list to which the snps are added that are not liftover to canfam 3.1 to exclude
    :param count_no_correct_location: counter for how many snps no correct location is known
    :return: row with updated location and chromosome, list with snps to exclude
    """
    if line[1] in snps_cf3_info.keys():  # line[1] is SNP id
        line[0] = snps_cf3_info[line[1]][0]  # line[0] is chromosome
        line[3] = snps_cf3_info[line[1]][1]  # line[3] is basepair position
    else:
        if line[1] not in snps_to_exclude_list:
            snps_to_exclude_list.append(line[1])
            count_no_correct_location += 1
    return line, snps_to_exclude_list, count_no_correct_location


def check_exclude_snp(line, snps_to_exclude_merge, snps_not_in_top, snps_to_exclude_list, count_not_in_top, count_exclude_merge):
    """
    :param line: row of input bim file
    :param snps_to_exclude_merge: list with which snps to exclude when merging files because location differs between arrays
    :param snps_not_in_top: list with snps that can not be converted to top calling
    :param snps_to_exclude_list: list with snps that have to be excluded
    :param count_not_in_top: counter for how many snps cannot be converted to top
    :param count_exclude_merge: counter for how many snps will be removed because location differs between arrays
    :return: updated snps_to_exclude_list, and updated counts
    """
    if line[1] in snps_not_in_top and line[1] not in snps_to_exclude_list:
        snps_to_exclude_list.append(line[1])  # line[1] = SNP id
        count_not_in_top += 1
    if line[1] in snps_to_exclude_merge and line[1] not in snps_to_exclude_list:
        snps_to_exclude_list.append(line[1])
        count_exclude_merge += 1
    return snps_to_exclude_list, count_not_in_top, count_exclude_merge


def main():
    """
    Creates a new BIM file and a file with SNPs to exclude
    """
    # input files
    filename_bim = sys.argv[1]  # input plink .bim file
    filename_cf3_locations = 'convert_files/lupa170/LupaSNPsPresentInCF3.map'  # File with snps that have a location in canfam 3.1
    snps_to_exclude_merge = 'convert_files/common_files/SNPsToExcludeMerge.list'  # File with SNPids to exclude when merging files
    snps_not_in_top = 'convert_files/lupa170/Lupa174KSNPsNotInTop.list'  # File with SNPs that cannot be converted to TOP calling

    # output files
    lupa174k_snps_to_exclude = sys.argv[2]  # File with SNPnames to use in --exclude plink
    new_filename_bim = sys.argv[3] + '.bim'

    with open(filename_bim, mode="r") as DataBIM, \
            open(filename_cf3_locations, mode="r") as DataCF3, \
            open(snps_to_exclude_merge, mode="r") as DataExcludeMerge, \
            open(snps_not_in_top, mode="r") as DataNotInTop, \
            open(lupa174k_snps_to_exclude, "w", newline='') as NewFileExcludedSNPs, \
            open(new_filename_bim, "w", newline='') as NewFileBIM:
        writer_exclude = csv.writer(NewFileExcludedSNPs, delimiter='\t')
        writer_map = csv.writer(NewFileBIM, delimiter='\t')

        # Make dictionary of snps that were liftover to canfam 3.1
        snps_cf3_info = get_cf3_locations(DataCF3)
        # Make list of SNPs that have to be excluded when merging files
        snps_to_exclude_merge = get_excluded_snps(DataExcludeMerge)
        # Make list of SNPs not present in TOP calling
        snps_not_in_top = get_excluded_snps(DataNotInTop)

        snps_to_exclude_list = []
        count_exclude_merge = 0
        count_not_in_top = 0
        count_no_correct_location = 0
        for line in DataBIM:
            line = split_and_strip(line)
            # Update location and chromosome and add snps to snp list to exclude when snp could not be liftover
            line, snps_to_exclude_list, count_no_correct_location = update_location(line, snps_cf3_info, snps_to_exclude_list, count_no_correct_location)
            # Check if snp needs to be excluded because no TOP calling is known or location differs between arrays
            snps_to_exclude_list, count_not_in_top, count_exclude_merge = check_exclude_snp(line, snps_to_exclude_merge, snps_not_in_top, snps_to_exclude_list, count_not_in_top,
                              count_exclude_merge)
            writer_map.writerow(line)

        # write snps in snps_to_exclude_list to new file
        for snp in snps_to_exclude_list:
            writer_exclude.writerow([snp])

        print("Number of SNPs to be deleted: ", len(snps_to_exclude_list))
        print("\t- Number of SNPs of which no correct location is available, or location differs between arrays: ", count_exclude_merge + count_no_correct_location)
        print("\t- Number of SNPs that can not be converted to TOP callling: ", count_not_in_top)


main()

# get the end time
et = time.time()
# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')