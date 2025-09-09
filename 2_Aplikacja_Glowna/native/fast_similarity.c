#include <math.h>
#include <stddef.h>
#ifdef USE_BLAS
#include <cblas.h>
#endif

// Simple and fast cosine similarity implementation for vectors
// double and float with optional BLAS support

double cosine_similarity(const double * restrict a, const double * restrict b, int n) {
#ifdef USE_BLAS
    double dot = cblas_ddot(n, a, 1, b, 1);
    double na = cblas_ddot(n, a, 1, a, 1);
    double nb = cblas_ddot(n, b, 1, b, 1);
#else
    double dot = 0.0;
    double na = 0.0;
    double nb = 0.0;
    #pragma omp simd reduction(+:dot,na,nb)
    for (int i = 0; i < n; ++i) {
        dot += a[i] * b[i];
        na += a[i] * a[i];
        nb += b[i] * b[i];
    }
#endif
    if (na == 0.0 || nb == 0.0) {
        return 0.0;
    }
    return dot / (sqrt(na) * sqrt(nb));
}

float cosine_similarityf(const float * restrict a, const float * restrict b, int n) {
    float dot = 0.0f;
    float na = 0.0f;
    float nb = 0.0f;
    #pragma omp simd reduction(+:dot,na,nb)
    for (int i = 0; i < n; ++i) {
        dot += a[i] * b[i];
        na += a[i] * a[i];
        nb += b[i] * b[i];
    }
    if (na == 0.0f || nb == 0.0f) {
        return 0.0f;
    }
    return dot / (sqrtf(na) * sqrtf(nb));
}
