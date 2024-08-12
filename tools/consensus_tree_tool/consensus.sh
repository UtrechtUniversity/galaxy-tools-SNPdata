#!/bin/bash
#
# x = number of iterations chosen
# This script produces x SNP datasets by bootstrapping with
# resampling the SNPs of the samples. Next, x kinship matrixes are made.
# Of each matrix, a phylogenetic tree is made.
# From these x trees, a consensus tree is made.
#
start=$(date +%s)

f_option=0
o_option=0
i_option=0
t_option=0
h_option=0
g_option=0

# Extra arguments for Galaxy
b_option=0
e_option=0
a_option=0
x_option=0

# define options and capture input
while getopts ":b:e:a:f:o:t:i:g:x:h:" option; do
  case $option in
    b)  # input flag for .bim file
      file_bim="$OPTARG"
      b_option=1
      ;;
    e)  # input flag for .bed file
      file_bed="$OPTARG"
      e_option=1
      ;;
    a)  # input flag for .fam file
      file_fam="$OPTARG"
      a_option=1
      ;;
    f)  # flag for input files if they have the same prefix name
      file="$OPTARG"
      file_bim="$file.bim"
      file_bed="$file.bed"
      file_fam="$file.fam"
      f_option=1
      ;;
    o)  # flag for the new output file name
      file_new="$OPTARG"
      log_file="${file_new}_Log.txt"
      o_option=1
      ;;
    t) # flag for which method to use for making tree
      method_tree="$OPTARG"
      t_option=1
      ;;
    i) # flag for the number of iterations
      iter="$OPTARG"
      i_option=1
      ;;
    g) # flag for the outgroup sample
      outgroup="$OPTARG"
      g_option=1
      ;;
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
  echo "Use bash consensus.sh -h for help"
  exit 1
fi

shift "$(( OPTIND -1 ))"

# output for help option -h
if [ $h_option -eq 1 ]; then
  echo "USAGE: consensus.sh [-f|o|t|i|g|h]"
  echo -e "\nCommand line tool to create a consensus tree from bootstrapped datasets"
  echo -e "Author: Marilijn van Rumpt - marilijn@live.nl (2024)"
  echo -e "\nSYNTAX OPTIONS:"
  echo -e "\t-f <prefix_filename> \t\tSpecify prefix for .bed + .fam +. bim file. Obligatory"
  echo -e "\t-o <prefix_filename> \t\tSpecify prefix for output files. Obligatory"
  echo -e "\t-t <method_tree_construction> \tSpecify method of tree construction: phylip or biopython"
  echo -e "\t-i <number_of_iterations> \tSpecify number of iterations"
  echo -e "\t-g <outgroup sample ID> \tSpecify Sample ID of outgroup sample"
  echo -e "\t-h \t\t\t\tPrint the help overview \n"
  echo -e "NOTE: tree construction method phylip is generally faster than biopython"
  echo -e "\nEXAMPLES:"
  echo -e "\tbash consensus.sh -f inputfile -t phylip -i 100 -g Coyote_1 -o newfilename"
  echo -e "\tbash consensus.sh -f inputfile -t biopython -i 50 -g 93754 -o newfilename"
  echo -e "\nDEPENDENCIES NEEDED:"
  echo -e "\tpython3 with package numpy (and biopython if chosen tree construction method is biopython)"
  echo -e "\tplink 1.9 (included in this tool)"
  echo -e "\tPhylip's programs neighbor and consense (included in this tool)"
  exit 1
fi

if [ $o_option -ne 1 ]; then
  echo "ERROR: no output file name was given."
  exit 1
fi

if [ $t_option -ne 1 ]; then
  echo "ERROR: no method for tree construction was given. Use -t phylip or -t biopython."
  exit 1
fi

if [ $i_option -ne 1 ]; then
  echo "ERROR: no number of iterations was given. Use e.g. -i 100"
  exit 1
fi

if [ $g_option -ne 1 ]; then
  echo "ERROR: no sample ID for the outgroup sample was given, use e.g. -g Coyote_4"
  exit 1
fi

if ! [ -f "${file_bim}" ] || ! [ -f "${file_fam}" ] || ! [ -f "${file_bed}" ]; then
  echo "ERROR: one of these files is not present: ${file_bim}, ${file_fam} or ${file_bed}"
  exit 1
fi

if ! grep -Fwq "$outgroup" "$file_fam"; then
  echo "ERROR: given outgroup sample id was not found in .fam file"
  exit 1
fi

# error if wrong method for tree construction was given
tree_construction_options=(phylip biopython)
if ! printf '%s\0' "${tree_construction_options[@]}" | grep -Fzxq -- "$method_tree"; then
  echo "ERROR: wrong method for tree construction was given, options: phylip or biopython"
  exit 1
fi

# Error if chosen new file name already exists
if [ -f "${file_new}_Log.txt" ] || [ -f "${file_new}_consensus_tree.newick" ]; then
  echo "ERROR: filename ${file_new}_Log.txt or ${file_new}_consensus_tree.newick already exists, change -o output name"
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

# check if plink file is present
if ! [ -f ""${tool_directory}"/consensus_files/scripts/plink" ]; then
  echo "ERROR: plink was not found. This executable should be in directory consensus_files."
  exit 1
fi

# Check if python3 is installed
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 is not installed" >&2; exit 1;}

# Check if numpy python package is installed
python3 -c "import pkgutil; exit(0 if pkgutil.find_loader('numpy') else 1)"
if [ $? -eq 1 ]; then
  echo "ERROR: required package 'numpy' is not installed" 2>&1 | tee -a "$log_file"
  echo "Use 'sudo pip3 install numpy' in terminal" 2>&1 | tee -a "$log_file"
  exit 1
fi

rm -r "${tool_directory}"/consensus_files/temp_files # empty temp_files folder
# create directory for temporary files, if directory not already exists
mkdir -p "${tool_directory}"/consensus_files/temp_files
# create directory for bootstrap snp lists, if directory not already exists
mkdir -p "${tool_directory}"/consensus_files/temp_files/bootstrap_datasets
# create directory for matrix files, if directory not already exists
mkdir -p "${tool_directory}"/consensus_files/temp_files/matrix_datasets
# create directory for newick tree files, if directory not already exists
mkdir -p "${tool_directory}"/consensus_files/temp_files/newick_trees

{
# Printing the the chosen options in the log of the bash script
echo -e "Log of bash script consensus.sh on $(date)"
echo -e "Author: Marilijn van Rumpt - marilijn@live.nl (2024)\n\nThe following options were used: \n"
if [ $f_option -eq 1 ]; then echo -e "-f $file"; fi
if [ $t_option -eq 1 ]; then echo -e "-t $method_tree"; fi
if [ $i_option -eq 1 ]; then echo -e "-i $iter"; fi
if [ $g_option -eq 1 ]; then echo -e "-g $outgroup"; fi
if [ $o_option -eq 1 ]; then echo -e "-o $file_new"; fi
if [ $i_option -eq 1 ]; then echo -e "-f $file_bim"; fi
if [ $e_option -eq 1 ]; then echo -e "-f $file_bed"; fi
if [ $a_option -eq 1 ]; then echo -e "-f $file_fam"; fi

# Printing data summary: number of samples and number of snps
number_samples=$(wc -l < "$file_fam")
echo -e "\nNumber of samples: $number_samples"
number_snps=$(wc -l < "$file_bim")
echo -e "Number of SNPs: $number_snps"

echo -e "\nMaking $iter bootstrapped SNP lists"
python3 "${tool_directory}"/consensus_files/scripts/BootstrapSamples.py "$file_bim" "$iter" "$file_new" "$tool_directory"

if [ "$method_tree" = 'biopython' ]; then
  # Check if biopython python package is installed
  python3 -c "import pkgutil; exit(0 if pkgutil.find_loader('Bio') else 1)"
  if [ $? -eq 1 ]; then
    echo "ERROR: required python package 'biopython' is not installed" 2>&1 | tee -a "$log_file"
    echo "Use 'sudo pip3 install biopython' in terminal" 2>&1 | tee -a "$log_file"
    exit 1
  fi

  echo -e "\nMaking $iter kinship matrices of the new SNP datasets"
  # Make a kinship matrix for each dataset
  for i in $(eval echo "{1..$iter}");do
    snp_list=""${tool_directory}"/consensus_files/temp_files/bootstrap_datasets/${file_new}_bootstrap_sample_${i}.list"
    file_out=""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_sample_${i}"
    echo "Distance matrix ${i}"
    "${tool_directory}"/consensus_files/scripts/plink  \
    --fam "$file_fam"  \
    --bim "$file_bim"  \
    --bed "$file_bed"  \
    --extract "$snp_list"  \
    --chr-set 38  \
    --distance triangle 1-ibs  \
    --allow-no-sex  \
    --out "$file_out"  \
    --silent
  done

  rm "${tool_directory}"/consensus_files/temp_files/bootstrap_datasets/"${file_new}"_bootstrap_sample*

  echo -e "\nUsing python script MakeTree.py to create $iter phylogenetic trees"
  for i in $(eval echo "{1..$iter}");do
    echo "Tree ${i}"
    python3 "${tool_directory}"/consensus_files/scripts/MakeTree.py  \
      ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_sample_${i}.mdist"  \
      ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_sample_${i}.mdist.id"  \
      ""${tool_directory}"/consensus_files/temp_files/newick_trees/${file_new}_tree_${i}.newick"  \
      "$outgroup"
  done

  rm "${tool_directory}"/consensus_files/temp_files/matrix_datasets/"${file_new}"_sample*

  echo -e "\nUsing python script MakeConsensusTree.py to create a consensus tree"
  python3 "${tool_directory}"/consensus_files/scripts/MakeConsensusTree.py  \
    "$iter"  \
    ""${tool_directory}"/consensus_files/temp_files/newick_trees/${file_new}_tree_"  \
    "${file_new}_consensus_tree.newick"

  rm "${tool_directory}"/consensus_files/temp_files/newick_trees/"${file_new}"_tree*
fi
} 2>&1 | tee -a "$log_file" # put output in log file

if [ "$method_tree" = 'phylip' ]; then
  {
  # check if phylip executables are present
  if ! [ -f ""${tool_directory}"/consensus_files/scripts/consense" ] || ! [ -f ""${tool_directory}"/consensus_files/scripts/neighbor" ]; then
    echo "ERROR: phylip's consense or neighbor executable was not found. This executable should be in directory scripts in directory consensus_files."
    exit 1
  fi

  echo -e "\nMaking $iter kinship matrices of the new SNP datasets"
  # Make a kinship matrix for each dataset
  for i in $(eval echo "{1..$iter}");do
    snp_list=""${tool_directory}"/consensus_files/temp_files/bootstrap_datasets/${file_new}_bootstrap_sample_${i}.list"
    file_out=""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_sample_${i}"
    echo "Distance matrix ${i}"
    "${tool_directory}"/consensus_files/scripts/plink  \
    --fam "$file_fam"  \
    --bim "$file_bim"  \
    --bed "$file_bed"  \
    --extract "$snp_list"  \
    --chr-set 38  \
    --distance square 1-ibs  \
    --allow-no-sex  \
    --out "$file_out"  \
    --silent
  done

  rm "${tool_directory}"/consensus_files/temp_files/bootstrap_datasets/"${file_new}"_bootstrap_sample*

  echo -e "\nUsing python script ReformatDist.py to reformat the distance matrix to phylip format"
  python3 "${tool_directory}"/consensus_files/scripts/ReformatDist.py  \
    ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_sample"  \
    ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_matrices.txt"  \
    ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_ids.txt"  \
    "$iter"

  rm "${tool_directory}"/consensus_files/temp_files/matrix_datasets/"${file_new}"_sample*

  row_outgroup=$(sed -n "/${outgroup}/=" "$file_fam")
  echo -e "\nUsing the Phylip neighbor executable to make newick trees"
  echo -e "Used settings are:"
  echo -e "O - Outgroup is used, outgroup on row $row_outgroup"
  echo -e "J - Input order of species is randomized"
  echo -e "M - Multiple distance matrices are analyzed, number of datasets is $iter"

  echo ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_matrices.txt" > ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"
  echo "O" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # Use an outgroup
  echo "$row_outgroup" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # row of outgroup sample
  echo "J" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # randomize input order of species
  echo "3" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # odd random seed number
  echo "M" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # analyze multiple datasets
  echo "$iter" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # number of datasets
  echo "3" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # odd random seed number
  #echo "2" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # do not print indications of progress of run
  echo "Y" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"  # accept settings


  } 2>&1 | tee -a "$log_file" # put output in log file
  # Run the neighbor program with the input from input.txt
  "${tool_directory}"/consensus_files/scripts/neighbor < ""${tool_directory}"/consensus_files/temp_files/${file_new}_input.txt"
  {
  mv outtree  "${file_new}_trees.newick"

  echo -e "\nUsing the Phylip consense executable to make a consensus tree"
  echo -e "Used settings are:"
  echo -e "R - Trees are treated as rooted"
  echo -e "3 - Tree does not get printed"
  echo -e "2 - Progress of run is not printed\n"

  echo "${file_new}_trees.newick" > ""${tool_directory}"/consensus_files/temp_files/${file_new}_input2.txt"
  echo "R" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input2.txt"  # Treat trees as rooted
  echo "3" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input2.txt"  #
  echo "2" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input2.txt"  # do not print indications of progress of run
  echo "Y" >> ""${tool_directory}"/consensus_files/temp_files/${file_new}_input2.txt"  # accept settings
  } 2>&1 | tee -a "$log_file" # put output in log file

  "${tool_directory}"/consensus_files/scripts/consense < ""${tool_directory}"/consensus_files/temp_files/${file_new}_input2.txt"
  {
  mv outtree "${file_new}_consensus_tree_temp.newick" 2>&1 | tee -a "$log_file"

  # reverse the temporary sample_ids to the original ids
  echo -e "\nUsing python script UpdateSampleIDs.py to update the sample IDs in the newick file"
  python3 "${tool_directory}"/consensus_files/scripts/UpdateSampleIDs.py  \
    ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_ids.txt"  \
    "${file_new}_consensus_tree_temp.newick"  \
    "${file_new}_consensus_tree.newick"

  rm outfile
  rm "${file_new}_trees.newick"
  rm "${file_new}_consensus_tree_temp.newick"
  rm ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_matrices.txt"
  rm ""${tool_directory}"/consensus_files/temp_files/matrix_datasets/${file_new}_ids.txt"
  rm "${tool_directory}"/consensus_files/temp_files/"${file_new}"_input*
  } 2>&1 | tee -a "$log_file" # put output in log file
fi

end=$(date +%s)
echo -e "\nExecution time in total: $((end-start)) seconds ($(((end-start)/60)) minutes)" 2>&1 | tee -a "$log_file"
