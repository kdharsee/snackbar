#!/bin/sh
# vim ft=sh

balance=`echo "($2 + 100) / 100" | bc`
contactor=$( cat contactor.txt )
#'Komail(kdharsee@cs.rochester.edu)'

if [ $balance != '0' ]
then
echo "Your snack bar balance is \$-$balance. Please put the money in an envelop with your name on it and throw it in $contactor's mailbox, or on his desk." | mail -s "Snack Bar Balance" $1
fi
