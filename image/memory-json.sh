#!/usr/bin/env bash
# memory and CPU usage and print in json format.
# this assumes `free` gives the old style output with a "-/+ buffers/cache:.." line,
# it won't work with new style "available" `free`.
set -e
free -m > .mem
mem_total=`grep "Mem" .mem | awk '{print $2}'`
mem_used=`grep "buffers/cache" .mem | awk '{print $3}'`
mem_percent=`echo "$mem_total $mem_used" | awk '{print $2/$1*100}'`
cpu_percent=`mpstat | tail -n 1 | awk '{print $3+$4+$5}'`
unknown="\"-\""
printf "{\"info\": \"sys\", "
printf "\"mem_used\": ${mem_used:-$unknown}, "
printf "\"mem_percent\": ${mem_percent:-$unknown}, "
printf "\"cpu_percent\": ${cpu_percent:-$unknown}, "
printf "\"run\": ${1:-$unknown}}\n"
rm .mem
