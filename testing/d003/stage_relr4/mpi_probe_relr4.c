/* mpi_probe_relr4.c -- minimal MPI program: prints this process's rank (T3 precheck, task brief 5.4.1). */
#include <stdio.h>
#include <mpi.h>

int main(int argc, char **argv)
{
	int rank, size;
	MPI_Init(&argc, &argv);
	MPI_Comm_rank(MPI_COMM_WORLD, &rank);
	MPI_Comm_size(MPI_COMM_WORLD, &size);
	printf("%d\n", rank);
	fflush(stdout);
	MPI_Finalize();
	return 0;
}
