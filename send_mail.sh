#!/bin/sh
# vim ft=sh

balance=`echo "($2 + 100) / 100" | bc`
contactor=$( cat contactor.txt )
#'Komail(kdharsee@cs.rochester.edu)'

if [ $balance -eq 0 ]
then
    :
elif [ $balance -gt 0 ]
then
    echo "Your snack bar balance is $balance. Thanks for having a positive credit!" | mail -s "Snack Bar Balance" $1
else
    echo "Your snack bar balance is $balance. Please send the money through Google Pay to urcs.snackbar@gmail.com" | mail -s "Snack Bar Balance" $1
fi
