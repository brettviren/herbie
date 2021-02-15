#!/bin/bash


SRC_TAG="$1"
TGT_TAG="$2"

set -euo pipefail
# set -x

if [ -n "$SRC_TAG" ] ; then
    herbstclient use "$SRC_TAG" || exit -1
fi
SRC_INDEX=$(herbstclient attr tags.focus.index)
    
if [ -n "$TGT_TAG" ] ; then
    herbstclient use "$TGT_TAG" || exit -1
    TGT_INDEX=$(herbstclient attr tags.focus.index)
else
    TGT_INDEX="0"
fi


ask_first () {
    ind=$1 ;  shift
    herbstclient substitute TAG "tags.${ind}.name" \
                 or , and . compare monitors.focus.tag = TAG . use_previous , use TAG
}

try_first () {
    ind=$1 ; shift
    herbstclient substitute PRE tags.focus.index \
                 chain + use_index "$ind" + or , compare tags.focus.index != PRE , use_previous 
}


time_it () {
    cmd="$1" ; shift
    srcind="$1" ; shift
    tgtind="$1" ; shift

    log="${cmd}.log"
    rm -f "$log"
    herbstclient use_index $srcind
    for n in {1..10}
    do
        (time "$cmd" "$tgtind") 2>&1 | grep real >> "$log"
        sleep 1                 # emulate dwelling on a tag
        herbstclient use_index $srcind
        sleep 1                 # emulate dwelling on a tag
    done
    herbstclient use_index $srcind
    echo $cmd
    cat $log
}

time_it ask_first "$SRC_INDEX" "$TGT_INDEX"
sleep 1
time_it try_first "$SRC_INDEX" "$TGT_INDEX"
