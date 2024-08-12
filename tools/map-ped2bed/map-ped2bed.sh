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
  --out $outputfile_galaxy