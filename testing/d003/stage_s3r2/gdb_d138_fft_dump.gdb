set pagination off
set confirm off
break FMMGetEpsilon_FFT
run
set $n = $edx
set $e2 = $rcx
set $inv = $r8
set $n2 = 2*$n
set $bytes_e2 = $n2*$n2*16
set $bytes_inv = $n*$n*16
printf "FFT_ENTER n=%d n2=%d bytes_e2=%d bytes_inv=%d\n", $n, $n2, $bytes_e2, $bytes_inv
break *(FMMGetEpsilon_FFT + RET_OFF)
continue
printf "FFT_RET eax=%d\n", $eax
dump binary memory OUTDIR/ret_E2.bin $e2 ($e2 + $bytes_e2)
dump binary memory OUTDIR/ret_INV.bin $inv ($inv + $bytes_inv)
printf "FFT_DUMP_DONE\n"
quit
