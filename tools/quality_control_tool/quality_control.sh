#!/bin/bash
# To ensure clean and good quality data, quality control steps need to be performed.
# This command line tool can be used to perform multiple quality control checks:
#   sample call rate, sex check, duplicate sample check, breed check.
#
start=$(date +%s)
i_option=0
e_option=0
a_option=0
o_option=0
f_option=0
p_option=0
h_option=0
s_option=0
b_option=0
d_option=0
m_option=0

# Extra arguments for Galaxy
x_option=0

# define options and capture input
while getopts ":i:e:a:x:o:f:m:sdb:hp:" option; do
  case $option in
    i)  # input flag for .bim file
      file_bim="$OPTARG"
      i_option=1
      ;;
    e)  # input flag for .bed file
      file_bed="$OPTARG"
      e_option=1
      ;;
    a)  # input flag for .fam file
      file_fam="$OPTARG"
      original_name="${file_fam%.*}"
      a_option=1
      ;;
    o)  # flag for the new output file name and log file
      file_new="$OPTARG"
      log_file="${file_new}_Log.txt"
      o_option=1
      ;;
    f) # flag for input files if they have the same name
      file="$OPTARG"
      file_bim="$file.bim"
      file_bed="$file.bed"
      file_fam="$file.fam"
      original_name="$file"
      f_option=1
      ;;
    s) # flag to check sex of samples
      s_option=1;;
    b) # flag to check breed of samples and which method for tree construction to use
      method_tree="$OPTARG"
      b_option=1
      ;;
    d) # flag to check for duplicate samples
      d_option=1;;
    m) # flag for prefix input file snp database
      database="$OPTARG"
      database_bim="$database.bim"
      database_bed="$database.bed"
      database_fam="$database.fam"
      m_option=1
      ;;
    p) # flag for defining platform
      platform="$OPTARG"
      p_option=1
      ;;
    h) #flag for help
      h_option=1;;
    x)  # input flag for tool path
      tool_directory="$OPTARG"
      x_option=1
      ;;
    \?)
      echo "Unknown option: -$OPTARG" >&2; exit 1 ;;
    :)
      echo "Missing option argument for -$OPTARG" >&2; exit 1 ;;
    *)
      echo "Missing option: -$option" >&2; exit 1 ;;

  esac
done

# error if no options were used
if ((OPTIND ==1)); then
  echo "ERROR: No options were specified"
  echo "Use bash quality_control.sh -h for help"
  exit 1
fi

shift "$(( OPTIND -1 ))"

# output for help option -h
if [ $h_option -eq 1 ]; then
  echo "USAGE: bash quality_control.sh [-i|e|a|o|f|s|d|m|b|p|h]"
  echo -e "Author: Marilijn van Rumpt - marilijn@live.nl (2024)"
  echo -e "\nStandard performed quality step for all platforms except for 'merged': sample call rate check to remove bad quality samples"
  echo -e "Optional quality steps to perform: sex check, duplicate check, breed check"
  echo -e "\nSYNTAX OPTIONS:"
  echo -e "\t-i <filename.bim> \tSpecify full name of .bim file, use -i, e, a together"
  echo -e "\t-e <filename.bed> \tSpecify full name of .bed file"
  echo -e "\t-a <filename.fam> \tSpecify full name of .fam file"
  echo -e "\t-o <prefix_filename> \tSpecify prefix for output files. Obligatory."
  echo -e "\t-f <prefix_filename> \tSpecify prefix for .bed + .fam + .bim file, can be used instead of option -i, e, a"
  echo -e "\t-p <platform> \t\tSpecify platform, options: embark, neogen170, neogen220, lupa170, mdd, wisdom, vcf3, vcf4, affymetrix, merged, other. Obligatory."
  echo -e "\t-s \t\t\tExecute sex check"
  echo -e "\t-d \t\t\tExecute duplicate check within input file"
  echo -e "\t-m <prefix_filename>\tSpecify prefix for .bed + .fam + .bim file"
  echo -e "\t\t\t\tAnd execute duplicate check between specified file in -m and file in option -f or -i, e, a"
  echo -e "\t\t\t\tUse in combination with -d"
  echo -e "\t-b <method_tree_construction>\tExecute breed check"
  echo -e "\t\t\t\tSpecify method to construct tree, options are: phylip and biopython"
  echo -e "\t-h \t\t\tPrint the help overview \n"
  echo "EXAMPLES:"
  echo -e "\tbash quality_control.sh -f inputfile -p neogen170 -o newfilename"
  echo -e "\tbash quality_control.sh -f inputfile -p embark -s -d -o newfilename"
  echo -e "\tbash quality_control.sh -f inputfile -p embark -s -d -m second_inputfile -o newfilename"
  echo -e "\tbash quality_control.sh -a inputfile.fam -i inputfile.bim -e inputfile.bed -p mdd -o newfilename\n"
  echo -e "\tbash quality_control.sh -f inputfile -p neogen220 -b phylip -o newfilename\n"
  echo "DEPENDENCIES NEEDED:"
  echo -e "\tpython3 with package biopython if chosen tree construction method is biopython"
  echo -e "\tplink 1.9 (included in this tool)"
  echo -e "\tplink 2 (included in this tool)\n"
  echo -e "\tPhylip's programs neighbor (included in this tool) if chosen tree construction method is phylip"
  echo "ADDITIONAL INFORMATION OF OPTIONS:"
  echo -e "\tIf no optional options (s, d, m, b) are used, only check for sample call rate is performed"
  echo -e "\tFor all platforms:"
  echo -e "\t\tFor specifying input files, use either -i, e, a together, or only -f."
  echo -e "\t-p merged:"
  echo -e "\t\tWARNING: when input is a merged dataset, call rate of samples is NOT checked. If merged dataset contains"
  echo -e "\t\tbad quality samples, the check for sex, breed and duplicates/relatedness is not reliable. Always perform quality control"
  echo -e "\t\tsteps on each individual dataset before merging.\n"
  echo "TYPE OF SEX DETERMINATION PER PLATFORM:"
  echo -e "\tSex check based on number of Y SNP calls:"
  echo -e "\t\tembark and neogen220"
  echo -e "\tSex check based on proportion homozygous SNPs on X chromosome:"
  echo -e "\t\tneogen170, lupa170, wisdom, affymetrix, vcf3, vcf4, merged, other"
  exit 1
fi

# Error if no output name was given
if [ $o_option -ne 1 ]; then
  echo "ERROR: no output file name was given."
  exit 1
fi

# Error if no platform was given
if [ $p_option -ne 1 ]; then
  echo "ERROR: no platform was given, choose from embark, neogen170, neogen220, lupa170, mdd,
  wisdom, vcf3, vcf4, affymetrix, merged, other."
  exit 1
fi

# Error if not all input files are found
if ! [ -f "${file_bim}" ] || ! [ -f "${file_fam}" ] || ! [ -f "${file_bed}" ]; then
  echo "ERROR: one of these files is not found: ${file_bim}, ${file_fam} or ${file_bed}"
  exit 1
fi

# Error if not all input files used in -m are found
if [ $m_option -eq 1 ]; then
  if ! [ -f "${database_bim}" ] || ! [ -f "${database_fam}" ] || ! [ -f "${database_bed}" ]; then
    echo "ERROR: one of these files is not found: ${database_bim}, ${database_fam} or ${database_bed}"
    exit 1
  fi
fi

# Check if given platform is a valid option
platform_options=(embark neogen170 neogen220 mdd wisdom lupa170 vcf3 vcf4 affymetrix merged other)
if ! printf '%s\0' "${platform_options[@]}" | grep -Fzxq -- "$platform"; then
  echo "ERROR: wrong platform was given, choose from embark, neogen170, neogen220, lupa170, mdd,
  wisdom, vcf3, vcf4, affymetrix, merged, other."
  exit 1
fi

if [ -f outfile ]; then
  echo "ERROR: filename outfile already exists, remove this file or change its name"
  exit 1
  # phylip program automatically names output file outfile. So this file should not exist already
fi

if [ -f outtree ]; then
  echo "ERROR: filename outtree already exists, remove this file or change its name"
  exit 1
  # phylip program automatically names output file outtree. So this file should not exist already
fi

if [ $b_option -eq 1 ]; then
  tree_construction_options=(phylip biopython)
  if ! printf '%s\0' "${tree_construction_options[@]}" | grep -Fzxq -- "$method_tree"; then
    echo "ERROR: wrong method for tree construction was given in -b, options: phylip or biopython"
    exit 1
  fi
fi

# check if plink executable is present
if ! [ -f ""${tool_directory}"/quality_control_files/common_scripts/plink" ] || ! [ -f ""${tool_directory}"/quality_control_files/common_scripts/plink2" ] ; then
  echo "ERROR: plink or plink2 was not found. This executable should be in directory "${tool_directory}"/quality_control_files/common_scripts."
  exit 1
fi

# Check if python3 is installed
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 is not installed" >&2; exit 1;}

# Error if chosen new file name already exists
if [ -f "$file_new.bim" ] || [ -f "$file_new.bed" ] || [ -f "$file_new.fam" ]  \
|| [ -f "${file_new}_Log.txt" ]; then
  echo "ERROR: filename containing $file_new already exists, change -o output name or remove this file"
  exit 1
fi

# Error if chosen new file name already exists, specifically for files produced with -d
if [ $d_option -eq 1 ] && { [ -f "${file_new}_between_files_duplicate_summary.txt" ]  \
|| [ -f "${file_new}_between_files_kinship.kin0" ] || [ -f "${file_new}_kinship.kin0" ]  \
|| [ -f "${file_new}_duplicate_summary.txt" ]; }; then
  echo "ERROR: filename containing $file_new _duplicate_summary or $file_new _kinship already exists,
  change -o output name, or remove these files"
  exit 1
fi

# Error if option -m is not used in combination with -d
if [ $m_option -eq 1 ] && [ $d_option -ne 1 ]; then
  echo "ERROR: option -m can only be used in combination with -d"
  exit 1
fi


rm -r "${tool_directory}"/quality_control_files/temp_files # empty temp_files folder
# create directory for temporary files, if directory not already exists
mkdir -p "${tool_directory}"/quality_control_files/temp_files

# check if temporary output file names already exist
if [[ -n $(shopt -s nullglob; echo "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_temp*) ]]; then
  echo "ERROR: filename ${file_new}_temp(123) for the temporary output file in the temp_files folder already exists, remove or change location of this file." 2>&1 | tee -a "$log_file"
  exit 1
fi
# check if _bad_sample output file names already exist
if [[ -n $(shopt -s nullglob; echo "${file_new}"_bad_sample* ) ]]; then
  echo "ERROR: filename ${file_new}_bad_sample already exists, remove or change location of this file." 2>&1 | tee -a "$log_file"
  exit 1
fi

# Error if neither separate bed bim fam files were given or the -f option was used
if [[ ($((i_option + e_option + a_option)) -ne 3 && $f_option -ne 1)  \
|| ($((i_option + e_option + a_option)) -ne 0 && $f_option -eq 1) ]]; then
  echo "ERROR: use either options i,e,a together or only f." 2>&1 | tee -a "$log_file"
  exit 1
fi

{
# Printing the the chosen options in the log of the bash script
echo -e "Log of bash script quality_control.sh on $(date)"
echo -e "Author: Marilijn van Rumpt - marilijn@live.nl (2024)\n\nThe following options were used: \n"
if [ $p_option -eq 1 ]; then echo -e "-p $platform"; fi
if [ $i_option -eq 1 ]; then echo -e "-i $file_bim"; fi
if [ $e_option -eq 1 ]; then echo -e "-e $file_bed"; fi
if [ $a_option -eq 1 ]; then echo -e "-a $file_fam"; fi
if [ $f_option -eq 1 ]; then echo -e "-f $file"; fi
if [ $s_option -eq 1 ]; then echo -e "-s"; fi
if [ $b_option -eq 1 ]; then echo -e "-b $method_tree"; fi
if [ $d_option -eq 1 ]; then echo -e "-d"; fi
if [ $m_option -eq 1 ]; then echo -e "-m $database" ; fi
if [ $o_option -eq 1 ]; then echo -e "-o $file_new"; fi

# Printing data summary: number of samples and number of snps
number_samples=$(wc -l < "$file_fam")
echo -e "\nNumber of samples: $number_samples"
number_snps=$(wc -l < "$file_bim")
echo -e "Number of SNPs: $number_snps"

} 2>&1 | tee -a "$log_file" # put output in log file

# check if there are duplicate sample IDs in the input .fam file
duplicate_ids=$(sort -k2n "$file_fam" | awk 'a[$2]++{ if(a[$2]==2){ print b }; print $0 }; {b=$0}')
    if [ ! -z "$duplicate_ids" ]; then
      echo -e "\nDuplicate sample IDs in $file_fam:" 2>&1 | tee -a "$log_file"
      echo -e "$duplicate_ids" 2>&1 | tee -a "$log_file"
      echo -e "ERROR: duplicate ID(s) found in $file_fam file. Make sure all individual sample IDs are unique." 2>&1 | tee -a "$log_file"
      echo -e "Further checks could not be performed because of the duplicate IDs." 2>&1 | tee -a "$log_file"
      exit 1
    fi

# action to perform is chosen platform is not 'merged'
if [ "$platform" != 'merged' ]; then
  {
  # actions to perform if platform is embark or neogen220
  if [ "$platform" = 'embark' ] || [ "$platform" = 'neogen220' ]; then
    # set variables needed for removal of bad Y snps in embark and neogen 220K
    if [ "$platform" = 'embark' ]; then
        y_nr="46"
        bad_y_file=""${tool_directory}"/quality_control_files/embark/EmbarkYSNPsFemales.list"
    fi
    if [ "$platform" = 'neogen220' ]; then
        y_nr="49"
        bad_y_file=""${tool_directory}"/quality_control_files/neogen220/Neogen220YSNPsFemales.list"
    fi

    echo -e "\n\n--- Checking quality of samples using sample call rate"
    echo -e "Using plink for removing bad samples (sample call rate under 90%) and $y_nr bad Y snps (call Y alleles in females)"

    # checking for sample call rate >90% and removing bad Y SNPs
    "${tool_directory}"/quality_control_files/common_scripts/plink  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bed "$file_bed"  \
    --make-bed  \
    --mind 0.1  \
    --exclude $bad_y_file  \
    --allow-no-sex  \
    --chr-set 38  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp"  \
    --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.log" >> "$log_file"

  # actions to perform is platform is not embark or neogen220 or merged
  else
    echo -e "\n\n--- Checking quality of samples using sample call rate"
    echo -e "Using plink for removing bad samples (sample call rate under 90%)"
    # using plink to remove samples with callrate under 90%
    "${tool_directory}"/quality_control_files/common_scripts/plink  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bed "$file_bed"  \
    --make-bed  \
    --mind 0.1  \
    --chr-set 38  \
    --allow-no-sex  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp"  \
    --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.log" >> "$log_file"

  fi

  # get sample call rate if sample failed (less than 90% call rate)
  if [ -f ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.irem" ]; then # check if file with removed samples exists
    echo -e "Using plink2 for getting SNP call rate of removed bad samples"
    "${tool_directory}"/quality_control_files/common_scripts/plink2  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bed "$file_bed"  \
    --make-bed  \
    --missing sample-only 'scols=maybefid,nmiss,nobs,fmiss'  \
    --keep ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.irem"  \
    --allow-no-sex  \
    --chr-set 38  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_bad_sample"  \
    --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_bad_sample.log" >> "$log_file"
    echo -e "\nThe samples which were removed and the percentage missing SNPs per sample: "
    # get the sample call rate of the removed samples and report this
    awk 'NR!=1{$1=$1;print$1,$2,"has sample missing rate of",$5*100,"%"}' ""${tool_directory}"/quality_control_files/temp_files/${file_new}_bad_sample.smiss"
    mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_bad_sample.fam" "${file_new}_bad_sample.fam"
    mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_bad_sample.bed" "${file_new}_bad_sample.bed"
    mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_bad_sample.bim" "${file_new}_bad_sample.bim"
    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_bad_sample*
  else
    echo -e "\nNo samples were removed because of a bad sample call rate"
  fi
  mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.bim" "$file_new.bim"
  mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.bed" "$file_new.bed"
  mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.fam" "$file_new.fam"
  rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_temp*

  } 2>&1 | tee -a "$log_file" # put output in log file

  file_bim="$file_new.bim"
  file_fam="$file_new.fam"
  file_bed="$file_new.bed"
# actions to perform is platform is 'merged'
else
  echo -e " \nWARNING: when input is a merged dataset, call rate of samples is NOT checked. If merged dataset contains
  bad quality samples, the check for sex, breed and duplicates/relatedness is not reliable.
  Always perform quality quality_control steps on each individual dataset before merging."
  # check if optional checks were used for merged file, if not, give error because no checks get executed
  if [ $s_option -ne 1 ] && [ $d_option -ne 1 ] && [ $b_option -ne 1 ]; then
    echo -e "\nERROR: no quality control checks are performed for -p merged, if -s, d or b is not used."
    echo "The standard sample call rate check is not performed for -p merged."
    rm "$log_file"
    exit 1
  fi
fi

# execute when s option for sex check is used
if [ $s_option -eq 1 ]; then
  # set variable for Y call limit for embark and neogen220K, is used in script GetSexY.py
  if [ "$platform" = 'embark' ] || [ "$platform" = 'neogen220' ]; then
    if [ "$platform" = 'embark' ]; then
        y_limit="100"
    fi
    if [ "$platform" = 'neogen220' ]; then
        y_limit="130"
    fi
    {
    echo -e "\n\n--- Performing sex check based on number of Y SNP calls"

    # get number of Y alleles called per sample to determine sex
    echo -e "Using plink2 for getting Y calls per sample to determine sex"
    "${tool_directory}"/quality_control_files/common_scripts/plink2  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bed "$file_bed"  \
    --missing sample-only 'scols=maybefid,nmiss,nobs,fmiss'  \
    --chr-set 40  \
    --chr 40  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3"  \
    --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3.log" >> "$log_file"

    # execute python script to check if sex is correct
    echo -e "Using python script GetSexY.py to check if sex in $original_name.fam is same as SNP sex"
    python3 "${tool_directory}"/quality_control_files/common_scripts/GetSexY.py  \
    $y_limit  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3.smiss"  \
    "$file_fam"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3.fam"  \
    "${file_new}_sex_changed.txt"

    # check if file with new filename already exists, if not, change input file name to new file name for .bim and .bed
    if [ "$file_bim" !=  "$file_new.bim" ]; then
      cp "$file_bim" "$file_new.bim"
      cp "$file_bed" "$file_new.bed"
    fi
    mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3.fam" "$file_new.fam"
    # remove temporary file
    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_temp*
    } 2>&1 | tee -a "$log_file" # put output in log file

    file_bim="$file_new.bim"
    file_fam="$file_new.fam"
    file_bed="$file_new.bed"
  fi

  # sex check based on X snps for Neogen 170K, Lupa 170K, wisdom, vcf, affymetrix, mdd, merged, other
  platform_sexx=(neogen170 wisdom lupa170 vcf3 vcf4 affymetrix merged mdd other)
  if printf '%s\0' "${platform_sexx[@]}" | grep -Fzxq -- "$platform"; then # check if selected platform -p is in platform list
    echo -e "\n\n--- Performing sex check based on X SNP homozygosity"
    # check if .bim file contains X snps
    sex_SNPs_available=$(awk '$1==39 {print $1}' "$file_bim")
    if [ -z "$sex_SNPs_available" ]; then
      echo -e "ERROR: no X snps (chromosome 39) found in $file_bim" 2>&1 | tee -a "$log_file"
      exit 1
    fi
    {
    # get number of homozygous and heterozygous X alleles per sample to determine sex
    echo -e "Using plink2 for getting number of homozygous X SNPs "
    "${tool_directory}"/quality_control_files/common_scripts/plink2  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bed "$file_bed"  \
    --missing sample-only 'scols=maybefid,nmiss,nobs,fmiss'  \
    --sample-counts 'cols=maybefid,hetsnp'  \
    --chr-set 40  \
    --chr 39  \
    --allow-no-sex  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp2"  \
    --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp2.log" >> "$log_file"

    # execute python script to check if sex is correct
    echo -e "Using python script GetSexX.py to check if sex in $original_name.fam is same as SNP sex"
    python3 "${tool_directory}"/quality_control_files/common_scripts/GetSexX.py  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp2.scount"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp2.smiss"  \
    "$file_fam"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3.fam"  \
    "${file_new}_sex_changed.txt"

    mv ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp3.fam" "$file_new.fam"
    # check if file with new filename already exists, if not, change input file name to new file name for .bim and .bed
    if [ "$file_bim" !=  "$file_new.bim" ]; then
      cp "$file_bim" "$file_new.bim"
      cp "$file_bed" "$file_new.bed"
    fi
    # remove temporary file
    rm ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp"*
    } 2>&1 | tee -a "$log_file" # put output in log file

    file_bim="$file_new.bim"
    file_fam="$file_new.fam"
    file_bed="$file_new.bed"

  fi
  echo -e "\nFollowing sex coding is used:"
  echo -e "Male = 1"
  echo -e "Female = 2"
  echo -e "Unknown = 0"
fi

# Execute when d option for duplicate check is used
if [ $d_option -eq 1 ]; then
  echo -e "\n\n--- Checking for duplicate samples and first degree relations within input file $original_name" 2>&1 | tee -a "$log_file"
  # check if input file contains more than 1 sample
  if [[ $(wc -l < "$file_fam") -eq 1 ]]; then
    echo -e "$original_name.fam file only contains 1 sample, so duplicate checks within input file are skipped." 2>&1 | tee -a "$log_file"
  else # if input file contains more than 1 sample, execute duplicate check
    {
    echo -e "Using plink2 to get kinship scores of samples in input file $original_name"
    # use plink2 to make a kinship table with scores higher than 0.1875
    "${tool_directory}"/quality_control_files/common_scripts/plink2  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bed "$file_bed"  \
    --make-king-table  \
    --king-table-filter 0.1875  \
    --chr-set 38  \
    --out "${file_new}_kinship"  \
    --silent
    cat "${file_new}_kinship.log" >> "$log_file"
    rm "${file_new}_kinship.log"

    # get number of kinship scores by counting rows in file
    number_kinship_scores=$(wc -l < "${file_new}_kinship.kin0")
    if [ "$number_kinship_scores" -eq 1 ]; then # if no kinship scores are found
      echo -e "\nNo duplicates or first degree relation kinship scores found within $original_name"
      rm "${file_new}_kinship.kin0"
    else # if kinship scores were found
      echo -e "\nKinship scores higher than 0.1875 have been found within $original_name"
      echo -e "See ${file_new}_kinship.kin0 for kinship scores.\n"
      # get duplicate samples with kinship score higher than 0.4
      duplicate_kin=$(awk 'FNR==1{next} $8>0.4 {print $1,$2,$3,$4,$8}' "${file_new}_kinship.kin0")
      if [ ! -z "$duplicate_kin" ]; then # if variable duplicate_kin is not empty (thus contains duplicates)
        # Put duplicate samples in temporary file
        echo -e "$duplicate_kin" > ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates.txt"
        # Put ids of duplicate samples in temporary list file, which can be used in plink to extract these samples
        duplicate_kin1=$(awk 'FNR==1{next} $8>0.4 {print $1,$2}' "${file_new}_kinship.kin0")
        duplicate_kin2=$(awk 'FNR==1{next} $8>0.4 {print $3,$4}' "${file_new}_kinship.kin0")
        echo -e "$duplicate_kin1\n""$duplicate_kin2" > ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates.list"

        # for duplicate samples, get number of SNPs per sample
        echo -e "Using plink2 to get number of successfully genotyped SNPs"
        "${tool_directory}"/quality_control_files/common_scripts/plink2  \
        --bim "$file_bim"  \
        --fam "$file_fam"  \
        --bed "$file_bed"  \
        --missing sample-only 'scols=maybefid,nmiss,nobs,fmiss'  \
        --keep ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates.list"  \
        --allow-no-sex  \
        --chr-set 60  \
        --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates_missing"  \
        --silent
        cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates_missing.log" >> "$log_file"

        # make a summary for duplicate samples
        echo -e "Using python script GetDuplicateInfo.py to get duplicate samples summary"
        python3 "${tool_directory}"/quality_control_files/common_scripts/GetDuplicateInfo.py  \
        ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates.txt"  \
        ""${tool_directory}"/quality_control_files/temp_files/${file_new}_duplicates_missing.smiss"  \
        "${file_new}_duplicate_summary.txt"

        echo -e "\nDuplicate samples based on kinship within input file $original_name:"
        cat "${file_new}_duplicate_summary.txt"

        echo -e "\nNOTE: no duplicate samples are removed from the input file.
        Based on the given information, the user should decide further actions for duplicate samples."

        rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_duplicates*
      else # if variable duplicate_kin is empty (thus contains no duplicates)
        echo -e "No duplicates found within input file $original_name based on kinship"
      fi
    fi
    } 2>&1 | tee -a "$log_file" # put output in log file
  fi
  # execute when -m option is used
  if [ $m_option -eq 1 ]; then
    echo -e "\n\n--- Checking for duplicate samples and first degree relations between input file $original_name and second file $database"
    # get duplicate IDs out of .fam used in the -m option
    duplicate_ids=$(sort -k2n "$database_fam" | awk 'a[$2]++{ if(a[$2]==2){ print b }; print $0 }; {b=$0}')
    if [ ! -z "$duplicate_ids" ]; then # if variable duplicate_kin is not empty (thus contains duplicates)
      echo -e "Duplicate sample IDs found in $database_fam:" 2>&1 | tee -a "$log_file"
      echo -e "$duplicate_ids" 2>&1 | tee -a "$log_file"
      echo -e "ERROR: duplicate ID(s) found in $database_fam file. Make sure all individual sample IDs are unique." 2>&1 | tee -a "$log_file"
      echo -e "Further duplicate check could not be performed because of the duplicate IDs." 2>&1 | tee -a "$log_file"
      exit 1
    else
      echo -e "\nNo duplicate sample IDs found in $database_fam\n" 2>&1 | tee -a "$log_file"
    fi

    {
    # check if duplicate IDs exists between first (-f or -i,a,e) and second file (-m), and if they exist, create temporary unique ID
    echo -e "Using python script GetDuplicateIDs.py to check for duplicate IDs between $original_name.fam and $database.fam"
    python3 "${tool_directory}"/quality_control_files/common_scripts/CheckDuplicateIDs.py  \
    "$file_fam"  \
    "$database_fam"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.fam"
    } 2>&1 | tee -a "$log_file" # put output in log file

    # Merge the first (-f or -i,a,e) and second file (-m)
    echo -e "Using plink to merge $original_name and $database"
    "${tool_directory}"/quality_control_files/common_scripts/plink  \
      --allow-no-sex  \
      --bed "$file_bed"  \
      --bim "$file_bim"  \
      --fam ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.fam"  \
      --bmerge "$database_bed" "$database_bim" "$database_fam"  \
      --chr-set 38  \
      --make-bed  \
      --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge"  \
      --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.log" >> "$log_file"

    {
    echo -e "Using plink2 to get kinship scores of samples in merged file of $original_name and $database"
    # use plink2 to make a kinship table with scores higher than 0.1875
    "${tool_directory}"/quality_control_files/common_scripts/plink2  \
    --bim ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.bim"  \
    --fam ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.fam"  \
    --bed ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.bed"  \
    --make-king-table  \
    --king-table-filter 0.1875  \
    --king-table-require ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.fam"  \
    --chr-set 38  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_temp_kinship"  \
    --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_temp_kinship.log" >> "$log_file"

    echo -e "Using python script ExtractKinshipScores.py to extract sample pairs between $original_name and $database"
    # extract sample pairs between the first (-f or -i,a,e) and second file (-m), the sample pairs within the first file are removed.
    python3 "${tool_directory}"/quality_control_files/common_scripts/ExtractKinshipScores.py  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_temp.fam"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_temp_kinship.kin0"  \
    "${file_new}_between_files_kinship.kin0"

    # get number of kinship scores by counting rows in file
    number_kinship_scores=$(wc -l < "${file_new}_between_files_kinship.kin0")
    if [ "$number_kinship_scores" -eq 1 ]; then # if no kinship scores are found
      echo -e "\nNo duplicates or first degree relation kinship scores found between $original_name and $database"
      rm "${file_new}_between_files_kinship.kin0"
    else # if kinship scores were found
      echo -e "\nKinship scores higher than 0.1875 have been found between samples of $original_name and $database"
      echo -e "See ${file_new}_between_files_kinship.kin0 for kinship scores.\n"
      # get duplicate samples with kinship score higher than 0.4
      duplicate_kin=$(awk 'FNR==1{next} $8>0.4 {print $1,$2,$3,$4,$8}' "${file_new}_between_files_kinship.kin0")
      if [ ! -z "$duplicate_kin" ]; then # if variable duplicate_kin is not empty (thus contains duplicates)
        # Put duplicate samples in temporary file
        echo -e "$duplicate_kin" > ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates.txt"

        # make arrays of duplicate samples, put sample ID in the array
        duplicate_kin1=$(awk 'FNR==1{next} $8>0.4 {print $1,$2}' "${file_new}_between_files_kinship.kin0")
        duplicate_kin2=$(awk 'FNR==1{next} $8>0.4 {print $3,$4}' "${file_new}_between_files_kinship.kin0")
        duplicate_kin3=("${duplicate_kin1[@]}" "${duplicate_kin2[@]}") # add arrays together
        duplicate_kin4=$(printf "%s\n" "${duplicate_kin3[@]}" | sort -u) # get unique samples

        # Put ids of duplicate samples in temporary list file, which can be used in plink to extract these samples
        echo -e "$duplicate_kin4" > ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates.list"

        # for duplicate samples, get number of SNPs per sample
        echo -e "Using plink2 to get number of successfully genotyped SNPs"
        "${tool_directory}"/quality_control_files/common_scripts/plink2  \
        --bim ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.bim"  \
        --fam ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.fam"  \
        --bed ""${tool_directory}"/quality_control_files/temp_files/${file_new}_merge.bed"  \
        --missing sample-only 'scols=maybefid,nmiss,nobs,fmiss'  \
        --keep ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates.list"  \
        --allow-no-sex  \
        --chr-set 60  \
        --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates_missing"  \
        --silent
        cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates_missing.log" >> "$log_file"

        # make a summary for duplicate samples
        echo -e "Using python script GetDuplicateInfo.py to get duplicate samples summary"
        python3 "${tool_directory}"/quality_control_files/common_scripts/GetDuplicateInfo.py  \
        ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates.txt"  \
        ""${tool_directory}"/quality_control_files/temp_files/${file_new}_between_files_duplicates_missing.smiss"  \
        "${file_new}_between_files_duplicate_summary.txt"

        echo -e "\nDuplicate samples based on kinship in merged $original_name and $database:"
        cat "${file_new}_between_files_duplicate_summary.txt"

        echo -e "\nNOTE: no duplicate samples are removed from the input file.
        Based on the given information, the user should decide further actions for duplicate samples."

        rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_between_files_duplicates*
      else # if variable duplicate_kin is empty (thus contains no duplicates)
        echo -e "No duplicates found between $original_name and $database based on kinship"
      fi
    fi
    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}"_between_files_temp_kinship*
    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}_"merge*
    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}_"temp*
    } 2>&1 | tee -a "$log_file" # put output in log file
  fi
fi

if [ $b_option -eq 1 ]; then
  {
  echo -e "\n\n--- Performing the breed check"
  echo -e "Using python script GetInnerJoin.py to extract SNPs in common between $original_name and breed database"
  python3 "${tool_directory}"/quality_control_files/common_scripts/GetInnerJoin.py  \
    ""${tool_directory}"/quality_control_files/breed_database/Dogs_for_tree.bim"  \
    "$file_bim"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_innerjoin.list"

  innerjoin_size=$(wc -l < ""${tool_directory}"/quality_control_files/temp_files/${file_new}_innerjoin.list")
  echo "Number of common SNPs: $innerjoin_size"
  } 2>&1 | tee -a "$log_file" # put output in log file

  {
  # Merge the breed_database and the input file
  echo -e "Using plink to merge $original_name and the breed database"
  "${tool_directory}"/quality_control_files/common_scripts/plink  \
    --allow-no-sex  \
    --bed "$file_bed"  \
    --bim "$file_bim"  \
    --fam "$file_fam"  \
    --bmerge ""${tool_directory}"/quality_control_files/breed_database/Dogs_for_tree.bed"   \
    ""${tool_directory}"/quality_control_files/breed_database/Dogs_for_tree.bim"   \
    ""${tool_directory}"/quality_control_files/breed_database/Dogs_for_tree.fam"  \
    --extract ""${tool_directory}"/quality_control_files/temp_files/${file_new}_innerjoin.list"  \
    --chr-set 38  \
    --make-bed  \
    --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_merge"  \
    --silent
  cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_merge.log" >> "$log_file"

  rm ""${tool_directory}"/quality_control_files/temp_files/${file_new}_innerjoin.list"
  } 2>&1 | tee -a "$log_file" # put output in log file
  if [ "$method_tree" = 'biopython' ]; then
    {
    # Check if biopython python package is installed
    python3 -c "import pkgutil; exit(0 if pkgutil.find_loader('Bio') else 1)"
    if [ $? -eq 1 ]; then
      echo "ERROR: required python package 'biopython' is not installed" 2>&1 | tee -a "$log_file"
      echo "Use 'sudo pip3 install biopython' in terminal" 2>&1 | tee -a "$log_file"
      exit 1
    fi

    # Make a distance matrix of the merged file
    echo -e "Using plink to make a distance matrix of the merged file"
    "${tool_directory}"/quality_control_files/common_scripts/plink  \
      --allow-no-sex  \
      --bfile ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_merge"  \
      --distance triangle 1-ibs  \
      --chr-set 38  \
      --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance"  \
      --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance.log" >> "$log_file"

    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}_"breed_merge*

    echo -e "\nUsing python script MakeTree.py to create a phylogenetic tree"
    python3 "${tool_directory}"/quality_control_files/common_scripts/MakeTree.py  \
        ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance.mdist"  \
        ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance.mdist.id"  \
        "${file_new}_tree.nwk"  \
        "$file_fam"  \
        "${file_new}_tree.png"  \
        "${file_new}_tree_annotation.txt"  \
        "linux"
    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}_"breed_distance*
  } 2>&1 | tee -a "$log_file" # put output in log file
  fi

  if [ "$method_tree" = 'phylip' ]; then
    {
    # check if phylip executables are present
    if ! [ -f ""${tool_directory}"/quality_control_files/common_scripts/neighbor" ]; then
      echo "ERROR: phylip's neighbor executable was not found. This executable should be in directory
      common_scripts in directory quality_control_files."
      exit 1
    fi

    # Make a distance matrix of the merged file
    echo -e "Using plink to make a distance matrix of the merged file"
    "${tool_directory}"/quality_control_files/common_scripts/plink  \
      --allow-no-sex  \
      --bfile ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_merge"  \
      --distance square 1-ibs  \
      --chr-set 38  \
      --out ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance"  \
      --silent
    cat ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance.log" >> "$log_file"

    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}_"breed_merge*

    echo -e "\nUsing python script ReformatDist.py to reformat the distance matrix to phylip format"
    python3 "${tool_directory}"/quality_control_files/common_scripts/ReformatDist.py  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_breed_distance"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_matrix.txt"  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_ids.txt"

    rm "${tool_directory}"/quality_control_files/temp_files/"${file_new}_"breed_distance*


    row_outgroup=$(sed -n '/Coyote_347/=' ""${tool_directory}"/quality_control_files/temp_files/${file_new}_ids.txt")
    echo -e "\nUsing the Phylip neighbor executable to make a newick tree"
    echo -e "Used settings are:"
    echo -e "O - Outgroup is used, outgroup on row $row_outgroup"
    echo -e "J - Input order of species is randomized"
    echo -e "2 - Progress of run is not printed \n"

    # input file
    echo ""${tool_directory}"/quality_control_files/temp_files/${file_new}_matrix.txt" > ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"
    echo "O" >> ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"  # Use an outgroup
    echo "$row_outgroup" >> ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"  # row of outgroup sample
    echo "J" >> ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"  # randomize input order of species
    echo "3" >> ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"  # odd random seed number
    echo "2" >> ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"  # do not print indications of progress of run
    echo "Y" >> ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"  # accept settings
    } 2>&1 | tee -a "$log_file" # put output in log file
    # Run the neighbor program with the input from input.txt
    "${tool_directory}"/quality_control_files/common_scripts/neighbor < ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"
    {
    mv outtree  "${file_new}_tree_temp.newick"
    rm outfile

    # reverse the temporary sample_ids to the original ids and make annotation file.
    echo -e "\nUsing python script UpdateSampleIDs.py to update the sample IDs in the newick file"
    python3 "${tool_directory}"/quality_control_files/common_scripts/UpdateSampleIDs.py  \
    ""${tool_directory}"/quality_control_files/temp_files/${file_new}_ids.txt"  \
    "${file_new}_tree_temp.newick"  \
    "${file_new}_tree.newick"  \
    "$file_fam"  \
    "${file_new}_tree_annotation.txt"

    rm "${file_new}_tree_temp.newick"
    rm ""${tool_directory}"/quality_control_files/temp_files/${file_new}_input.txt"
    rm ""${tool_directory}"/quality_control_files/temp_files/${file_new}_ids.txt"
    rm ""${tool_directory}"/quality_control_files/temp_files/${file_new}_matrix.txt"
    } 2>&1 | tee -a "$log_file" # put output in log file
  fi
  echo "The produced annotation file can be loaded into ITOl -> control panel -> datasets,"
  echo "after the newick file is loaded. This colors the new dogs in the tree."

fi

end=$(date +%s)
echo -e "\nExecution time in total: $((end-start)) seconds ($(((end-start)/60)) minutes)" 2>&1 | tee -a "$log_file"
