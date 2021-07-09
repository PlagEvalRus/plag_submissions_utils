#!/usr/bin/env bash

check_rcode()
{
    local rcode=$1;
    local error_message="$2";

    if [ $rcode -ne 0 ]
    then
        echo " $error_message ";
        exit $rcode;
    fi
}

data_dir=""
generated_dir="generated_corpus"
suffix=""
eversion=()
ids_file=()

while [ $# -gt 0 ] ; do
    case "$1" in
        -i) data_dir="$2"         ; shift 2 ;;
        -o) generated_dir="$2"    ; shift 2 ;;
        -s) suffix="$2"           ; shift 2 ;;
        -V) eversion=("-V" "$2")  ; shift 2 ;;
        -I) ids_file=("-I" "$2")  ; shift 2 ;;
        *) targets="$targets $1"  ; shift 1 ;;
    esac
done

if [ -z "$data_dir" ]; then
    echo "$0 -i <data_dir> [-o <generated_dir>] "
fi

SR_dir="$generated_dir"/source_retrieval/"$suffix"
TA_dir="$generated_dir"/text_alignment/"$suffix"

echo "generate sources map..."
./bin/gen_corpus gen_map -i "$data_dir" "${ids_file[@]}"
check_rcode $? " error: failed to generate sources map!"

echo "generate text alignment and source retrieval tasks..."
./bin/gen_corpus "${eversion[@]}" pan -i "$data_dir" -s "$SR_dir" \
                 -t "$TA_dir" "${ids_file[@]}"
check_rcode $? " error: failed to generate tasks!"

echo "zip suspicious documents..."
zip -jrm "$TA_dir"/susp/susp.zip "$TA_dir"/susp
check_rcode $? " error: failed to zip suspicious documents!"

echo "zip sources..."
zip -jrm "$TA_dir"/src/src.zip "$TA_dir"/src
check_rcode $? " error: failed to zip sources documents!"

echo "copy suspicious documents and sources to source retrieval..."
mkdir -p "$SR_dir"/susp/
cp "$TA_dir"/susp/susp.zip "$SR_dir"/susp/
check_rcode $? " error: failed to copy suspicious documents!"
mkdir -p "$SR_dir"/src/
cp "$TA_dir"/src/src.zip "$SR_dir"/src/
check_rcode $? " error: failed to copy source documents!"


echo "zip metas..."
zip -jrm "$SR_dir"/meta/meta.zip "$SR_dir"/meta
check_rcode $? " error: failed to zip source retrieval metas!"

zip -jrm "$TA_dir"/meta/meta.zip "$TA_dir"/meta
check_rcode $? " error: failed to zip text alignment metas!"
echo "Ready!"
