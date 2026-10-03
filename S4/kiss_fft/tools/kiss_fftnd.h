#ifndef KISS_FFTND_H
#define KISS_FFTND_H

#include "kiss_fft.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct kiss_fftnd_state * kiss_fftnd_cfg;
    
kiss_fftnd_cfg  kiss_fftnd_alloc(const int *dims,int ndims,int inverse_fft,void*mem,size_t*lenmem);
void kiss_fftnd(kiss_fftnd_cfg  cfg,const kiss_fft_cpx *fin,kiss_fft_cpx *fout);
/* Checked variant: 0 on success, non-zero if an execution-time temporary buffer
 * could not be allocated (the output must then not be used). */
int kiss_fftnd_checked(kiss_fftnd_cfg  cfg,const kiss_fft_cpx *fin,kiss_fft_cpx *fout);

#ifdef __cplusplus
}
#endif
#endif
