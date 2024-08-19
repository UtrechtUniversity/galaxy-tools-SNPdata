"""
This script:
creates a ped file with these changes:
    changes - to 0 for alleles
creates a map file with these changes:
    removes _rs numbers of SNP name
    makes the SNP names uppercase
    changes chromosome coding:
        for SNPs in the pseudo autosomal region, change chromosome X to 41
        for SNPs NOT in the pseudo autosomal region, change chromosome X to 39
        for SNPs on Y chromosome, change chromosome Y to 40
    updates the snp location and chromosome, from canfam 2 to 3.1
    updates wrong alleles
creates a new file with a list of SNP names to be excluded:
    SNPs without location or SNPs that could not be lift over to canfam 3.1
    SNPs on SNPsToExcludeMerge.list
"""
import csv
import re
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


def reorder_and_select_columns(line):
    """
    :param line: row of input snp map file
    :return: a reordered row, with also a zero added for centi morgan position
    """
    line[0], line[2] = line[2], "0"
    line = line[0:4]  # chromosome, SNPid, 0, basepair position
    return line


def update_id(line):
    """
    :param line: row of input snp map file
    :return: row with the SNP id in uppercase and _rsnumber removed
    """
    line[1] = line[1].upper()  # line[1] is SNPid
    line[1] = re.sub("(_RS.*)", "", line[1])
    return line


def update_chromosome(line):
    """
    :param line: row of input snp map file
    :return: row with updated chromosome: X chromosomes divided over 39 en 41 (pseudo-autosomal), and Y becomes 40
    """
    if line[0] == 'X':  # line[0] is chromosome
        if int(line[3]) < 6640000:  # line[3] is basepair position
            # For SNPs in the pseudo autosomal region, change chromosome X to 41
            line[0] = '41'
        else:
            # For SNPs NOT in the pseudo autosomal region, change chromosome X to 39
            line[0] = '39'
    # For Y chromosome SNPs, change chromosome Y to 40
    if line[0] == 'Y':
        line[0] = '40'
    return line


def skip_description(line, skip_row, header):
    """
    :param line: input row of final report file
    :param skip_row: True if this row has to be skipped, otherwise false
    :param header: True when current row is the header, otherwise false
    :return: status of skip_row and header
    """
    # if previous row was the header, then current row, and following rows, should not be skipped
    if header:
        skip_row = False
    # check if current row is header
    if line.startswith("SNP"):
        header = True
    return skip_row, header


def check_if_same_sample(line, sample):
    """
    :param line: input row of final report file
    :param sample: the sample in the previous row
    :return: If still the same sample: True, otherwise if new sample: False
    """
    # check if this row has the same sample Id as the previous row (stored in param sample)
    if line[1] == sample:
        same_sample = True
    else:
        same_sample = False
    return same_sample


def get_info_new_sample(line):
    """
    :param line: input row of ped file
    :return: a list with info of the sample: family ID, individual ID, Paternal Id, Maternal Id, Sex, Phenotype,
    of which the last 4 are set to 0
    """
    sample = line[1]
    alleles = []
    sample_info = [line[1], line[1], "0", "0", "0", "0"]
    return sample, alleles, sample_info


def add_allele(line, alleles, correct_alleles, count_wrong_allele):
    """
    :param line: row of input file
    :param alleles: the list with alleles already gathered for this sample
    :param correct_alleles: dictionary with snps and their correct alleles, which have to be updated in the raw bim file
    :param count_wrong_allele: counter for how many wrong alleles were updated
    :return: list with alleles for this sample. In each iteration, new alleles are added to this list.
    """
    # change missing alleles to 0, line[4] and [5] are allele 1 and 2
    if line[4] == '-':
        line[4] = '0'
    if line[5] == '-':
        line[5] = '0'
    # for snps that call wrong alleles, change these alleles
    if line[0] in correct_alleles.keys():  # line[0] is Sample id
        if line[4] not in correct_alleles[line[0]] and line[4] != '0':
            line[4] = correct_alleles[line[0]][1]
            count_wrong_allele += 1
        if line[5] not in correct_alleles[line[0]] and line[5] != '0':
            line[5] = correct_alleles[line[0]][1]
            count_wrong_allele += 1
    alleles.extend([line[4], line[5]])
    return alleles, count_wrong_allele


def previous_sample_complete(sample_info, sample_alleles):
    """
    :param sample_info: the sample info list created with function get_info_new_sample(line)
    :param sample_alleles: list with alleles for this sample
    :return: if the previous sample is complete, add the sample info list and the alleles list together in one list.
    Return True if the list is complete, and the return list with complete sample information.
    First it is checked whether the sample_info list is not empty. This is empty if no info was added yet, because this
    is the first sample in the loop, there was no previous sample.
    """
    if len(sample_info) != 0:
        complete_sample = sample_info + sample_alleles
        return True, complete_sample
    else:
        complete_sample = []
        return False, complete_sample


def get_excluded_snps_merge(file):
    """
    :param file: input file SNPsToExcludeMerge.list
    :return: updated list with snps that have to be excluded
    """
    snps_to_exclude_merge = set()
    for line in file:
        line = split_and_strip(line)
        snps_to_exclude_merge.add(line[0])
    return snps_to_exclude_merge


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


def update_location(line, snps_cf3_info, snps_to_exclude_list, snps_to_exclude_merge, count_merge_exclude, count_no_correct_location, count_locations_changed):
    """
    :param line: row of input map file
    :param snps_cf3_info: dictionary of snps in canfam 3
    :param snps_to_exclude_list: list to which the snps are added that are not liftover to canfam 3.1 to exclude
    :param snps_to_exclude_merge: set with snps that have to be excluded because location differs between arrays
    :param count_merge_exclude: counter of how many snps have no correct location
    :param count_no_correct_location: counter of how many snps have no correct location
    :param count_locations_changed: counter of how many snp locations were updated
    :return: row with updated location and chromosome, list with snps to exclude
    """
    if line[1] in snps_to_exclude_merge:  # line[1] is SNP id
        if line[1] not in snps_to_exclude_list:
            snps_to_exclude_list.append(line[1])
            count_merge_exclude += 1
    elif line[1] in snps_cf3_info.keys():
        # count the number of snps that were changed
        if line[3] != snps_cf3_info[line[1]][1]:
            count_locations_changed += 1
        line[0] = snps_cf3_info[line[1]][0]  # line[0] is chromosome
        line[3] = snps_cf3_info[line[1]][1]  # line[3] is basepair position
    else:
        count_no_correct_location += 1
        snps_to_exclude_list.append(line[1])
    return line, snps_to_exclude_list, count_merge_exclude, count_no_correct_location, count_locations_changed


def get_correct_alleles(file):
    """
    :param file: input file with snps with correct alleles, Neogen220KCorrectAlleles.bim
    :return: dictionary with format SNPid: [allele1, allele2]
    """
    correct_alleles = {}
    for line in file:
        line = split_and_strip(line)
        correct_alleles[line[1]] = [line[4], line[5]]
    return correct_alleles


def main():
    """
    Creates a new MAP file, a new PED file and a file with SNPs to exclude
    """
    # input files
    filename_final = sys.argv[1]  # input final report file that was given as option in the convert.sh script
    tool_directory = sys.argv[4]  # tool path Galaxy
    filename_map = f'{tool_directory}/convert_files/neogen170/Neogen170KRaw_SNP_Map.txt'
    filename_cf3_locations = f'{tool_directory}/convert_files/neogen170/Neogen170KsnpsPresentInCF3.map'  # File with snps that have a location in canfam 3.1
    snps_to_exclude_merge = f'{tool_directory}/convert_files/common_files/SNPsToExcludeMerge.list'  # File with SNPids to exclude when merging files
    neogen_correct_alleles = f'{tool_directory}/convert_files/neogen170/Neogen170KCorrectAlleles.bim'

    # output files
    new_filename_map = sys.argv[3] + '.map'
    new_filename_ped = sys.argv[3] + '.ped'
    neogen_snps_to_exclude = sys.argv[2]  # File with SNPids to use in --exclude plink

    with open(filename_map, mode="r") as DataMAP, \
            open(filename_final, mode="r") as DataFINAL, \
            open(filename_cf3_locations, mode="r") as DataCF3, \
            open(snps_to_exclude_merge, mode="r") as DataExcludeMerge, \
            open(neogen_snps_to_exclude, "w", newline='') as NewFileExcludedSNPs, \
            open(neogen_correct_alleles, mode="r") as DataCorrectAlleles, \
            open(new_filename_map, "w", newline='') as NewFileMAP, \
            open(new_filename_ped, "w", newline='') as NewFilePED:
        writer_exclude = csv.writer(NewFileExcludedSNPs, delimiter='\t')
        writer_map = csv.writer(NewFileMAP, delimiter='\t')
        writer_ped = csv.writer(NewFilePED, delimiter='\t')

        # Make dictionary of snps that were liftover to canfam 3.1
        snps_cf3_info = get_cf3_locations(DataCF3)

        # Add snps from SNPsToExcludeMerge.list to a set
        snps_to_exclude_merge = get_excluded_snps_merge(DataExcludeMerge)

        # Get dictionary of SNPs with their correct alleles
        correct_alleles = get_correct_alleles(DataCorrectAlleles)

        count_locations_changed = 0
        count_no_correct_location = 0
        count_merge_exclude = 0
        count_wrong_allele = 0

        snps_to_exclude_list = []
        # create new map file in cf 3.1
        for index, line in enumerate(DataMAP):
            # skip first header line
            if index == 0:
                continue
            line = split_and_strip(line)
            line = reorder_and_select_columns(line)
            line = update_id(line)  # make id uppercase and remove _rsnumber
            # Update location and chromosome and add snps to snp list to exclude when snp could not be liftover
            line, snps_to_exclude_list, count_merge_exclude, count_no_correct_location, count_locations_changed = update_location(line, snps_cf3_info, snps_to_exclude_list, snps_to_exclude_merge, count_merge_exclude, count_no_correct_location, count_locations_changed)
            # change chromosome coding: X to 39 or 41 (pseudo-autosomal), and Y to 40
            line = update_chromosome(line)
            writer_map.writerow(line)

        # write snps in snps_to_exclude_list to new file
        for snp in snps_to_exclude_list:
            writer_exclude.writerow([snp])

        # create new ped file
        skip_row = True
        header = False
        sample = None
        sample_info = []
        alleles = []
        # get index of last sample
        for line in DataFINAL:
            # skip the first lines with data description
            skiprow, header = skip_description(line, skip_row, header)
            if skiprow:
                continue
            line = split_and_strip(line)
            # check if sample has changed or not
            if not check_if_same_sample(line, sample):
                # if this is a new sample, complete the previous sample and write this to a new file
                complete, complete_sample = previous_sample_complete(sample_info, alleles)
                if complete:
                    writer_ped.writerow(complete_sample)
                # get sample info of new sample (family ID, individual ID, paternal and maternal ID, sex and phenotype)
                sample, alleles, sample_info = get_info_new_sample(line)
            # if still on same sample, add new alleles to list
            if check_if_same_sample(line, sample):
                # update and add alleles
                alleles, count_wrong_allele = add_allele(line, alleles, correct_alleles, count_wrong_allele)
        # completing last sample
        complete, complete_sample = previous_sample_complete(sample_info, alleles)
        if complete:
            writer_ped.writerow(complete_sample)

        print("Number of SNPs to be deleted: ", len(snps_to_exclude_list))
        print("\t- Number of SNPs of which no correct location is available: ", count_no_correct_location)
        print("\t- Number of SNPs to be removed because location of SNP differs between arrays: ", count_merge_exclude)
        print("Number of SNPs of which location is updated (canfam 2 --> canfam 3): ", count_locations_changed)
        print("Number of SNPs in all samples with a wrong allele:", count_wrong_allele)


main()

# get the end time
et = time.time()
# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')