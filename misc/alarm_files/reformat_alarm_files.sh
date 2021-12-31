#!/bin/bash



for AFN in $@
do
		
	echo "# StateFile	 - Instrument State file. ex: HRC-I.alarm => use when HRC-I is selected " > $AFN.txt
	echo "# MSID	     - FOT MSID " >> $AFN.txt
	echo "# EGSEMSID	 - EGSE MSID " >> $AFN.txt
	echo "# VALIDFLAG	 - Ignore/Use flag for this state: 0=ignore, 1=active " >> $AFN.txt
	echo "# LR         - Lower red limit " >> $AFN.txt
	echo "# LY         - Lower yellow limit " >> $AFN.txt
	echo "# UY         - Upper yellow limit " >> $AFN.txt
	echo "# uR         - Upper red limit " >> $AFN.txt
	echo "# uR         - Upper red limit " >> $AFN.txt
	echo "#" >> $AFN.txt
	echo "StateFile	MSID	EGSEMSID	VALIDFLAG	LR	LY	UY	UR" >> $AFN.txt
	echo "---------	----	--------	---------	--	--	--	--" >> $AFN.txt
	EGSENAMSE=$( cat $AFN | cut -f1 )
	for EGSEID in $EGSENAMSE
	do
		M2M=$( msid2msid $EGSEID | cut -f2)
		LINE=$( grep -w $EGSEID  $AFN )
		echo "$AFN	$M2M	$LINE" >> $AFN.txt
	done
done
	
