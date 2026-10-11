set pagination off
set confirm off
set logging off
break FMMGetEpsilon_PolBasisVL
run pattern both 4 3
set $n = $edx
set $e2 = $rcx
set $inv = $r8
set $n2 = 2*$n
set $bytes = $n2*$n2*16
set $ibytes = $n*$n*16
printf "DUMP_ENTRY n=%d n2=%d bytes_e2=%d bytes_inv=%d\n", $n, $n2, $bytes, $ibytes
dump binary memory OUTDIR/entry_E2.bin $e2 ($e2 + $bytes)
dump binary memory OUTDIR/entry_INV.bin $inv ($inv + $ibytes)
finish
printf "DUMP_RETURN eax=%d\n", $eax
dump binary memory OUTDIR/return_E2.bin $e2 ($e2 + $bytes)
dump binary memory OUTDIR/return_INV.bin $inv ($inv + $ibytes)
quit
