// Positive control for UBSan only.  Deliberate undefined behaviour that
// AddressSanitizer does NOT diagnose: signed integer overflow and an
// out-of-range shift.  Its job is to confirm the UBSan instrumentation used
// for this round is live.  It says nothing about ASan.
#include <cstdio>
int main()
{
	int a = 2147483647;
	volatile int b = a + 1;          // signed integer overflow
	int c = 1;
	volatile int d = c << 31;        // shift exponent too large for 'int'
	printf("pos_ubsan b=%d d=%d\n", b, d);
	return 0;
}
