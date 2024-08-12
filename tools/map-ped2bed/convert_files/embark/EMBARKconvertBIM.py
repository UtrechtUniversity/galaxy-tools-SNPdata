"""
This script:
creates a new file with a list of SNP names to be excluded:
    SNPs on chromosome 0 (= no location available) or with a wrong location that could not be corrected
    SNPs in the SNPsToExcludeMerge.list, because of not identical snp locations between different platforms
    SNPs that are duplicate (one of the duplicate pair)
creates a new bim file with these changes:
    SNP names in uppercase
    removes _ilmndup and _rs numbers
    adds _INDEL for SNPs with insertion or deletion
    changes indel I/D alleles to respectively A and G
    changes wrong alleles to correct alleles using EmbarkCorrectAlleles.bim
    for SNPs without or wrong location, location and chromosome is updated using EmbarkCorrectSNPPositions.map
    Change SNP id if SNP also has different id in other arrays
        (some SNPs in embark are the same as for example in Illumina array, different SNPid, but same location)
"""

import csv
import re
import time
import sys
# get the start time
st = time.time()


def split_and_strip(line, delimiter='\t'):
    """
    :param line: row of input file
    :param delimiter: the delimiter to use
    :return: stripped and split row
    """
    split_line = line.strip().split(delimiter)
    return split_line


def update_id(line, indel_snps):
    """
    :param line: row of input bim file
    :param indel_snps: set with SNP ids that call for indel snps
    :return: row with the SNP id in uppercase and _ilmndup and _rsnumber removed and _INDEL added for indel snps
    """
    line[1] = line[1].upper()  # line[1] is SNP id
    line[1] = re.sub("(_ILMNDUP.*|_RS.*)", "", line[1])
    if line[1] in indel_snps:
        line[1] = line[1] + '_INDEL'
    return line


def get_excluded_snps_merge(file, snps_to_exclude, count_no_correct_location):
    """
    :param file: input file with snps to exclude when merging
    :param snps_to_exclude: set with snps to exclude
    :param count_no_correct_location: counter for how many snps will be removed because location between arrays differs
    :return: updated set of SNP IDs that have to be excluded
    """
    for line in file:
        line = split_and_strip(line)
        if line[0] not in snps_to_exclude:  # line[0] is SNP id
            snps_to_exclude.add(line[0])
            count_no_correct_location += 1
    return snps_to_exclude, count_no_correct_location


def get_snps_without_location(line, snps_to_exclude, count_no_correct_location):
    """
    :param line: row of input map file
    :param snps_to_exclude: set of SNP IDs that have to be excluded
    :param count_no_correct_location: counter for how many snps will be removed because location is missing
    :return: updated snps_to_exclude set with SNP ids with no chromosome information (chromosome = 0, or position = 0)
    """
    if line[0] == '0' or line[3] == '0':  # line[0] is chromosome and line[3] is basepair position of SNP on chromosome
        if line[1] not in snps_to_exclude:
            snps_to_exclude.add(line[1])
            count_no_correct_location += 1
    return snps_to_exclude, count_no_correct_location


def get_indel_snps(file):
    """
    :param file: input file with indel snp IDs
    :return: set with SNP ids that call for indel snps (allele I/D)
    """
    indel_snps = {line.strip().split("\t")[0] for line in file}
    return indel_snps


def update_alleles(line, correct_alleles, count_wrong_allele):
    """
    :param line: row of input bim file
    :param correct_alleles: dictionary with snps and their correct alleles, which have to be updated in the raw bim file
    :param count_wrong_allele: counter for how many wrong alleles were updated
    :return: row with indel alleles changed to 'fictional' alleles and with corrected alleles
    """
    # change allele I to A and D to G
    if re.search("(I|D)", line[4]) or re.search("(I|D)", line[5]):  # line[4] and [5] are allele1 and 2
        line[4] = re.sub("[\t(I)\t]", "A", line[4])
        line[5] = re.sub("[\t(I)\t]", "A", line[5])
        line[4] = re.sub("[\t(D)\t]", "G", line[4])
        line[5] = re.sub("[\t(D)\t]", "G", line[5])

    # for snps that call wrong alleles, change these alleles
    if line[1] in correct_alleles.keys():  # line[1] is SNP id
        if line[4] not in correct_alleles[line[1]] and line[4] != '0':
            line[4] = correct_alleles[line[1]][1]
            count_wrong_allele += 1
        if line[5] not in correct_alleles[line[1]] and line[5] != '0':
            line[5] = correct_alleles[line[1]][1]
            count_wrong_allele += 1
    return line, count_wrong_allele


def get_id(file):
    """
    :param file: input file EmbarkSNPIdConversion
    :return: dictionary with embark ids and other platform id
    """
    different_snp_ids = {}
    for line in file:
        line = line.strip().split(",")
        different_snp_ids[line[0]] = line[1]
    return different_snp_ids


def get_correct_alleles(file):
    """
    :param file: input file with snps with correct alleles, EmbarkCorrectAlleles.bim
    :return: dictionary with format SNPid: [allele1, allele2]
    """
    correct_alleles = {}
    for line in file:
        line = split_and_strip(line)
        correct_alleles[line[1]] = [line[4], line[5]]
    return correct_alleles


def change_id(line, different_snp_ids, count_id_changed):
    """
    :param line: row of input bim file
    :param different_snp_ids: dictionary with embarks snp ids and corresponding other platform ids
    :param count_id_changed: counter for how many SNP ids were updated
    :return: row with changed embark SNP id to other platforms SNP id, if SNP is in EmbarkSNPIdConversion file.
    """
    if line[1] in different_snp_ids.keys():  # line[1] is SNP id
        line[1] = different_snp_ids[line[1]]
        count_id_changed += 1
    return line, count_id_changed


def get_location(line, correct_location_snps, snps_to_exclude, count_locations_changed, count_no_correct_location):
    """
    :param line: row of input bim file
    :param correct_location_snps: dictionary with correct snps locations
    :param snps_to_exclude: set with snps to exclude
    :param count_locations_changed: number count of how many locations were wrong in original file and are changed
    :param count_no_correct_location: number count of snps with a wrong location and no correct location is available
    :return: row with updated snp location, and counts of how many locations were changed,
    and for how many snps no correct locations is available
    """
    # Check if snp is in dictionary with correct snp info
    if line[1] in correct_location_snps.keys():  # line[1] is SNP id
        # count the number of snps that were changed
        if line[3] != correct_location_snps[line[1]][1]:  # line[3] is basepair position of SNP
            count_locations_changed += 1
        # update location
        line[0] = correct_location_snps[line[1]][0]
        line[3] = correct_location_snps[line[1]][1]
    else:
        count_no_correct_location += 1
        if line[1] not in snps_to_exclude:
            snps_to_exclude.add(line[1])
    return line, snps_to_exclude, count_locations_changed, count_no_correct_location


def get_correct_locations(file):
    """
    :param file: input file EmbarkCorrectSNPPositions.map
    :return: dictionary in format SNPid: [chromosome, location]
    """
    correct_location_snps = {}
    for line in file:
        line = split_and_strip(line)
        correct_location_snps[line[1]] = [line[0], line[3]]
    return correct_location_snps


def get_duplicate_or_different_call_snps(file):
    """
    :param file: input file EmbarkDuplicatesOrWrongAllele
    :return: wrong_duplicates set and dictionary with duplicate snp IDs
    """
    duplicate_snps = {}
    wrong_duplicates = set()
    for line in file:
        line = line.strip().split(",")
        # put snps with wrong alleles in wrong duplicates set
        if line[2].startswith('wrong'):
            wrong_duplicates.add(line[0])
        # for duplicates that both call correct allele, create dictionary with the two IDs of this snp
        else:
            duplicate_snps[line[0]] = line[1]
    return wrong_duplicates, duplicate_snps


def check_if_duplicate(line, wrong_duplicates, duplicate_snps, snps_to_exclude, all_snps, count_duplicates, merge_duplicates):
    """
    :param line: input row of bim file
    :param duplicate_snps: dictionary with duplicate snp ids
    :param wrong_duplicates: set with snps that call wrong allele, and are part of a duplicate snp
    :param snps_to_exclude: set with snps to exclude
    :param all_snps: list to which snp ids are added
    :param count_duplicates: number count of duplicates
    :param merge_duplicates: True if duplicates other than the snps in the EmbarkDuplicatesOrWrongAlelle are present
    :return: updated line, snps to exclude set, all snps list, number count of duplicates,
    and status of having to merge duplicates after script converted file
    """
    # change id of the duplicate snps (that both call correct allele) with id that not corresponds with other arrays and
    # is in EmbarkDuplicatesOrWrongAlelle
    if line[1] in wrong_duplicates:  # line[1] is SNP id
        if line[1] not in snps_to_exclude:
            snps_to_exclude.add(line[1])
            count_duplicates += 1
    if line[1] in duplicate_snps.keys():
        line[1] = duplicate_snps[line[1]]
    # add _DUPLICATE to id (of snps that both call correct allele and are in DuplicatesOrWrongAlelle) that have
    # to be removed, so 1 of the duplicate pair remains
    elif line[1] in duplicate_snps.values():
        line[1] = line[1] + '_DUPLICATE'
        if line[1] not in snps_to_exclude:
            snps_to_exclude.add(line[1])
            count_duplicates += 1
    # if other duplicates snps are found (are double in the all_snps list), add _DUPLICATE to SNP id and set status
    # of having to merge the duplicates to true
    if line[1] in all_snps:
        merge_duplicates = True
        line[1] = line[1] + '_DUPLICATE'
        if line[1] not in snps_to_exclude:
            snps_to_exclude.add(line[1])
            count_duplicates += 1
    # if SNPid is not yet in all_snps list, add this snp
    else:
        all_snps.add(line[1])
    return line, wrong_duplicates, duplicate_snps, snps_to_exclude, all_snps, count_duplicates, merge_duplicates


def main():
    """ Creates a new BIM file,
    and creates a file with SNPs that have _ilmndup in SNP id,
    and creates a file with mitochondrial SNPs,
    and creates a file with SNPs to exclude,
    and creates a file with indel SNP ids
    """
    # input files
    filename_bim = sys.argv[1]  # input plink .bim file
    tool_directory = sys.argv[4]  # tool path Galaxy
    snps_to_exclude_merge = f'{tool_directory}/convert_files/common_files/SNPsToExcludeMerge.list'  # File with SNPids to exclude when merging files
    snp_id_conversion = f'{tool_directory}/convert_files/embark/EmbarkSNPIdConversion'  # File to use for changing SNP ids
    embark_duplicates_or_different_allele = f'{tool_directory}/convert_files/embark/EmbarkDuplicatesOrWrongAllele'  # File with duplicate snps
    embark_correct_locations = f'{tool_directory}/convert_files/embark/EmbarkCorrectSNPPositions.map'
    embark_correct_alleles = f'{tool_directory}/convert_files/embark/EmbarkCorrectAlleles.bim'
    filename_indels = f'{tool_directory}/convert_files/embark/EmbarkIndelSNPs.txt'

    # Output files
    new_filename_bim = sys.argv[3]
    embark_snps_to_exclude = sys.argv[2]  # File with SNPnames to use in --exclude plink

    with open(filename_bim, mode="r") as DataBIM, \
            open(snps_to_exclude_merge, mode="r") as DataExcludeMerge, \
            open(embark_duplicates_or_different_allele, mode="r") as DataUnusualSNPs, \
            open(embark_correct_locations, mode="r") as DataCorrectLocations, \
            open(new_filename_bim, "w", newline='') as NewFileBIM, \
            open(embark_snps_to_exclude, "w", newline='') as NewFileExcludedSNPs, \
            open(filename_indels, mode="r") as DataIndels, \
            open(snp_id_conversion, mode="r") as DataSNPID, \
            open(embark_correct_alleles, mode="r") as DataCorrectAlleles:
        writer_exclude = csv.writer(NewFileExcludedSNPs, delimiter='\t')
        writer_bim = csv.writer(NewFileBIM, delimiter='\t')

        snps_to_exclude = set()
        all_snps = set()
        count_locations_changed = 0
        count_no_correct_location = 0
        count_duplicates = 0
        count_wrong_allele = 0
        count_id_changed = 0

        indel_snps = get_indel_snps(DataIndels)  # Get set of indel snps

        # Get dictionary of embark SNP ids with different id in other array, and corresponding other platform ids
        different_snp_ids = get_id(DataSNPID)

        # Get dictionary of SNPs with their correct alleles
        correct_alleles = get_correct_alleles(DataCorrectAlleles)

        # Get dictionary of the correct locations of SNPs
        correct_location_snps = get_correct_locations(DataCorrectLocations)

        # set status for having to merge duplicates with plink after converting this file
        merge_duplicates = False

        # Add snps that are duplicates and call wrong allele, to SNPs to exclude set, and
        # make dictionary of the duplicate snps that both call correct allele for same snp, but with different ID
        wrong_duplicates, duplicate_snps = get_duplicate_or_different_call_snps(DataUnusualSNPs)

        # create a new bim file, mitochondrial snp file, and add snps to Embarks snps to exclude file
        for line in DataBIM:
            line = split_and_strip(line)
            # Make all snp ids uppercase, remove _ilmndup1 and _rsnumber from SNP id and add _INDEL to indels snps
            line = update_id(line, indel_snps)
            # Change SNP id for Embark SNPs that have different name in other platform arrays
            line, count_id_changed = change_id(line, different_snp_ids, count_id_changed)
            # Update locations and count how many snp locations were changed, and of how many snps no correct location
            # is available (these snps are put in snps to exclude set).
            line, snps_to_exclude, count_locations_changed, count_no_correct_location \
                = get_location(line, correct_location_snps, snps_to_exclude, count_locations_changed,
                               count_no_correct_location)
            # update wrong alleles to correct alleles and change indel alleles (I=A, D=G)
            line, count_wrong_allele = update_alleles(line, correct_alleles, count_wrong_allele)
            # check if snp is a duplicate (in duplicate_snps dictionary), change the snp id, and
            # add duplicate snp to snps_to_exclude list
            line, wrong_duplicates, duplicate_snps, snps_to_exclude, all_snps, count_duplicates, merge_duplicates = check_if_duplicate(
                line, wrong_duplicates, duplicate_snps, snps_to_exclude, all_snps, count_duplicates, merge_duplicates)
            # Write adjusted row to new bim file
            writer_bim.writerow(line)
            # Add snps with chromosome 0 or position 0 to embarks snps to exclude set
            snps_to_exclude, count_no_correct_location = get_snps_without_location(line, snps_to_exclude, count_no_correct_location)

        # Add snps from SNPsToExcludeMerge.list to embarks snps to exclude set
        snps_to_exclude, count_no_correct_location = get_excluded_snps_merge(DataExcludeMerge, snps_to_exclude, count_no_correct_location)

        # Write snps to exclude to new file
        for snp in snps_to_exclude:
            writer_exclude.writerow([snp])

        print("Number of SNPs to be deleted: ", len(snps_to_exclude))
        print("\t- Number of SNPs of which no correct location is available, or location differs between arrays: ", count_no_correct_location)
        print("\t- Number of duplicate SNPs: ", count_duplicates)
        print("Number of SNPs of which location is updated: ", count_locations_changed)
        print("Number of SNPs for which alleles were corrected: ", count_wrong_allele)
        print("Number of SNPs of which id is updated: ", count_id_changed)

        if merge_duplicates:
            print('Use plink --merge-equal-pos to merge duplicate SNPs')
        else:
            print('No duplicate SNPs are left in the new file')


main()

# get the end time
et = time.time()

# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')
