#!/usr/bin/env bash
set -e
free -m > .mem
mem_used=`grep "Mem" .mem | awk '{print $3}'`
mem_percent=`grep "Mem" .mem | awk '{print $3/$2*100}'`
cpu_percent=`mpstat | tail -n 1 | awk '{print $3+$4+$5}'`
echo "{\"info\": \"sys\", \"mem_used\": $mem_used, \"mem_percent\": $mem_percent, \"cpu_percent\": $cpu_percent, \"run\": $1}"
rm .mem
