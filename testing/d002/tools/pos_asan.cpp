// Positive control for ASan only.  Its job is to confirm that the ASan
// instrumentation used for this round actually detects a heap buffer overflow
// in THIS toolchain/flag combination.  It says nothing about UBSan.
#include <cstdio>
int main()
{
	int *p = new int[4];
	for (int i = 0; i < 4; ++i) p[i] = i;
	volatile int *q = p;
	int s = 0;
	for (int i = 0; i < 8; ++i) s += q[i];   // 4 elements past the end
	printf("pos_asan sum=%d\n", s);
	delete[] p;
	return 0;
}
