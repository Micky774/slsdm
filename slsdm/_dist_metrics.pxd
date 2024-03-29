from sklearn.utils._typedefs cimport float64_t, float32_t, int32_t, intp_t

cdef extern from "src/generated/_dist_optim.cpp":
    cdef Type xsimd_manhattan_dist[Type](Type * x, Type * y, intp_t size) nogil
    cdef Type xsimd_euclidean_rdist[Type](Type * x, Type * y, intp_t size) nogil
    cdef Type xsimd_seuclidean_rdist[Type](Type * x, Type * y, intp_t size, const Type * v) nogil
    cdef Type xsimd_chebyshev_dist[Type](Type * x, Type * y, intp_t size) nogil
    cdef Type xsimd_minkowski_rdist[Type](Type * x, Type * y, intp_t size, const double p) nogil
    cdef Type xsimd_minkowski_w_rdist[Type](Type * x, Type * y, intp_t size, const Type * w, const double p) nogil
