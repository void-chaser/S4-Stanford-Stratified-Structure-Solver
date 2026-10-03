/* Copyright (C) 2009-2011, Stanford University
 * This file is part of S4
 * Written by Victor Liu (vkl@stanford.edu)
 *
 * S4 is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

#include "Interpolator.h"
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <stdio.h>
#include <string.h>

struct Interpolator_{
	double *xy;
	int ny;
	int n;
	Interpolator_type type;
	double *result;
	double *m; // Precomputed slopes for cubic spline
};

Interpolator Interpolator_New(int n, int ny, double *xy, Interpolator_type type){
	Interpolator I = (Interpolator)malloc(sizeof(struct Interpolator_));
	if (!I) return NULL;
	if (n < 2 || ny < 1) { free(I); return NULL; }
	I->n = n;
	I->ny = ny;
	size_t extra = 0;
	if (type == Interpolator_CUBIC_SPLINE) {
		extra = (size_t)n * (size_t)ny;
	}
	size_t total_elements = (size_t)ny + (1 + (size_t)ny) * (size_t)n + (size_t)extra;
	if (total_elements > (size_t)-1 / sizeof(double)) { free(I); return NULL; }
	I->result = (double*)malloc(sizeof(double)*total_elements);
	if (!I->result) { free(I); return NULL; }
	I->xy = I->result + ny;
	memcpy(I->xy, xy, sizeof(double)*(1+ny)*n);
	I->type = type;
	if (type == Interpolator_CUBIC_SPLINE) {
		I->m = I->xy + (1+ny)*n;
		if (n >= 2) {
			const int ld = 1 + ny;
			double *c_prime = (double*)malloc(sizeof(double)*n);
			double *d_prime = (double*)malloc(sizeof(double)*n);
			double *h = (double*)malloc(sizeof(double)*(n-1));
			if (!c_prime || !d_prime || !h) {
				if (c_prime) free(c_prime);
				if (d_prime) free(d_prime);
				if (h) free(h);
				Interpolator_Destroy(I);
				return NULL;
			}
			// Compute h_i
			for(int i = 0; i < n-1; ++i) {
				h[i] = I->xy[(i+1)*ld] - I->xy[i*ld];
			}

			// Compute C'_i since they are independent of j
			c_prime[0] = 1.0 / 2.0;
			for(int i = 1; i < n-1; ++i) {
				double a = h[i];
				double b = 2.0 * (h[i-1] + h[i]);
				double c = h[i-1];
				c_prime[i] = c / (b - a * c_prime[i-1]);
			}

			for(int j = 0; j < ny; ++j) {
				// Compute D'_i for this j
				double d0 = 3.0 * (I->xy[1*ld + j + 1] - I->xy[0*ld + j + 1]) / h[0];
				d_prime[0] = d0 / 2.0;
				for(int i = 1; i < n-1; ++i) {
					double a = h[i];
					double b = 2.0 * (h[i-1] + h[i]);
					double dy1 = (I->xy[i*ld + j + 1] - I->xy[(i-1)*ld + j + 1]) / h[i-1];
					double dy2 = (I->xy[(i+1)*ld + j + 1] - I->xy[i*ld + j + 1]) / h[i];
					double d = 3.0 * (h[i] * dy1 + h[i-1] * dy2);
					d_prime[i] = (d - a * d_prime[i-1]) / (b - a * c_prime[i-1]);
				}
				double dn = 3.0 * (I->xy[(n-1)*ld + j + 1] - I->xy[(n-2)*ld + j + 1]) / h[n-2];
				double an = 1.0;
				double bn = 2.0;
				d_prime[n-1] = (dn - an * d_prime[n-2]) / (bn - an * c_prime[n-2]);

				// Back substitution
				I->m[(n-1)*ny + j] = d_prime[n-1];
				for(int i = n-2; i >= 0; --i) {
					I->m[i*ny + j] = d_prime[i] - c_prime[i] * I->m[(i+1)*ny + j];
				}
			}
			free(h);
			free(c_prime);
			free(d_prime);
		}
	} else {
		I->m = NULL;
	}
	return I;
}

void Interpolator_Destroy(Interpolator I){
	if(NULL == I){ return; }
	if(NULL != I->result){ free(I->result); }
	free(I);
}

double* Interpolator_Get(const Interpolator I, double x, int *ny){
	if(NULL == I){ return NULL; }
	if(I->n < 1){ return NULL; }
	const int ld = 1+I->ny;
	int i, j;

	*ny = I->ny;

	// Handle extrapolation explicitly: we will just evaluate the spline/line at the ends.
	// We'll find the segment. If x < x_0, we use segment 0. If x > x_{n-1}, we use segment n-2.
	// For n=1, we can't interpolate, but we require n >= 2 from bindings.
	if(I->n < 2){
		for(j = 0; j < I->ny; ++j) I->result[j] = I->xy[1+j];
		return I->result;
	}

	if (isnan(x) || isinf(x)) return NULL;
	int idx = -1;
	if (x <= I->xy[0]) {
		idx = 0;
	} else if (x >= I->xy[(I->n - 1) * ld]) {
		idx = I->n - 2;
	} else {
		for(i = 1; i < I->n; ++i){
			if(x < I->xy[i*ld]){
				idx = i - 1;
				break;
			}
		}
	}

	int im1 = idx;
	i = idx + 1;

	switch(I->type){
	case Interpolator_CUBIC_SPLINE:
		{
			const double h = I->xy[i*ld] - I->xy[im1*ld];
			const double t = (x - I->xy[im1*ld]) / h;
			const double h00 = (2.0*t - 3.0)*t*t + 1.0;
			const double h10 = ((t - 2.0)*t + 1.0) * t;
			const double h01 = (-2.0*t + 3.0)*t*t;
			const double h11 = (t - 1.0)*t*t;
			for(j = 0; j < I->ny; ++j){
				double m0 = I->m[im1*I->ny + j];
				double m1 = I->m[i*I->ny + j];
				I->result[j] = h00 * I->xy[im1*ld+j+1] + h01 * I->xy[i*ld+j+1] + h * (h10*m0 + h11*m1);
			}
			return I->result;
		}
	case Interpolator_CUBIC_HERMITE_SPLINE:
		{
			static const double dpp = 0.5;
			static const double dpm = 0.5;
			static const double dmp = 0.5;
			static const double dmm = 0.5;

			int im2 = (im1 > 0 ? im1-1 : 0);
			int ip1 = (i < I->n-1 ? i+1 : i);

			const double h = I->xy[i*ld] - I->xy[im1*ld];
			const double t = (x - I->xy[im1*ld]) / h;
			const double h00 = (2.0*t - 3.0)*t*t + 1.0;
			const double h10 = ((t - 2.0)*t + 1.0) * t;
			const double h01 = (-2.0*t + 3.0)*t*t;
			const double h11 = (t - 1.0)*t*t;

			// Prevent div by zero at endpoints if they are accessed
			double dx0 = I->xy[im1*ld] - I->xy[im2*ld];
			if (dx0 == 0.0) dx0 = h; // For im1 == 0, fallback to current segment length
			double dx1 = I->xy[i*ld] - I->xy[im1*ld];
			if (dx1 == 0.0) dx1 = h;
			double dx2 = I->xy[ip1*ld] - I->xy[i*ld];
			if (dx2 == 0.0) dx2 = h;

			for(j = 0; j < I->ny; ++j){
				double m0 = dpp*(I->xy[im1*ld+j+1] - I->xy[im2*ld+j+1])/dx0 + dmm*(I->xy[i*ld+j+1] - I->xy[im1*ld+j+1])/dx1;
				double m1 = dpm*(I->xy[i*ld+j+1] - I->xy[im1*ld+j+1])/dx1 + dmp*(I->xy[ip1*ld+j+1] - I->xy[i*ld+j+1])/dx2;

				I->result[j] = h00 * I->xy[im1*ld+j+1] + h01 * I->xy[i*ld+j+1] + h * (h10*m0 + h11*m1);
			}
			return I->result;
		}
	default: // Interpolator_LINEAR
		{
			double h = I->xy[i*ld] - I->xy[im1*ld];
			double t = (x - I->xy[im1*ld]) / h;
			for(j = 0; j < I->ny; ++j){
				I->result[j] = (1.0-t) * I->xy[im1*ld+j+1] + t * I->xy[i*ld+j+1];
			}
			return I->result;
		}
	}
	return NULL;
}
