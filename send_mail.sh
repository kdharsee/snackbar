#!/bin/sh
# vim ft=sh

real_balance=`echo "scale=2; ($2 + 100) / 100" | bc`
round_balance=`echo "($2 + 100) / 100" | bc`

if [ $round_balance -eq 0 ]
then
    :
elif [ $round_balance -gt 0 ]
then
	set -x
    echo "Your snack bar balance is \$$real_balance. Thanks for having a positive credit!" | mailx -r "URCS Snack Bar <kdharsee@cs.rochester.edu>" -s "Snack Bar Balance" $1 
	{ set +x; } 2>/dev/null
else
	set -x
    echo "Your snack bar balance is \$$real_balance. Please send the money through Google Pay to urcs.snackbar@gmail.com" | mailx -r "URCS Snack Bar <kdharsee@cs.rochester.edu>" -s "Snack Bar Balance" $1 
	{ set +x; } 2>/dev/null
fi
