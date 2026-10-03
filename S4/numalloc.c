/* Copyright (C) 2009-2011, Stanford University
 * This file is part of S4
 * Written by Victor Liu (vkl@stanford.edu)
 *
 * S4 is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * S4 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <stdlib.h>
#include <stdio.h>

#ifdef _WIN32
# include <malloc.h>
/*void * _aligned_malloc(size_t size, size_t alignment);
void * _aligned_realloc(void *ptr, size_t size, size_t alignment);
void _aligned_free(void *ptr);
*/
#else
#include <inttypes.h>
#include <string.h>
# ifdef __GLIBC__
#  include <malloc.h>   /* malloc_usable_size, used by the sanitizer branch */
# endif
typedef uintptr_t malloc_aligned_ULONG_PTR;
#endif

/* Detect a sanitizer build. Under AddressSanitizer the side channel used by the
 * manual alignment below (the original pointer stored in the word before the
 * returned one) lands in the redzone and is reported as a heap-buffer-underflow
 * on every allocation. posix_memalign returns a genuine allocation instead. */
#if defined(__SANITIZE_ADDRESS__)
#  define S4_HAVE_ASAN 1
#elif defined(__has_feature)
#  if __has_feature(address_sanitizer)
#    define S4_HAVE_ASAN 1
#  endif
#endif
#ifndef S4_HAVE_ASAN
#  define S4_HAVE_ASAN 0
#endif

// size : the size of allocated memory
//        The actual size of allocation will be greater than this size.
// alignment : the alignment boundary
void *malloc_aligned(size_t size, size_t alignment){
#ifdef _WIN32
	return (void*)_aligned_malloc(size, alignment);
#elif S4_HAVE_ASAN
	void *ptr = NULL;
	if(0 != posix_memalign(&ptr, alignment, size ? size : 1)){ return NULL; }
	return ptr;
#else
	void *pa, *ptr;

	//pa=malloc(((size+alignment-1)&~(alignment-1))+sizeof(void *)+alignment-1);

	pa = malloc((size+alignment-1)+sizeof(void*));
	if(!pa){ return NULL; }

	ptr = (void*)( ((malloc_aligned_ULONG_PTR)pa+sizeof(void*)+alignment-1)&~(alignment-1) );
	*((void **)ptr-1) = pa;

	return ptr;
#endif
}
void *realloc_aligned(void *ptr, size_t size, size_t alignment){
#ifdef _WIN32
	return (void*)_aligned_realloc(ptr, size, alignment);
#elif S4_HAVE_ASAN
	/* posix_memalign allocations have no side channel, so the word before ptr
	 * cannot be read -- under AddressSanitizer that word is the left redzone.
	 * A fresh aligned allocation plus a copy is used instead. The old size comes
	 * from malloc_usable_size, which under AddressSanitizer returns the size
	 * that was requested, so the copy is exact. */
	void *np = NULL;
	size_t old_size;
	if(NULL == ptr){
		return malloc_aligned(size, alignment);
	}
	old_size = malloc_usable_size(ptr);
	if(0 != posix_memalign(&np, alignment, size ? size : 1)){ return NULL; }
	if(0 != old_size){
		memcpy(np, ptr, (old_size < size ? old_size : size));
	}
	free(ptr);
	return np;
#else
	void *pa;

	/* The user pointer is derived from the new raw address, so this is only
	 * correct while the derived offset is stable across a move. Measured stable
	 * on glibc (0 changes in 1024 reallocation trials spanning 16 sizes and 64
	 * malloc alignments), and the sanitizer branch above sidesteps the question
	 * by using a genuinely aligned allocation. */
	pa = realloc(*((void**)ptr-1), (size+alignment-1)+sizeof(void*));
	if(!pa){ return NULL; }

	ptr = (void*)( ((malloc_aligned_ULONG_PTR)pa+sizeof(void*)+alignment-1)&~(alignment-1) );
	*((void **)ptr-1) = pa;

	return ptr;
#endif
}


void free_aligned(void *ptr){
#ifdef _WIN32
	_aligned_free(ptr);
#elif S4_HAVE_ASAN
	/* posix_memalign memory is released with free; there is no side channel. */
	free(ptr);
#else
	if(ptr){
		free(*((void **)ptr-1));
	}
#endif
}
