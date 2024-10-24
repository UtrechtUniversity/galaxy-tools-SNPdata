#!/bin/bash

# Define variables from Galaxy tool inputs
inputbim="$1"
inputbed="$2"
inputfam="$3"
inputplatform="$4"
filename_output="$5"
tool_directory="$6"
sexcheck="$7"
duplicatecheck="$8"
breedcheck="$9"
sex_changed="${10}"
kinship="${11}"
dupsummary="${12}"
newicktree="${13}"
treeannotation="${14}"
treeimg="${15}"
outputbed="${16}"
outputbim="${17}"
outputfam="${18}"

# Base command
cmd="bash $tool_directory/quality_control.sh -i $inputbim -e $inputbed -a $inputfam -p $inputplatform -o $filename_output -x $tool_directory"

# Add options based on conditions
if [ "$sexcheck" == "true" ]; then
    cmd="$cmd -s"
fi

if [ "$duplicatecheck" == "true" ]; then
    cmd="$cmd -d"
fi

if [ "$breedcheck" != "None" ]; then
    cmd="$cmd -b $breedcheck"
fi

# Execute the command
eval $cmd

# Handle file copying based on existence
if [ "$sexcheck" == "true" ] && [ -f "${filename_output}_sex_changed.txt" ]; then
    cp "${filename_output}_sex_changed.txt" "$sex_changed"
fi

if [ "$duplicatecheck" == "true" ]; then
    if [ -f "${filename_output}_kinship.kin0" ]; then
        cp "${filename_output}_kinship.kin0" "$kinship"
    fi
    if [ -f "${filename_output}_duplicate_summary.txt" ]; then
        cp "${filename_output}_duplicate_summary.txt" "$dupsummary"
    fi
fi

if [ "$breedcheck" != "None" ]; then
    if [ -f "${filename_output}_tree.newick" ]; then
        cp "${filename_output}_tree.newick" "$newicktree"
    fi
    if [ -f "${filename_output}_tree_annotation.txt" ]; then
        cp "${filename_output}_tree_annotation.txt" "$treeannotation"
    fi
    if [ -f "${filename_output}_tree.png" ]; then
        cp "${filename_output}_tree.png" "$treeimg"
    fi
fi

# Copy essential files (bed, bim, fam) to outputs
if [ -f "${filename_output}.bed" ]; then
    cp "${filename_output}.bed" "$outputbed"
else
    echo "ERROR: no bed file was found."
    exit 1
fi

if [ -f "${filename_output}.bim" ]; then
    cp "${filename_output}.bim" "$outputbim"
else
    echo "ERROR: no bim file was found."
    exit 1
fi

if [ -f "${filename_output}.fam" ]; then
    cp "${filename_output}.fam" "$outputfam"
else
    echo "ERROR: no fam file was found."
    exit 1
fi
