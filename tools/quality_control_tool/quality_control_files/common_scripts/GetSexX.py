"""
This script:
creates a new .fam file with sex based on SNP data
    based on proportion of homozygous chromosome X SNP calls
reports for which samples the sex was changed and on how many X snps the sex is based
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


def get_heterozygosity(line, nr_hetero):
    """
    :param line: row of input file
    :param nr_hetero: dictionary in format ('sampleID': nr of heterozygous snps)
    :return: dictionary
    """
    # calculate number of heterozygous SNPs
    hetero = int(line[2])
    nr_hetero[line[1]] = hetero
    return nr_hetero


def get_snp_sex(line, snp_sex, nr_hetero, count_unknown, sex_unknown_ids, low_x_count):
    """
    :param line: row of input file
    :param snp_sex: dictionary in format ('sampleID': 'snp_sex', 'nr_nonmissing_snps')
    :param nr_hetero: dictionary in format ('sampleID': nr of heterozygous snps)
    :param count_unknown: count of how often sex cannot be determined based on SNP data
    :param sex_unknown_ids: list with ids of which no sex is determined
    :param low_x_count: list with ids of which sex was based on 500 or less X SNPs and nr of snps
    :return: updated dictionary
    """
    # calculate number of homozygous SNPs
    nr_nonmissing = int(line[3]) - int(line[2])  # number of X SNPs - number of missing calls
    if nr_nonmissing == 0:  # if no X snps are found
        low_x_count.append(line[0:2] + [nr_nonmissing])
        snp_sex[line[1]] = ['0', nr_nonmissing]  # sex unknown
        count_unknown += 1
        sex_unknown_ids.append([line[0], line[1]])  # line[0] = family id, line[1] = sample id
    else:  # if number of X SNPs is not zero
        nr_heterozygous = nr_hetero[line[1]]
        nr_homozygous = nr_nonmissing - nr_heterozygous
        homozygous_proportion = nr_homozygous / nr_nonmissing
        # check sex based on proportion of homozygous SNPs
        if homozygous_proportion <= 0.970:
            snp_sex[line[1]] = ['2', nr_nonmissing, homozygous_proportion]  # is female
        elif homozygous_proportion > 0.985:
            snp_sex[line[1]] = ['1', nr_nonmissing, homozygous_proportion]  # is male
        else:
            snp_sex[line[1]] = ['0', nr_nonmissing, homozygous_proportion]  # sex unknown
            count_unknown += 1
            sex_unknown_ids.append([line[0], line[1]])
        if nr_nonmissing <= 500:  # if sex check is based on less than 500 X snps
            low_x_count.append(line[0:2] + [nr_nonmissing])
    return snp_sex, count_unknown, sex_unknown_ids, low_x_count


def check_sex(line, snp_sex, different_sex, count_sex_changed):
    """
    :param line: row of input file
    :param snp_sex: dictionary in format ('sampleID': 'snp_sex')
    :param different_sex: dictionary in format ('sampleID': ['familyID', 'sampleID', 'SNP sex', 'Original sex',
    Nr_nonmissing_snps]
    :param count_sex_changed: count of how often sex was changed (different sex between .fam en snp sex)
    :return: line with updated sex, dictionary with different sex samples, counts for how often sex changed
    """
    # check if sex in .fam file is different to sex based on snps
    if line[4] != snp_sex[line[1]][0]:  # line[4] is sex in .fam file
        count_sex_changed += 1  # count how often sex was different
        different_sex[line[1]] = [line[0], line[1], line[4], snp_sex[line[1]][0], snp_sex[line[1]][1], snp_sex[line[1]][2]]
        line[4] = snp_sex[line[1]][0]
    return line, different_sex, count_sex_changed


def report_different_sex(different_sex, count_sex_changed, count_unknown, sex_unknown_ids, low_x_count):
    """
    :param different_sex: dictionary in format ('sampleID': ['familyID', 'sampleID', 'SNP sex', 'Original sex']
    :param count_sex_changed: count of how often sex was changed (different sex between .fam en snp sex)
    :param count_unknown: count of how often sex cannot be determined based on SNP data
    :param sex_unknown_ids: list with ids of which no sex is determined
    :param low_x_count: list with ids of which sex was based on 500 or less X SNPs and nr of snps
    """
    if count_sex_changed == 0:
        print("For", count_sex_changed, "samples the sex was changed based on SNP data")
    if count_sex_changed != 0:
        print("\nFor", count_sex_changed, "samples the sex was changed based on SNP data")
        print("The samples for which sex was changed are in the _changed_sex.txt file")
        print("\nFor", count_unknown, "samples the sex could not be determined based on SNP data")
        if count_unknown != 0:
            print("Samples for which no sex could be determined: ")
            for ids in sex_unknown_ids:
                print(ids[0], ids[1])
        if len(low_x_count) != 0:
            print("\nWARNING: for", len(low_x_count), "samples sex was based on 500 or less X SNPs. Samples and "
                                                      "number of X SNPs:")
            for sample in low_x_count:
                print(sample[0], sample[1], sample[2])
        sex_changed = sys.argv[5]
        with open(sex_changed, "w", newline='') as NewFileSexChanged:
            writer_sex = csv.writer(NewFileSexChanged, delimiter='\t')
            header = ['FamilyID', 'SampleID', 'original_sex', 'SNP_sex', 'nr_nonmissing_X_SNPs', "percentage_homozygous"]
            writer_sex.writerow(i for i in header)
            for sample in different_sex.keys():
                writer_sex.writerow(different_sex[sample])


def main():
    """ Creates a new FAM file and reports for which dogs the sex was changed
    """
    # input files
    file_het = sys.argv[1]  # plink .scount file
    file_missing = sys.argv[2]  # plink .smiss file
    file_fam = sys.argv[3]  # plink .fam file
    # Output files
    new_filename_fam = sys.argv[4]

    nr_hetero = {}
    snp_sex = {}
    count_unknown = 0
    sex_unknown_ids = []
    low_x_count = []
    with open(file_missing, mode="r") as DataMissing, \
            open(file_het, mode="r") as DataHet, \
            open(file_fam, mode="r") as DataFAM, \
            open(new_filename_fam, "w", newline='') as NewFileFAM:
        writer_fam = csv.writer(NewFileFAM, delimiter=' ')

        for index, line in enumerate(DataHet):
            if index == 0:
                continue
            line = split_and_strip(line)
            # get number of heterozygous X SNPs
            nr_hetero = get_heterozygosity(line, nr_hetero)

        for index, line in enumerate(DataMissing):
            if index == 0:
                continue
            line = split_and_strip(line)
            # get sex based on X chromosome SNP homozygosity
            snp_sex, count_unknown, sex_unknown_ids, low_x_count = get_snp_sex(line, snp_sex, nr_hetero, count_unknown, sex_unknown_ids, low_x_count)

        count_sex_changed = 0
        different_sex = {}
        for line in DataFAM:
            line = split_and_strip(line, delimiter=' ')
            # check if sex differs between snp sex and fam file
            line, different_sex, count_sex_changed = check_sex(line, snp_sex, different_sex, count_sex_changed, )
            writer_fam.writerow(line)

        report_different_sex(different_sex, count_sex_changed, count_unknown, sex_unknown_ids, low_x_count)


main()
