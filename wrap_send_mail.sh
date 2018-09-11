#!/bin/sh
# vim ft=sh

balancelist=$1
cat $balancelist | xargs -L 1 ./send_mail.sh
