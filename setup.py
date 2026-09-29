"""Build the S4 CPython extension against the locally built S4 core."""

import sys

from setuptools import Extension, setup


if sys.platform == "darwin":
    libraries = ["c++"]
    extra_link_args = ["-framework", "Accelerate"]
elif sys.platform == "win32":
    libraries = ["openblas", "stdc++", "gfortran", "quadmath"]
    extra_link_args = []
else:
    libraries = ["lapack", "blas", "stdc++"]
    extra_link_args = []


setup(
    name="S4",
    version="1.1.1",
    description="Stanford Stratified Structure Solver Python extension",
    ext_modules=[
        Extension(
            "S4",
            sources=["S4/main_python.c"],
            include_dirs=["S4"],
            extra_objects=["build/libS4.a"],
            libraries=libraries,
            extra_link_args=extra_link_args,
        )
    ],
)
