// san_probe_r8m2a2.cpp -- P05-S4 R8 M2a2 section 4.5: sanitizer toolchain probe source.  Does not link S4.
// Compiled by san_probe_r8m2a2.sh with -fsanitize=address,undefined.  Without an argument it does not
// write out of bounds; with an argument it writes one element past a 4-int heap block, to test that
// AddressSanitizer reports it.
#include <cstdio>
#include <cstdlib>

int main(int argc, char **argv){
	int *a = (int*)std::malloc(4 * sizeof(int));
	if(!a){ return 2; }
	a[0] = 1;
	if(argc > 1){ a[4] = 2; }
	std::printf("%d\n", a[0]);
	std::free(a);
	return 0;
}
