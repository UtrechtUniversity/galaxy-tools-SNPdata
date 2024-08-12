#!/bin/bash
#To be able to merge genotype files from different platforms, the files must be in a uniform format.
#This genotype processing pipeline (command line tool) creates files which are in the same format,
#ready to be merged.
start1=$(date +%s)
i_option=0
e_option=0
a_option=0
o_option=0
f_option=0
n_option=0
w_option=0
v_option=0
p_option=0
h_option=0
t_option=0
l_option=0

# Extra arguments for Galaxy
x_option=0

# define options and capture input
while getopts ":i:e:a:o:x:z:f:n:w:v:tlhp:" option; do
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
      a_option=1
      ;;
    o)  # flag for the new output file name
      file_new="$OPTARG"
      log_file="${file_new}_Log.txt"
      file_exclude="${file_new}_ExcludedSNPs.list"
      o_option=1
      ;;
    f)  # flag for input files if they have the same name
      file="$OPTARG"
      file_bim="$file.bim"
      file_bed="$file.bed"
      file_fam="$file.fam"
      f_option=1
      ;;
    n)  # flag for input file for neogen
      file_neogen="$OPTARG"
      n_option=1
      ;;
    w)  # flag for input file for wisdom
      file_wisdom="$OPTARG"
      w_option=1
      ;;
    v)  # flag for vcf (wgs) input
      file_vcf="$OPTARG"
      v_option=1
      ;;
    p)  # flag for defining platform
      platform="$OPTARG"
      p_option=1
      ;;
    t)  # flag for tbi vcf file present
      t_option=1;;
    l) # flag for filtered locations file of vcf present
      l_option=1;;
    h)  #flag for help
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
  echo "Use bash convert.sh -h for help"
  exit 1
fi

shift "$(( OPTIND -1 ))"

# output for help option -h
if [ $h_option -eq 1 ]; then
  echo "USAGE: convert.sh [-i|e|a|o|f|n|w|v|p|h|t]"
  echo -e "\nCommand line tool to convert input files to a uniform format"
  echo -e "Author: Marilijn van Rumpt - marilijn@live.nl (2024)"
  echo -e "\nSYNTAX OPTIONS:"
  echo -e "\t-i <filename.bim> \tSpecify full name of .bim file"
  echo -e "\t-e <filename.bed> \tSpecify full name of .bed file"
  echo -e "\t-a <filename.fam> \tSpecify full name of .fam file"
  echo -e "\t-o <prefix_filename> \tSpecify prefix for output files. Obligatory"
  echo -e "\t-f <prefix_filename> \tSpecify prefix for .bed + .fam +. bim file"
  echo -e "\t-n <filename> \t\tSpecify full name of final report file of Neogen 220K or 170K"
  echo -e "\t-w <filename> \t\tSpecify full name of Wisdom file (xlsx)"
  echo -e "\t-v <filename> \t\tSpecify full name of VCF.gz canfam 3 or 4 file (WGS)"
  echo -e "\t-t \t\t\tTo indicate a .tbi file of the VCF file is already present, and skip the step of indexing the raw vcf"
  echo -e "\t-l \t\t\tTo indicate a file with filtered locations from raw vcf file is present, and skip step of filtering locations"
  echo -e "\t-p <platform> \t\tSpecify platform, options: embark, neogen170, neogen220, lupa170, mdd, wisdom, vcf3, vcf4, affymetrix. Obligatory"
  echo -e "\t-h \t\t\tPrint the help overview \n"
  echo -e "\nEXAMPLES:"
  echo -e "\tbash convert.sh -f inputfile -p embark -o newfilename"
  echo -e "\tbash convert.sh -a inputfile.fam -i inputfile.bim -e inputfile.bed -p mdd -o newfilename"
  echo -e "\tbash convert.sh -n inputfile -p neogen220 -o newfilename"
  echo -e "\tbash convert.sh -v inputfile.vcf.gz -t -p vcf3 -o newfilename"
  echo -e "\tbash convert.sh -v inputfile_filtered_locations.vcf -l -p vcf3 -o newfilename\n"
  echo -e "\nDEPENDENCIES NEEDED:"
  echo -e "\tpython3, with packages pandas and openpyxl (only needed for converting wisdom files)"
  echo -e "\tperl"
  echo -e "\tplink 1.9 (included in this tool)"
  echo -e "\nSYNTAX OPTIONS PER PLATFORM:"
  echo "-p embark:"
  echo -e "\tFor specifying input files, use either -i,-e-,a together, or only -f."
  echo -e "\tOptions -n, -w, -v, -t cannot be used"
  echo -e "\tFor platform use -p embark"
  echo "-p neogen220:"
  echo -e "\tFor specifying input files, use -n"
  echo -e "\tOptions -i,-e-,a,-f, -w, -v, -t, -l cannot be used"
  echo -e "\tFor platform use -p neogen220"
  echo "-p neogen170:"
  echo -e "\tFor specifying input files, use -n"
  echo -e "\tOptions -i,-e-,a,-f, -w, -v, -t, -l cannot be used"
  echo -e "\tFor platform use -p neogen170"
  echo "-p wisdom:"
  echo -e "\tFor specifying input files, use -w"
  echo -e "\tOptions -i,-e-,a,-f, -n, -v, -t, -l cannot be used"
  echo -e "\tFor platform use -p wisdom"
  echo "-p mdd:"
  echo -e "\tFor specifying input files, use either -i,-e-,a together, or only -f."
  echo -e "\tOptions -n, -w, -v, -t, -l cannot be used"
  echo -e "\tFor platform use -p mdd"
  echo "-p lupa170:"
  echo -e "\tFor specifying input files, use either -i,-e-,a together, or only -f."
  echo -e "\tOptions -n, -w, -v, -t, -l cannot be used"
  echo -e "\tFor platform use -p lupa170"
  echo "-p vcf3:"
  echo -e "\tFor specifying input files, use -v"
  echo -e "\tUse -t to indicate .tbi (indexed vcf) file is already present. Use in combination with -v."
  echo -e "\tUse -l to indicate .vcf file with filtered locations from the raw vcf file is already present. Specify file with -v."
  echo -e "\tOptions -i,-e-,a,-f, -n, -w cannot be used"
  echo -e "\tFor platform use -p vcf3"
  echo "-p vcf4:"
  echo -e "\tFor specifying input files, use -v"
  echo -e "\tUse -t to indicate .tbi (indexed vcf) file is already present. Use in combination with -v."
  echo -e "\tUse -l to indicate .vcf file with filtered locations from the raw vcf file is already present. Specify file with -v."
  echo -e "\tOptions -i,-e-,a,-f, -n, -w cannot be used"
  echo -e "\tFor platform use -p vcf4"
  echo "-p affymetrix:"
  echo -e "\tFor specifying input files, use either -i,-e-,a together, or only -f."
  echo -e "\tOptions -n, -w, -v, -t, -l cannot be used"
  echo -e "\tFor platform use -p affymetrix"
  exit 1
fi

# Error if no output name was given
if [ $o_option -ne 1 ]; then
  echo "ERROR: no output file name was given."
  exit 1
fi

# Error if no platform was given
if [ $p_option -ne 1 ]; then
  echo "ERROR: no platform was given, choose from embark, neogen170, neogen220, lupa170, mdd, wisdom, vcf3, vcf4, affymetrix."
  exit 1
fi

# Check if given platform is a valid option
platform_options=(embark neogen170 neogen220 mdd wisdom lupa170 vcf3 vcf4 affymetrix)
if ! printf '%s\0' "${platform_options[@]}" | grep -Fzxq -- "$platform"; then
  echo "ERROR: wrong platform was given, choose from embark, neogen170, neogen220, lupa170, mdd, wisdom, vcf3, vcf4, affymetrix."
  exit 1
fi

# Error if chosen new file name already exists
if [ -f "$file_new.bim" ] || [ -f "$file_new.bed" ] || [ -f "$file_new.fam" ]  \
|| [ -f "${file_new}_Log.txt" ] || [ -f "$file_exclude" ]; then
  echo "ERROR: filename $file_new or $file_exclude already exists, change -o output name"
  exit 1
fi

# create directory for temporary files, if directory not already exists
mkdir -p "${tool_directory}"/convert_files/temp_files


# check if temporary output file names already exist
if [[ -n $(shopt -s nullglob; echo "${tool_directory}"/convert_files/temp_files/"${file_new}"_temp*) ]]; then
  echo "ERROR: filename ${file_new}_temp(12) for the temporary output file in the temp_files folder
  already exists, remove or change location of this file." 2>&1 | tee -a "$log_file"
  exit 1
fi

# check if plink file is present
if ! [ -f ""${tool_directory}"/convert_files/common_scripts/plink" ]; then
  echo "ERROR: plink was not found. This executable should be in directory "${tool_directory}"/convert_files/common_scripts."
  exit 1
fi

# Check if python3 is installed
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 is not installed" >&2; exit 1;}

{
# Printing the the chosen options in the log of the bash script
echo -e "Log of bash script convert.sh on $(date)"
echo -e "Author: Marilijn van Rumpt - marilijn@live.nl (2024)\n\nThe following options were used: \n"
if [ $p_option -eq 1 ]; then echo -e "-p $platform"; fi
if [ $i_option -eq 1 ]; then echo -e "-i $file_bim"; fi
if [ $e_option -eq 1 ]; then echo -e "-e $file_bed"; fi
if [ $a_option -eq 1 ]; then echo -e "-a $file_fam"; fi
if [ $f_option -eq 1 ]; then echo -e "-f $file"; fi
if [ $n_option -eq 1 ]; then echo -e "-n $file_neogen"; fi
if [ $w_option -eq 1 ]; then echo -e "-w $file_wisdom"; fi
if [ $v_option -eq 1 ]; then echo -e "-v $file_vcf"; fi
if [ $t_option -eq 1 ]; then echo -e "-t"; fi
if [ $l_option -eq 1 ]; then echo -e "-l"; fi
if [ $o_option -eq 1 ]; then echo -e "-o $file_new"; fi

# Printing data summary: number of samples and number of snps
if [ -f "$file_fam" ]; then
  number_samples=$(wc -l < "$file_fam")
  echo -e "\nNumber of samples: $number_samples"
fi
if [ -f "$file_bim" ]; then
  number_snps=$(wc -l < "$file_bim")
  echo -e "Number of SNPs: $number_snps"
fi

} 2>&1 | tee -a "$log_file" # put output in log file

# to convert embark files
if [ "$platform" = 'embark' ]; then
  # Error if neither separate bed bim fam files were given or the -f option was used
  if [[ ($((i_option + e_option + a_option)) -ne 3 && $f_option -ne 1)  \
  || ($((i_option + e_option + a_option)) -ne 0 && $f_option -eq 1) ]]; then
    echo "ERROR: for embark files, use either options i,e,a together or only f." 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Error if wrong input flags are used
  if [ $n_option -eq 1 ] || [ $w_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ]; then
    echo "ERROR: the -n, -w, -v, -t, -l options cannot be used for platform embark" 2>&1 | tee -a "$log_file"
    exit 1
  fi
  {
  # execute python script
  echo -e "\nUsing python script EMBARKConvertBIM.py to create a .bim file in the uniform format: "
  python3 "${tool_directory}"/convert_files/embark/EMBARKConvertBIM.py "$file_bim" ""${tool_directory}"/${file_exclude}" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim" "$tool_directory"

  # execute plink command
  echo -e "\nUsing plink to exclude SNPs: "
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --bim ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim"  \
  --fam "$file_fam"  \
  --bed "$file_bed"  \
  --make-bed  \
  --exclude ""${tool_directory}"/${file_exclude}"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  rm "$file_new.log"
fi

# to convert neogen 220k files
if [ "$platform" = 'neogen220' ]; then
  # Error if either -n was not used or another option was used
  if [ $n_option -ne 1 ] || [ $a_option -eq 1 ] || [ $e_option -eq 1 ] || [ $i_option -eq 1 ]  \
  || [ $f_option -eq 1 ] || [ $w_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ]; then
    echo "ERROR: to convert neogen 220K files, only use -n for input file. Do not use options -a, -i, -e, -f, -w, -v, -t, -l" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  {
  # execute python script
  echo -e "\nUsing python script NEOGEN220Kconvert.py: to create .map and .ped files in the uniform format:"
  python3 "${tool_directory}"/convert_files/neogen220/NEOGEN220KConvert.py "$file_neogen" ""${tool_directory}"/${file_exclude}" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp" "$tool_directory"

  # execute plink command
  echo -e "\nUsing plink to exclude SNPs: "
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --map ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.map"  \
  --ped ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.ped"  \
  --make-bed --exclude ""${tool_directory}"/${file_exclude}"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  rm "$file_new.log"

fi

# to convert neogen 170k files
if [ "$platform" = 'neogen170' ]; then

  # Error if either -n was not used or another option was used
  if [ $n_option -ne 1 ] || [ $a_option -eq 1 ] || [ $e_option -eq 1 ] || [ $i_option -eq 1 ]  \
  || [ $f_option -eq 1 ] || [ $w_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ]; then
    echo "ERROR: to convert neogen 170K files, only use -n for input file. Do not use options -a, -i, -e, -f, -w, -v, -t, -l" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  {
  # execute python script
  echo -e "\nUsing python script NEOGEN170Kconvert.py to create .map and .ped file in the uniform format: "
  python3 "${tool_directory}"/convert_files/neogen170/NEOGEN170Kconvert.py "$file_neogen" "$file_exclude" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp"

  # execute plink command
  echo -e "\nUsing plink to exclude SNPs: "
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --map ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.map"  \
  --ped ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.ped"  \
  --make-bed --exclude "$file_exclude"  \
  --chr-set 38  \
  --out "$file_new"
  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  rm "$file_new.log"
fi

# to convert wisdom files
if [ "$platform" = 'wisdom' ]; then

  # Error if either -n was not used or another option was used
  if [ $w_option -ne 1 ] || [ $a_option -eq 1 ] || [ $e_option -eq 1 ]  || [ $i_option -eq 1 ]  \
  || [ $f_option -eq 1 ] || [ $n_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ]; then
    echo "ERROR: to convert wisdom files, only use -w for input file. Do not use options -a, -i, -e, -f, -n, -v, -t, -l" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Check if pandas python package is installed
  python3 -c "import pkgutil; exit(0 if pkgutil.find_loader('pandas') else 1)"
  if [ $? -eq 1 ]; then
    echo "ERROR: required package 'pandas' is not installed" 2>&1 | tee -a "$log_file"
    echo "Use 'sudo pip3 install pandas' in terminal" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Check if openpyxl python package is installed
  python3 -c "import pkgutil; exit(0 if pkgutil.find_loader('openpyxl') else 1)"
  if [ $? -eq 1 ]; then
    echo "ERROR: required package 'openpyxl' is not installed" 2>&1 | tee -a "$log_file"
    echo "Use 'sudo pip3 install openpyxl' in terminal" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Check if perl is installed
  command -v perl >/dev/null 2>&1 || { echo "ERROR: Perl is not installed" >&2; exit 1;}
  {
  # execute python script
  echo -e "\nUsing python script WisdomConvert.py to create .map and .ped file in the uniform format: "
  python3 "${tool_directory}"/convert_files/wisdom/WisdomConvert.py "$file_wisdom" ""${tool_directory}"/$file_exclude" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp" "${tool_directory}"

  # execute plink command
  echo -e "\nUsing plink to exclude SNPs: "
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --map ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.map"  \
  --ped ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.ped"  \
  --make-bed  \
  --exclude ""${tool_directory}"/$file_exclude"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"

  {
  rm "$file_new.log"

  # execute perl script for converting to TOP calling
  echo -e "\nUsing perl script convert_bim_allele.pl to convert .bim file to TOP allele calling:"
  perl "${tool_directory}"/convert_files/common_scripts/convert_bim_allele.pl  \
  --intype dbsnp  \
  --outtype top  \
  --outfile ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim"  \
  "$file_new.bim"  \
  "${tool_directory}"/convert_files/common_files/SNP_Table_Big.txt

  rm "$file_new.bim"
  mv ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim" "$file_new.bim"
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

# to convert MyDogDNA (mdd) files
if [ "$platform" = 'mdd' ]; then

  # Error if neither separate bed bim fam files were given or the -f option was used
  if [[ ($((i_option + e_option + a_option)) -ne 3 && $f_option -ne 1)  \
  || ($((i_option + e_option + a_option)) -ne 0 && $f_option -eq 1) ]]; then
    echo "ERROR: for mdd files, use either options i,e,a together or only f." 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Error if wrong flags were used
  if [ $n_option -eq 1 ] || [ $w_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ] ; then
    echo "ERROR: the -n, -w, -v, -t, -l options cannot be used for platform mdd" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Check if perl is installed
  command -v perl >/dev/null 2>&1 || { echo "ERROR: Perl is not installed" >&2; exit 1;}
  {
  # execute python script
  echo -e "\nUsing python script MDDConvert.py to create a .bim and .fam file in the uniform format:"
  python3 "${tool_directory}"/convert_files/mdd/MDDConvert.py "$file_bim" "$file_fam" ""${tool_directory}"/${file_exclude}" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp" "${tool_directory}"

  # execute plink command
  echo -e "\nUsing plink to exclude SNPs: "
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --bim ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim"  \
  --fam ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.fam"  \
  --bed "$file_bed"  \
  --make-bed  \
  --exclude ""${tool_directory}"/${file_exclude}"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  {
  rm "$file_new.log"

  # execute perl script for converting to TOP calling
  echo -e "\nUsing perl script convert_bim_allele.pl to convert .bim file to TOP allele calling:"
  perl "${tool_directory}"/convert_files/common_scripts/convert_bim_allele.pl  \
  --intype ilmn12  \
  --outtype top  \
  --outfile ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim"  \
  "$file_new.bim"  \
  "${tool_directory}"/convert_files/common_files/SNP_Table_Big.txt

  rm "$file_new.bim"
  mv ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim" "$file_new.bim"
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

# to convert Lupa 170K files
if [ "$platform" = 'lupa170' ]; then

  # Error if neither separate bed bim fam files were given or the -f option was used
  if [[ ($((i_option + e_option + a_option)) -ne 3 && $f_option -ne 1)  \
  || ($((i_option + e_option + a_option)) -ne 0 && $f_option -eq 1) ]]; then
    echo "ERROR: for lupa 170K files, use either options i,e,a together or only f." 2>&1 | tee -a "$log_file"
    exit 1
  fi
  # Error if wrong flags were used
  if [ $n_option -eq 1 ] || [ $w_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ]; then
    echo "ERROR: the -n, -w, -v, -t, -l options cannot be used for platform lupa 170K" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Check if perl is installed
  command -v perl >/dev/null 2>&1 || { echo "ERROR: Perl is not installed" >&2; exit 1;}
  {
  # execute python script
  echo -e "\nUsing python script LUPA174Kconvert.py to create a .bim file in the uniform format:"
  python3 "${tool_directory}"/convert_files/lupa170/LUPA174KConvert.py "$file_bim" "${tool_directory}"/"$file_exclude" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp" "$tool_directory"

  # execute plink command
  echo -e "\nUsing plink to exclude SNPs: "
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --bim ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim"  \
  --fam "$file_fam"  \
  --bed "$file_bed"  \
  --make-bed  \
  --exclude "${tool_directory}"/"$file_exclude"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  {
  rm "$file_new.log"

  # execute perl script for converting to TOP calling
  echo -e "\nUsing perl script convert_bim_allele.pl to convert .bim file to TOP allele calling:"
  perl "${tool_directory}"/convert_files/common_scripts/convert_bim_allele.pl  \
  --intype dbsnp  \
  --outtype top  \
  --outfile ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim"  \
  "$file_new.bim"  \
  "${tool_directory}"/convert_files/common_files/SNP_Table_Big.txt

  rm "$file_new.bim"
  mv ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim" "$file_new.bim"
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

if [ "$platform" = 'vcf3' ] || [ "$platform" = 'vcf4' ]; then
  # Error if either -v was not used or another option was used
  if [ $v_option -ne 1 ] || [ $a_option -eq 1 ] || [ $e_option -eq 1 ] || [ $i_option -eq 1 ]  \
  || [ $f_option -eq 1 ] || [ $n_option -eq 1 ] || [ $w_option -eq 1 ]; then
    echo "ERROR: to convert vcf files, only use -v for input file, or -v and -t. Do not use options -a, -i, -e, -f, -n, -w" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Error if only -t and not -v was used
  if [ $v_option -ne 1 ] && [ $t_option -eq 1 ]; then
    echo "ERROR: to convert vcf files, use only -v or both -v and -t, not only -t" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Error if -l, and -v  and -t was used
  if [ $v_option -eq 1 ] && [ $l_option -eq 1 ] && [ $t_option -eq 1 ]; then
    echo "ERROR: to convert vcf files using a pre-made vcf with filtered SNPs, use only -v and -l, not -t" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Error if tbi file already exists and -t option was not used
  if [ $v_option -eq 1 ] && [ $t_option -ne 1 ] && [ -f "${file_vcf}.tbi" ]; then
    echo "ERROR: ${file_vcf}.tbi file already exists, change name/remove/change location of these files or change output name, or use the -t option to skip the indexing and use this tbi file." 2>&1 | tee -a "$log_file"
    rm "$log_file"
    exit 1
  fi

  # Error if the flag -t for an existing .tbi file was used, but file could not be found
  if [ $t_option -eq 1 ] && ! [ -f "${file_vcf}.tbi" ]; then
    echo "ERROR: -t was used but ${file_vcf}.tbi was not found."
    exit 1
  fi

  # Check if perl is installed
  command -v perl >/dev/null 2>&1 || { echo "ERROR: Perl is not installed" >&2; exit 1;}
fi

# to convert vcf canfam 3 files
if [ "$platform" = 'vcf3' ]; then
  if [ $l_option -ne 1 ]; then
    {
    # use tabix to filter vcf file for the correct snps
    echo -e "\nUsing tabix to filter vcf file for the correct snps:"
    if [ $t_option -ne 1 ]; then
      start=$(date +%s)
      echo -e "\tIndexing the VCF file"
      tabix -p vcf "$file_vcf"
      end=$(date +%s)
      echo -e "\tExecution time: $((end-start)) seconds ($(((end-start)/60)) minutes)"
    fi

    echo -e "\tFiltering locations from the vcf file"
    start=$(date +%s)
    tabix -h -R "${tool_directory}"/convert_files/VCF3/VCFFilterFileCF3_big.txt "$file_vcf" > "${file_new}_filtered_locations.vcf"
    end=$(date +%s)
    echo -e "\tExecution time: $((end-start)) seconds ($(((end-start)/60)) minutes)"
    } 2>&1 | tee -a "$log_file" # put output in log file
    file_filtered_locations="${file_new}_filtered_locations.vcf"
  else
    file_filtered_locations="$file_vcf"
  fi

  # use plink to make a BED BIM FAM format from the vcf file
  echo -e "\nUsing plink to make .bed .bim .fam files from vcf file:" 2>&1 | tee -a "$log_file"

  "${tool_directory}"/convert_files/common_scripts/plink  \
  --vcf "$file_filtered_locations"  \
  --make-bed  \
  --chr-set 38  \
  --const-fid 0 \
  --out ""${tool_directory}"/convert_files/temp_files/${file_new}_temp"
  ## --const-fid 0 \ can be added here if there is an error about IDs containing more than 1 _ (underscore)

  cat ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.log" >> "$log_file"
  {
  # execute python script
  echo -e "\nUsing python script VCF3Convert.py to create a .bim file in the uniform format:"
  python3 "${tool_directory}"/convert_files/VCF3/VCF3Convert.py ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2" "${tool_directory}"

  # execute plink command
  echo -e "\nUsing plink to extract SNPs:"
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --bim ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim"  \
  --fam ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.fam"  \
  --bed ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bed"  \
  --make-bed  \
  --extract ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2_extract.list"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  {
  rm "$file_new.log"

  # execute perl script for converting to TOP calling
  echo -e "\nUsing perl script convert_bim_allele.pl to convert .bim file to TOP allele calling:"
  perl "${tool_directory}"/convert_files/common_scripts/convert_bim_allele.pl  \
  --intype dbsnp  \
  --outtype top  \
  --outfile ""${tool_directory}"/convert_files/temp_files/${file_new}_temp3.bim"  \
  "$file_new.bim"  \
  "${tool_directory}"/convert_files/common_files/SNP_Table_Big.txt

  rm "$file_new.bim"
  mv ""${tool_directory}"/convert_files/temp_files/${file_new}_temp3.bim" "$file_new.bim"
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

# to convert vcf canfam 4 files
if [ "$platform" = 'vcf4' ]; then
  if [ $l_option -ne 1 ]; then
    {
    # use tabix to filter vcf file for the correct snps
    echo -e "\nUsing tabix to filter vcf file for the correct snps:"

    if [ $t_option -ne 1 ]; then
      echo -e "\tIndexing the VCF file"
      start=$(date +%s)
      tabix -p vcf "$file_vcf"
      end=$(date +%s)
      echo -e "\tExecution time: $((end-start)) seconds ($(((end-start)/60)) minutes)"
    fi

    start=$(date +%s)
    echo -e "\tFiltering locations from the vcf file"
    tabix -h -R "${tool_directory}"/convert_files/VCF4/VCFFilterFileCF4_big.txt "$file_vcf" > "${file_new}_filtered_locations.vcf"
    end=$(date +%s)
    echo -e "\tExecution time: $((end-start)) seconds ($(((end-start)/60)) minutes)"
    } 2>&1 | tee -a "$log_file" # put output in log file
    file_filtered_locations="${file_new}_filtered_locations.vcf"
  else
    file_filtered_locations="$file_vcf"
  fi
  # use plink to make a BED BIM FAM format from the vcf file
  echo -e "\nUsing plink to make .bed .bim .fam files from vcf file:"

  "${tool_directory}"/convert_files/common_scripts/plink  \
  --vcf "$file_filtered_locations"  \
  --make-bed  \
  --chr-set 38  \
  --out ""${tool_directory}"/convert_files/temp_files/${file_new}_temp"

  cat ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.log" >> "$log_file"
  {
  # execute python script
  echo -e "\nUsing python script VCF4Convert.py to create a .bim file in the uniform format:"
  python3 "${tool_directory}"/convert_files/VCF4/VCF4Convert.py ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2"

  # execute plink command
  echo -e "\nUsing plink to extract SNPs:"
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --bim ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim"  \
  --fam ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.fam"  \
  --bed ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bed"  \
  --make-bed  \
  --extract ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2_extract.list"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  {
  rm "$file_new.log"

  # execute perl script for converting to TOP calling
  echo -e "\nUsing perl script convert_bim_allele.pl to convert .bim file to TOP allele calling:"
  perl "${tool_directory}"/convert_files/common_scripts/convert_bim_allele.pl  \
  --intype dbsnp  \
  --outtype top  \
  --outfile ""${tool_directory}"/convert_files/temp_files/${file_new}_temp3.bim"  \
  "$file_new.bim"  \
  "${tool_directory}"/convert_files/common_files/SNP_Table_Big.txt

  rm "$file_new.bim"
  mv ""${tool_directory}"/convert_files/temp_files/${file_new}_temp3.bim" "$file_new.bim"
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

# to convert affymetrix files
if [ "$platform" = 'affymetrix' ]; then

  # Error if neither separate bed bim fam files were given or the -f option was used
  if [[ ($((i_option + e_option + a_option)) -ne 3 && $f_option -ne 1)  \
  || ($((i_option + e_option + a_option)) -ne 0 && $f_option -eq 1) ]]; then
    echo "ERROR: for affymetrix files, use either options i,e,a together or only f." 2>&1 | tee -a "$log_file"
    exit 1
  fi

  # Error if wrong input flags are used
  if [ $n_option -eq 1 ] || [ $w_option -eq 1 ] || [ $v_option -eq 1 ] || [ $t_option -eq 1 ] || [ $l_option -eq 1 ]; then
    echo "ERROR: the -n, -w, -v, -t, -l options cannot be used for platform affymetrix" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  {
  # execute python script
  echo -e "\nUsing python script AffymetrixConvert.py to create a .bim file in the uniform format:"
  python3 "${tool_directory}"/convert_files/Affymetrix/AffymetrixConvert.py "$file_bim" ""${tool_directory}"/convert_files/temp_files/${file_new}_temp" "${tool_directory}"

  # execute plink command
  echo -e "\nUsing plink to extract SNPs:"
  } 2>&1 | tee -a "$log_file" # put output in log file
  "${tool_directory}"/convert_files/common_scripts/plink  \
  --bim ""${tool_directory}"/convert_files/temp_files/${file_new}_temp.bim"  \
  --fam "$file_fam"  \
  --bed "$file_bed"  \
  --make-bed  \
  --extract ""${tool_directory}"/convert_files/temp_files/${file_new}_temp_extract.list"  \
  --chr-set 38  \
  --out "$file_new"

  # add plink log to log file
  cat "$file_new.log" >> "$log_file"
  {
  rm "$file_new.log"

  # execute perl script for converting to TOP calling
  echo -e "\nUsing perl script convert_bim_allele.pl to convert .bim file to TOP allele calling:"
  perl "${tool_directory}"/convert_files/common_scripts/convert_bim_allele.pl  \
  --intype dbsnp  \
  --outtype top  \
  --outfile ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim"  \
  "$file_new.bim"  \
  "${tool_directory}"/convert_files/common_files/SNP_Table_Big.txt

  rm "$file_new.bim"
  mv ""${tool_directory}"/convert_files/temp_files/${file_new}_temp2.bim" "$file_new.bim"
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

# Remove temporary files and, if present, the .nosex file produced by plink
rm "${tool_directory}"/convert_files/temp_files/"${file_new}"_temp*
if [ -f "${file_new}.nosex" ]; then
  rm "${file_new}".nosex
fi

# Printing data summary: number of samples and number of snps
echo -e "\nOutput files contain:"
if [ -f "$file_new.fam" ]; then
  number_samples=$(wc -l < "$file_new.fam")
  echo -e "Number of samples: $number_samples"
fi
if [ -f "$file_new.bim" ]; then
  number_snps=$(wc -l < "$file_new.bim")
  echo -e "Number of SNPs: $number_snps"
fi


end=$(date +%s)
echo -e "\nExecution time in total: $((end-start1)) seconds ($(((end-start1)/60)) minutes)" 2>&1 | tee -a "$log_file"