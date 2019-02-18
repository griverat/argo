#!/bin/bash 

files='*.eps'
for line in ${files}
do
file=`echo $line |awk -F. '{print $1}'`
convert -rotate 90 -density 400 $line ${file}.png
#convert -rotate 90 -density 400 $line ${file}.gif
done
