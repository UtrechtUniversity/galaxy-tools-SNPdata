"""
This script:
creates a ped file in TOP calling with these changes:
    changes - to 0 for alleles
    changes I to A, and D to G for indel alleles
creates a map file with these changes:
    removes _rs numbers of SNP name
    makes the SNP names uppercase
    adds _INDEL to id of indel SNPs
    changes chromosome coding:
        for SNPs in the pseudo autosomal region, change chromosome X to 41
        for SNPs NOT in the pseudo autosomal region, change chromosome X to 39
        for SNPs on Y chromosome, change chromosome Y to 40
        for mitochondrial snps change chromosome MT to 42
    updates location of SNPs if possible (get location from snp id or from file (Neogen220KSNPsMissingLocation)
    with locations in other platform arrays)
    change location and chromosome of indel SNPs using SNP id
    change location and chromosome of Y SNPs using SNP id
    for SNP ids that have different Id in other arrays, change name
    updates wrong alleles
creates a new file with a list of SNP names to be excluded:
    SNPs without location
    Duplicate SNPs
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


def reorder_columns(line):
    """
    :param line: row of input snp map file
    :return: a reordered row, with also a zero added for centi morgan position
    """
    line[0], line[2] = line[2], "0" # chromosome, SNPid, 0, basepair position
    return line


def update_snp_id(line, different_snp_ids, count_id_changed):
    """
    :param line: input row of snp map file
    :param different_snp_ids: dictionary with neogens snp ids and corresponding other platform ids
    :param count_id_changed: counter for how many ids were changed
    :return: snp id without rs number, in uppercase, and with updated snp id if snp present
    in other platforms under different id
    """
    line[1] = re.sub("(_rs.*)", "", line[1]).upper()  # line[1] is SNPid
    if line[1] in different_snp_ids.keys():
        line[1] = different_snp_ids[line[1]]
        count_id_changed += 1
    return line, count_id_changed


def add_indel_to_id(line):
    """
    :param line: input row of snp map file
    :return: row with _INDEL added to snp id for indel snps and updated location
    """
    if line[5] == '[I/D]' or line[5] == '[D/I]':
        if line[1].startswith('CHR'):  # line[1] is SNPid
            # update chromosome
            chromosome = re.findall('CHR(.+)_', line[1])
            line[0] = chromosome[0]
            # update location
            position = re.findall('_(.+)', line[1])
            line[3] = position[0]  # line[3] is basepair position
        # add _INDEL to SNP id
        line[1] = line[1] + '_INDEL'
    # select necessary columns
    line = line[0:4]  # chromosome, SNPid, 0, basepair position
    return line


def update_chromosome(line):
    """
    :param line: row of snp map file
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
    # For mitochondrial SNPs, change chromosome to 42
    if line[0] == 'MT' or line[0] == 'M':
        line[0] = '42'
    return line


def get_id(file):
    """
    :param file: input file NeogenSNPIdCorrespondingOtherArrayId.txt
    :return: dictionary with neogen ids and other platform id
    """
    different_snp_ids = {}
    for line in file:
        line = line.strip().split(",")
        different_snp_ids[line[0]] = line[1]
    return different_snp_ids


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


def get_location(line, count_locations_changed):
    """
    :param line: row of input snp map file
    :param count_locations_changed: counter for how many locations are changed
    :return: row with generated chromosome and bp position for a SNP that originally had no location,
    e.g. SNP chr11_9030031 gets chromosome 11 and bp position 9030031, and updated chromosome and location for snps on
    Y chromosome
    """
    # get chromosome and location from SNP id
    # line[1] is SNP id, line[0] is chromosome, line[3] is basepair position
    if line[0] == '0' and line[3] == '0' and line[1].startswith('CHR') and not line[1].startswith('CHRU'):
        chromosome = re.findall('CHR(.+)_', line[1])
        line[0] = re.sub('0', chromosome[0], line[0])
        position = re.findall('_(.+)', line[1])
        line[3] = re.sub('0', position[0], line[3])
        count_locations_changed += 1
    if line[1].startswith('CHRY'):
        line[0] = '40'
        position = re.findall('_(.+)', line[1])
        line[3] = position[0]
        count_locations_changed += 1
    return line, count_locations_changed


def get_info_new_sample(line):
    """
    :param line: input row of final report file
    :return: a list with info of the sample: family ID, individual ID, Paternal Id, Maternal Id, Sex, Phenotype,
    of which the last 4 are set to 0
    """
    sample = line[1]
    alleles = []
    sample_info = [line[1], line[1], "0", "0", "0", "0"]
    return sample, alleles, sample_info


def add_allele(line, alleles, correct_alleles, count_wrong_allele):
    """
    :param line: row of input final report file
    :param alleles: the list with alleles already gathered for this sample
    :param correct_alleles: dictionary with snps and their correct alleles, which have to be updated in the raw bim file
    :param count_wrong_allele: counter for how many wrong alleles were updated
    :return: list with alleles for this sample. In each iteration, new alleles are added to this list.
    """
    # update missing and indel alleles, line[4] and [5] are allele 1 and 2
    if line[4] == '-':
        line[4] = '0'
    if line[5] == '-':
        line[5] = '0'
    if line[4] == 'I':
        line[4] = 'A'
    if line[4] == 'D':
        line[4] = 'G'
    if line[5] == 'I':
        line[5] = 'A'
    if line[5] == 'D':
        line[5] = 'G'
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


def get_missing_location_snps(file):
    """
    :param file: input file (Neogen220KSNPsMissingLocation)
    :return: dictionary with missing snp info (SNP_id: [chromosome, location])
    """
    missing_snps_info = {}
    for line in file:
        line = split_and_strip(line)
        missing_snps_info[line[1]] = [line[0], line[3]]
    return missing_snps_info


def get_missing_location(line, missing_snps_info, count_locations_changed):
    """
    :param line: row of input snp map file
    :param missing_snps_info: dictionary with missing snps info
    :param count_locations_changed: counter for how many locations are changed
    :return: row with updated location and chromosome
    """
    # update chromosome and location
    # line[0] is chromosome, line[1] is SNP id, line[3] is basepair position
    if line[1] in missing_snps_info.keys():
        line[3] = missing_snps_info[line[1]][1]
        line[0] = missing_snps_info[line[1]][0]
        count_locations_changed += 1
    return line, count_locations_changed


def get_snps_without_location_for_exclude_file(line, snps_to_exclude_list, count_no_correct_location):
    """
    :param line: row of snp map file
    :param snps_to_exclude_list: list to which the snps are added, which have to be excluded because of no location,
    these snps have as chromosome: 0, so location is incorrect.
    :param count_no_correct_location: counter for how many snps have no location
    :return: updated list with snps that have to be excluded
    """
    # check if chromosome or basepair position is 0, and snp is not already in snps to exclude list
    if line[0] == '0' or line[3] == '0' and line[1] not in snps_to_exclude_list:
        snps_to_exclude_list.append(line[1])
        count_no_correct_location += 1
    return snps_to_exclude_list, count_no_correct_location


def get_excluded_snps_merge(file, snps_to_exclude_list, count_merge_exclude):
    """
    :param file: input file SNPsToExcludeMerge.list
    :param snps_to_exclude_list: list to which the snps names are added from the SNPsToExcludeMerge.list, if they are not
    already in the list
    :param count_merge_exclude: counter for how many snps will be removed because location differs between arrays
    :return: updated list with snps that have to be excluded
    """
    for line in file:
        line = split_and_strip(line)
        if line[0] not in snps_to_exclude_list:  # line[0] is SNP id
            snps_to_exclude_list.append(line[0])
            count_merge_exclude += 1
    return snps_to_exclude_list, count_merge_exclude


def get_duplicates(file, snps_to_exclude_list, count_duplicates):
    """
    :param file: file Neogen220KDuplicates
    :param snps_to_exclude_list: list with snps to exclude, to append to
    :param count_duplicates: counter for how many duplicates are removed
    :return: Neogen SNP ids (first column) in this file
    """
    for line in file:
        line = split_and_strip(line, ',')
        if line[0] not in snps_to_exclude_list:  # line[0] is SNP id
            snps_to_exclude_list.append(line[0])
            count_duplicates += 1
    return snps_to_exclude_list, count_duplicates


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
    Creates a new MAP file and a new PED file and a file with SNPs to exclude
    """
    # input files
    filename_final = sys.argv[1]  # input final report file that was given as option in the convert.sh script
    filename_map = 'convert_files/neogen220/Neogen220K_SNP_Map_CF3.txt'  # input snp map from neogen
    filename_missing_snps = 'convert_files/neogen220/Neogen220KSNPsMissingLocation'  # File with locations of snps that have a missing location
    snps_to_exclude_merge = 'convert_files/common_files/SNPsToExcludeMerge.list'  # File with SNPids to exclude when merging files
    # File with neogen snp ids that have different id in other platforms
    other_array_ids = 'convert_files/neogen220/Neogen220KSNPsIdConversion.txt'  # File to use for changing SNP ids
    duplicates = 'convert_files/neogen220/Neogen220KDuplicates.txt'  # File with duplicate snps
    neogen_correct_alleles = 'convert_files/neogen220/Neogen220KCorrectAlleles.bim'

    # output files
    new_filename_map = sys.argv[3] + '.map'
    new_filename_ped = sys.argv[3] + '.ped'
    neogen_snps_to_exclude = sys.argv[2]  # File with SNPids to use in --exclude plink

    with open(filename_map, mode="r") as DataMAP, \
            open(filename_final, mode="r") as DataFINAL, \
            open(duplicates, mode="r") as DataDuplicates, \
            open(filename_missing_snps, mode="r") as DataMissingSNPs, \
            open(new_filename_map, "w", newline='') as NewFileMAP, \
            open(new_filename_ped, "w", newline='') as NewFilePED, \
            open(snps_to_exclude_merge, mode="r") as DataExcludeMerge, \
            open(neogen_correct_alleles, mode="r") as DataCorrectAlleles, \
            open(other_array_ids, mode="r") as DataOtherIds, \
            open(neogen_snps_to_exclude, "w", newline='') as NewFileExcludedSNPs:
        writer_map = csv.writer(NewFileMAP, delimiter='\t')
        writer_ped = csv.writer(NewFilePED, delimiter='\t')
        writer_exclude = csv.writer(NewFileExcludedSNPs, delimiter='\t')

        count_locations_changed = 0
        count_no_correct_location = 0
        count_id_changed = 0
        count_duplicates = 0
        count_merge_exclude = 0
        count_wrong_allele = 0
        # Make dictionary of snps with missing snp info
        missing_snps_info = get_missing_location_snps(DataMissingSNPs)

        # Make dictionary with neogen snp ids and corresponding other array ids
        different_snp_ids = get_id(DataOtherIds)

        # Get dictionary of SNPs with their correct alleles
        correct_alleles = get_correct_alleles(DataCorrectAlleles)

        snps_to_exclude_list = []
        # create new  map file
        for index, line in enumerate(DataMAP):
            # skip first header line
            if index == 0:
                continue
            line = split_and_strip(line)
            line = reorder_columns(line)
            # make snp id uppercase, remove _rsnumber, change snp id if present in other arrays under different name
            line, count_id_changed = update_snp_id(line, different_snp_ids, count_id_changed)
            # get location from snp ID for snps without location and Y chrom snps
            line, count_locations_changed = get_location(line, count_locations_changed)
            # add _INDEL to snp id for indel snps and update location
            line = add_indel_to_id(line)
            # for snps without location, if possible get location from file with location in other arrays
            line, count_locations_changed = get_missing_location(line, missing_snps_info, count_locations_changed)
            # change chromosome coding: X to 39 or 41 (pseudo-autosomal), and Y to 40, and MT to 42
            line = update_chromosome(line)
            # Add snps with chromosome 0 or position 0 to neogen snps to exclude file
            snps_to_exclude_list, count_no_correct_location = get_snps_without_location_for_exclude_file(line, snps_to_exclude_list, count_no_correct_location)
            writer_map.writerow(line)

        # Add snps from SNPsToExcludeMerge.list to snps to exclude list
        snps_to_exclude_list, count_merge_exclude = get_excluded_snps_merge(DataExcludeMerge, snps_to_exclude_list, count_merge_exclude)

        # Add duplicate snps to the snps to exclude list
        snps_to_exclude_list, count_duplicates = get_duplicates(DataDuplicates, snps_to_exclude_list, count_duplicates)

        # write snps in snps_to_exclude_list to new file
        for snp in snps_to_exclude_list:
            writer_exclude.writerow([snp])

        # create new ped file
        skip_row = True
        header = False
        sample = None
        sample_info = []
        alleles = []
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
        print("\t- Number of duplicate SNPs: ", count_duplicates)
        print("\t- Number of SNPs to be removed because location of SNP differs between arrays: ", count_merge_exclude)
        print("Number of SNPs of which location is updated: ", count_locations_changed)
        print("Number of SNPs of which id is updated: ", count_id_changed)
        print("Number of SNPs in all samples with a wrong allele:", count_wrong_allele)

main()

# get the end time
et = time.time()
# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')