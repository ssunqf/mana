pybin=$(find $PWD -name python)
pyscr=$(find $PWD -name mana.py)
cpus=$(cat /proc/cpuinfo | grep processor | awk -F': ' {'print $2}')
cpu_ct=$(cat /proc/cpuinfo | grep processor | wc -l)
for port in $(seq 6881 $(echo $cpu_ct+6880|bc));
	do while [ True ];
		do $pybin $pyscr $port
	done&
done
cat
