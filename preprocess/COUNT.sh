#/bin/bash
ys=0
ns=0
js=0
for i in $(seq 0 84); do
    if [[ $i -lt 10 ]]; then
        num="0$i"
    else
        num=$i
    fi
    y=`grep Y: BB/log_${num}.err | wc -l`
    n=`grep N: BB/log_${num}.err | wc -l`
    j=`grep J: BB/log_${num}.err | wc -l`
    sum=$(( $y+$n+$j ))
    ys=$(( $ys+y ))
    ns=$(( $ns+n ))
    js=$(( $js+j ))
    echo $i $y $n $j $sum
done
echo $ys $ns $js
