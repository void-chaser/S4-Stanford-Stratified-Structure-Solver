set pagination off
set confirm off
break FMMGetEpsilon_PolBasisVL
run pattern both 4 3
set $n = $edx
set $e2 = $rcx
set $inv = $r8
printf "PB_ENTRY n=%d\n", $n
printf "PB_ENTRY inv_first4\n"
x/8gf $inv
printf "PB_ENTRY E2_blk00_first4\n"
x/8gf $e2
printf "PB_ENTRY E2_blk10_first4\n"
x/8gf $e2 + $n*16
printf "PB_ENTRY E2_blk01_first4\n"
x/8gf $e2 + $n*2*$n*16
printf "PB_ENTRY E2_blk11_first4\n"
x/8gf $e2 + $n*2*$n*16 + $n*16
finish
printf "PB_RETURN eax=%d\n", $eax
printf "PB_RETURN inv_first4\n"
x/8gf $inv
printf "PB_RETURN E2_blk00_first4\n"
x/8gf $e2
printf "PB_RETURN E2_blk10_first4\n"
x/8gf $e2 + $n*16
printf "PB_RETURN E2_blk01_first4\n"
x/8gf $e2 + $n*2*$n*16
printf "PB_RETURN E2_blk11_first4\n"
x/8gf $e2 + $n*2*$n*16 + $n*16
quit
