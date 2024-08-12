"""
This script:
Creates a new bim file with these changes:
    adds SNP id for known snps, based on base pair position
    SNPs on chromosome 39 are divided over 39 and 41 (pseudo-autosomal)
    flipped strands when needed
    changes alleles of indel IDs to fictional alleles A (insertion) and G (deletion)
    changes locations from canfam 4 to 3
Creates a file with SNPs to extract
    only snps:
        with a SNP id
        bi-allelic
        that are SNPs and not indels, except for the known indels
"""

import csv
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


def get_snp_name_and_update_chromosome(line, snp_info, count_false_indel, count_snp_id_not_found, count_indel_shown_as_snp):
    """
    :param line: input row of bim file
    :param snp_info: dictionary with snp information in format ('location:chromosome': 'SNP id')
    :param count_false_indel: counter for how many false indels were found
    :param count_snp_id_not_found: counter for how many snps miss a snp id
    :param count_indel_shown_as_snp: counter for how many snps falsly call for indel
    :return: row with updated chromosome (chr 39 divided over 39 and 41 = pseudo-autosomal), added SNP id when location
    and chromosome combination match with a SNP in snp_info dictionary, and updated alleles for indel snps (insertion
    becomes A, deletion becomes G). Changed SNP_id to '.' when non-indel SNPs code for indels, and when a * is present
    in the alleles (‘*’ indicates that the allele is missing due to a upstream deletion).
    """
    # divide chr 39 over 39 and 41 (pseudo-autosomal)
    if line[0] == '39' or line[0] == '41':
        if int(line[3]) < 6640000:
            line[0] = '41'
        else:
            line[0] = '39'
    loc = line[0] + ':' + line[3]
    # if chromosome-location combination is in the snp_info dictionary, get corresponding SNP id from dictionary
    if loc in snp_info.keys():
        line[1] = snp_info[loc]
        # if snp was found, delete this one from dictionary, so no duplicate SNPs end up in bim file
        # (second snp of duplicate gets '.' for snp id).
        del snp_info[loc]
        # change alleles of indel SNPs to insertion = A and deletion = G
        if line[1].endswith('INDEL'):   # line[1] is SNP id
            first = line[4]  # line[4] is allele 1
            second = line[5]  # line[5] is allele 2
            # check if indel snps is coding for an indel, if not, it is an incorrect snp
            if len(first) == 1 and len(second) == 1:
                line[1] = '.'
                count_indel_shown_as_snp += 1
            # check if insertion or deletion (insertion is more alleles compared to deletion)
            if len(first) > len(second):
                line[4] = 'A'
                line[5] = 'G'
            else:
                line[4] = 'G'
                line[5] = 'A'
        # change SNP id to '.' when SNP codes for a indel, but is not known as indel snp, and when SNP has a * allele
        if len(line[4]) > 1 or len(line[5]) > 1 or line[4] == '*' or line[5] == '*':
            line[1] = '.'
            count_false_indel += 1
    else:
        line[1] = '.'
        count_snp_id_not_found += 1
    return line, count_false_indel, count_snp_id_not_found, count_indel_shown_as_snp


def get_snp_info(file_alleles):
    """
    :param file_alleles: input bim file with correct alleles in forward
    :return: dictionary with format ('snp id': [allele 1, allele 2]
    """
    forward_alleles = {}
    for line in file_alleles:
        line = split_and_strip(line)
        forward_alleles[line[1]] = [line[4], line[5]]
    return forward_alleles


def update_alleles(line, forward_alleles, count_flip, count_tri_allelic):
    """
    :param line: input row of bim file
    :param forward_alleles: dictionary with forward alleles for each SNP
    :param count_flip: number count for flipped strands
    :param count_tri_allelic: number count for triallelic SNPs
    :return: updated row (with flipped strand if necessary, and SNP id is changed to '.' for SNPs that call wrong,
    (tri-)allelic alleles (they do not match with alleles in forward_alleles dictionary)), the number count for flipped
    strands and tri-allelic/wrong alleles.
    """
    # line[1] is SNP id, line[4] and [5] are alleles 1 and 2
    if line[1] != '.' and line[1] in forward_alleles.keys():
        # get correct forward alleles for this SNP
        correct_alleles = forward_alleles[line[1]]

        # if alleles in bim file are not the same as correct forward alleles, flip strand
        if line[4] not in correct_alleles or line[5] not in correct_alleles:
            if line[4] == 'A':
                line[4] = 'T'
            elif line[4] == 'T':
                line[4] = 'A'
            elif line[4] == 'C':
                line[4] = 'G'
            elif line[4] == 'G':
                line[4] = 'C'
            if line[5] == 'A':
                line[5] = 'T'
            elif line[5] == 'T':
                line[5] = 'A'
            elif line[5] == 'C':
                line[5] = 'G'
            elif line[5] == 'G':
                line[5] = 'C'
            # check if alleles are now correct after flipping strand
            if line[4] in correct_alleles and line[5] in correct_alleles:
                count_flip += 1
            # if alleles are still not the same as correct forward alleles, change SNP id to '.'
            if line[4] not in correct_alleles or line[5] not in correct_alleles:
                count_tri_allelic += 1
                line[1] = '.'
    else:
        line[1] = '.'
    return line, count_flip, count_tri_allelic


def get_snps_to_extract(line, snps_to_extract, count_kept, count_removed):
    """
    :param line: input row of bim file
    :param snps_to_extract: list with SNPs that should be extracted (are correct SNPs with a SNP id, not '.')
    :param count_kept: number count of extracted SNPs
    :param count_removed: number count of SNPs that will not be extracted, and thus removed
    :return: updated list with SNPs to extract, number count of SNPs to extract and to remove
    """
    if line[1] != '.':  # line[1] is snp id
        snps_to_extract.append(line[1])
        count_kept += 1
    if line[1] == '.':
        count_removed += 1
    return snps_to_extract, count_kept, count_removed


def get_cf3_and_cf4_locations(file):
    """
    :param file: input file with snps in canfam 3 and 4
    :return: dictionaries of snps in canfam3 (snp_id : [chromosome, location] and cf4 (chromosome:basepair : snpid)
    """
    snps_cf3_info = {}
    snps_cf4_info = {}
    for line in file:
        line = split_and_strip(line)
        snps_cf3_info[line[0]] = [line[1], line[2]]
        snps_cf4_info[line[3] + ':' + line[4]] = line[0]
    return snps_cf3_info, snps_cf4_info


def update_location(line, snps_cf3_info):
    """
    :param line: row of input bim file
    :param snps_cf3_info: dictionary of snps in canfam 3
    :return: row with updated location and chromosome
    """
    if line[1] in snps_cf3_info.keys():  # line[1] is SNP id
        line[0] = snps_cf3_info[line[1]][0]  # line[0] is chromosome
        line[3] = snps_cf3_info[line[1]][1]  # line[3] is basepair position
    return line


def main():
    """"
    Creates a new BIM file and a SNPSToExtract list file to use in plink --extract
    """

    # input files
    filename_bim = sys.argv[1]  # input plink .bim file
    filename_forward_snps = 'convert_files/common_files/SNP_Table_Big_Forward.bim'
    filename_cf34 = "convert_files/VCF4/SNPs_CF3_CF4.txt"  # map file with locations in canfam 3 and canfam 4 for liftover

    # output files
    newfile_bim = sys.argv[2] + '.bim'
    snps_to_extract = sys.argv[2] + '_extract.list'

    with open(filename_bim, mode="r") as DataBIM, \
            open(filename_forward_snps, mode="r") as DataForwardSNPs, \
            open(filename_cf34, mode="r") as DataCF34, \
            open(newfile_bim, "w", newline='') as NewFileBIM, \
            open(snps_to_extract, "w", newline='') as NewFileExtractedSNPs:
        writer_extract = csv.writer(NewFileExtractedSNPs, delimiter='\t')
        writer_map = csv.writer(NewFileBIM, delimiter='\t')

        # get dictionary of known SNPs and a dictionary of their forward alleles
        forward_alleles = get_snp_info(DataForwardSNPs)

        # Make dictionary of snp locations canfam 3 and 4
        snps_cf3_info, snps_cf4_info = get_cf3_and_cf4_locations(DataCF34)

        count_flip, count_tri_allelic, count_removed, count_kept, count_false_indel, count_snp_id_not_found, count_indel_shown_as_snp = 0, 0, 0, 0, 0, 0, 0

        snps_to_extract = []
        for line in DataBIM:
            line = split_and_strip(line)
            # add SNP id to known SNPs and divide chromosome 39 over 39 and 41 (pseudo-autosomal)
            line, count_false_indel, count_snp_id_not_found, count_indel_shown_as_snp = get_snp_name_and_update_chromosome(line, snps_cf4_info, count_false_indel, count_snp_id_not_found, count_indel_shown_as_snp)
            # update alleles, flip strand when necessary
            line, count_flip, count_tri_allelic = update_alleles(line, forward_alleles, count_flip, count_tri_allelic)
            line = update_location(line, snps_cf3_info)
            snps_to_extract, count_kept, count_removed = get_snps_to_extract(line, snps_to_extract,
                                                                             count_kept, count_removed)
            writer_map.writerow(line)

        for line in snps_to_extract:
            writer_extract.writerow([line])

        print('Number of strand flips:', count_flip)
        print('Number of SNPs calling wrong alleles:', count_tri_allelic)
        print('Number of snps incorrectly shown as indels:', count_false_indel)
        print('Number of indels SNPs not coding for indel:', count_indel_shown_as_snp)
        print('Number of snps for which no SNP id was found:', count_snp_id_not_found)
        print('Number of snps to remove (wrong alleles + incorrect indels + no SNP-id found):', count_removed)
        print('Number of correct snps:', count_kept)


main()


# get the end time
et = time.time()

# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')