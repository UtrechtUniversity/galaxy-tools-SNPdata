"""
This script:
creates a new .fam file with sex based on SNP data
    based on number of Y calls per sample (high in males, low in females)
reports for which samples the sex was changed
"""

import sys
import csv


def split_and_strip(line, delimiter=None):
    """
    :param line: row of input file
    :param delimiter: the delimiter to use
    :return: stripped and split row
    """
    split_line = line.strip().split(delimiter)
    return split_line


def get_snp_sex(line, snp_sex, y_limit):
    """
    :param line: row of input file
    :param snp_sex: dictionary in format ('sampleID': 'snp_sex')
    :param y_limit: limit for number of SNP calls (100 for embark, 130 for neogen 220k)
    :return: updated dictionary
    """
    # check if number of missing Y calls is under y_limit (male), or above y_limit (female)
    y_calls = int(line[3]) - int(line[2]) # line[2] is number of missing Y calls, line[3] is total number Y SNPs
    if y_calls > y_limit:
        snp_sex[line[1]] = '1'  # is male
    else:
        snp_sex[line[1]] = '2'  # is female
    return snp_sex


def check_sex(line, snp_sex, different_sex, count_sex_changed):
    """
    :param line: row of input file
    :param snp_sex: dictionary in format ('sampleID': 'snp_sex')
    :param different_sex: dictionary in format ('sampleID': ['familyID', 'sampleID', 'SNP sex', 'Original sex']
    :param count_sex_changed: count of how often sex was changed (different sex between .fam en snp sex)
    :return: line with updated sex, dictionary with different sex samples, counts for how often sex changed
    """
    # check if sex in .fam file is different to sex based on snps
    if line[4] != snp_sex[line[1]]:  # line[4] = sex in .fam file
        count_sex_changed += 1
        different_sex[line[1]] = [line[0], line[1], line[4], snp_sex[line[1]]]
        line[4] = snp_sex[line[1]]
    return line, different_sex, count_sex_changed


def report_different_sex(different_sex, count_sex_changed):
    """
    :param different_sex: dictionary in format ('sampleID': ['familyID', 'sampleID', 'SNP sex', 'Original sex']
    :param count_sex_changed: count of how often sex was changed (different sex between .fam en snp sex)
    """
    if count_sex_changed == 0:
        print("For", count_sex_changed, "samples the sex was changed based on SNP data")
    if count_sex_changed != 0:
        print("For", count_sex_changed, "samples the sex was changed based on SNP data")
        print("The samples for which sex was changed are in the _changed_sex.txt file")
        sex_changed = sys.argv[5]
        # write information of samples for which sex changed to file
        with open(sex_changed, "w", newline='') as NewFileSexChanged:
            writer_sex = csv.writer(NewFileSexChanged, delimiter='\t')
            header = ['FamilyID', 'SampleID', 'original_sex', 'SNP_sex']
            writer_sex.writerow(i for i in header)
            for sample in different_sex.keys():
                writer_sex.writerow(different_sex[sample])


def main():
    """ Creates a new FAM file and reports for which dogs the sex was changed
    """
    # input files
    file_missing = sys.argv[2]  # plink .smiss file
    file_fam = sys.argv[3]  # plink .fam file
    # Output files
    new_filename_fam = sys.argv[4]

    y_limit = int(sys.argv[1])
    snp_sex = {}
    with open(file_missing, mode="r") as DataMissing, \
            open(file_fam, mode="r") as DataFAM, \
            open(new_filename_fam, "w", newline='') as NewFileFAM:
        writer_fam = csv.writer(NewFileFAM, delimiter=' ')

        for index, line in enumerate(DataMissing):
            if index == 0:
                continue
            line = split_and_strip(line)
            # get sex based on Y SNPs
            snp_sex = get_snp_sex(line, snp_sex, y_limit)

        count_sex_changed = 0
        different_sex = {}
        for line in DataFAM:
            line = split_and_strip(line, delimiter=' ')
            # check if sex differs between snp sex and fam file
            line, different_sex, count_sex_changed = check_sex(line, snp_sex, different_sex, count_sex_changed)
            writer_fam.writerow(line)

        report_different_sex(different_sex, count_sex_changed)


main()
