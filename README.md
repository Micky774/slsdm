# Scikit-Learn SIMD DistanceMetrics (SLSDM)

## Install from pip
Run `pip install slsdm`. Note that the premade wheels are only built with support for `SSE2, SSE3, AVX` instructions.

## Install From Source:

1. Create a new environment with `conda create -n <env_name> -c conda-forge python~=3.10.0 compilers`
2. Activate the environment: `conda activate <env_name>`
3. Run `pip install -e .`

**Warning**: At this point, building from source only works with `gcc`. Support for `clang` and `MSVC` is in progress.

## Example
To run this example, you must either [build scikit-learn from source](https://scikit-learn.org/stable/developers/advanced_installation.html#install-bleeding-edge) or use the [nightly build](https://scikit-learn.org/stable/developers/advanced_installation.html#installing-nightly-builds).

```python
from slsdm import get_distance_metric
from sklearn.metrics import DistanceMetric
from sklearn.neighbors import KNeighborsRegressor
from timeit import Timer
import numpy as np

random_state = 0
n_samples_X = 1_000
n_features = 100
n_classes = 3

rng = np.random.RandomState(random_state)
X = rng.uniform(size=(n_samples_X, n_features))
y = rng.randint(n_classes, size=n_samples_X)
metric = 'manhattan'

# We provide a similar API to scikit-learn for grabbing a specific
# DistanceMetric instance, however we do so through a public
# function as opposed to a static method.
dst = get_distance_metric(metric=metric, dtype=X.dtype)
dst_sk = DistanceMetric.get_metric(metric=metric, dtype=X.dtype)

print(Timer('dst.pairwise(X)', globals=globals()).autorange())
print(Timer('dst_sk.pairwise(X)', globals=globals()).autorange())

# Note that you can pass an instance of `DistanceMetric`
# directly to the `metric` keyword
est = KNeighborsRegressor(n_neighbors=20, metric=dst, algorithm="brute").fit(X, y)
est_sk = KNeighborsRegressor(n_neighbors=20, metric=dst_sk, algorithm="brute").fit(X, y)

print(Timer('est.predict(X)', globals=globals()).autorange())
print(Timer('est_sk.predict(X)', globals=globals()).autorange())
```

## Specify SIMD Target Architectures

By default, `slsdm` will be built with `{SSE2, SSE3, AVX}` support. The preferred architectures can be specified at build time using the `SLSDM_SIMD_ARCH` environment variable by passing a comma-separated list of architecture specification tokens. Currently, only `x86_64` CPU features are supported. Specifically, the following features are available:
```
Instruction Set | Specification Tokens
======================================
AVX512BW        |     avx512bw
AVX512DQ        |     avx512dq
AVX512CD        |     avx512cd
AVX512F         |     avx512f
FMA4            |     fma4
FMA3 + AVX2     |     fma3, avx2
AVX2            |     avx2
FMA3 + AVX      |     fma3, avx
AVX             |     avx
FMA3 + SSE4.2   |     fma3, sse4_2
SSE4.2          |     sse4_2
SSE4.1          |     sse4_1
SSSE3           |     ssse3
SSE3            |     sse3
SSE2            |     sse2
```

For example, to build for `{SSE3, AVX, FMA 3 + AVX, AVX2}` one would specify `SLSDM_SIMD_ARCH="sse3, avx, fma3, avx2"`.

You may also prefer to specify features *up to*, and optionally including, a certain instruction. For that, you may prepend a specification token with `<` (exclusive) or `<=` (inclusive). For example, to build for `{SSE2, SSE3, SSSE3, AVX2}` one would specify `SLSDM_SIMD_ARCH="<=ssse3, avx2"`.

You can also disable specific features that would otherwise be enabled by your specification by prepending the `~` symbol to the specification token. For example, to build for `{SSE4_2, SSE4_1, SSE3, SSE2}`, one would specify `SLSDM_SIMD_ARCH="<=sse4_2, !ssse3"`. Note that the specification will be resolved in a left-to-right order, so `SLSDM_SIMD_ARCH="!ssse3, <=sse4_2"` would not produce equivalent results, and indeed still generates `SSSE3` instructions.

To include `FMA3` combination instruction sets, include `fma3` in the `SLSDM_SIMD_ARCH` specification and any compatible instruction sets will automatically be enabled. For example, `SLSDM_SIMD_ARCH="fma3, <=avx"` will enable `{FMA3 + AVX, AVX, FMA3 + SSE4.2, SSE4.2, SSE4.1, SSSE3, SSE3, SSE2}`.
