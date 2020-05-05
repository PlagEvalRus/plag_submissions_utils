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
    echo "$0 -i <data_dir> [-o <generated_dir>] [-s 3]"
fi

batch="manually-paraphrased${suffix}"
SR_dir="$generated_dir"/source_retrieval
TA_dir="$generated_dir"/text_alignment

echo "generate sources map..."
./bin/gen_corpus gen_map -i "$data_dir" "${ids_file[@]}"
check_rcode $? " error: failed to generate sources map!"

echo "generate suspicious documents..."
./bin/gen_corpus "${eversion[@]}" create_susp -i "$data_dir" -o "$TA_dir"/susp "${ids_file[@]}"
check_rcode $? " error: failed to generate suspicious documents!"

echo "zip suspicious documents..."
zip -r "$TA_dir"/susp.zip "$TA_dir"/susp
check_rcode $? " error: failed to zip suspicious documents!"

echo "copy suspicious documents to text_alignment..."
mkdir -p "$SR_dir"/susp/
cp -r "$TA_dir"/susp "$SR_dir"/susp/"$batch"
check_rcode $? " error: failed to copy suspicious documents!"
zip -r "$SR_dir"/susp/"$batch".zip "$SR_dir"/susp/"$batch"
check_rcode $? " error: failed to zip suspicious documents2!"


echo "generate sources for text alignment..."
./bin/gen_corpus create_src -i "$data_dir" -o "$TA_dir"/src/ -e "${ids_file[@]}"
check_rcode $? " error: failed to generate sources documents!"


echo "zip sources..."
zip -r "$TA_dir"/src.zip "$TA_dir"/src
check_rcode $? " error: failed to zip sources documents!"


echo "generate text alignment and source retrieval tasks..."
./bin/gen_corpus "${eversion[@]}" pan -i "$data_dir" -s "$SR_dir"/tasks/"$batch" \
                 -t "$TA_dir"/tasks/"$batch" "${ids_file[@]}"
check_rcode $? " error: failed to generate tasks!"


echo "zip tasks..."
zip -r "$SR_dir"/tasks/"$batch".zip "$SR_dir"/tasks/"$batch"
check_rcode $? " error: failed to zip source retrieval tasks!"

zip -r "$TA_dir"/tasks/"$batch".zip "$TA_dir"/tasks/"$batch"
check_rcode $? " error: failed to zip text alignment tasks!"


echo "Ready!"
