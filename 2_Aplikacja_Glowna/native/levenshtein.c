#include <stdlib.h>
#include <string.h>

// Compute Levenshtein distance between two strings.
// Returns -1 on allocation failure.
int levenshtein_distance(const char *a, const char *b) {
    size_t len_a = strlen(a);
    size_t len_b = strlen(b);
    int *prev = (int *)malloc((len_b + 1) * sizeof(int));
    int *curr = (int *)malloc((len_b + 1) * sizeof(int));
    if (!prev || !curr) {
        free(prev);
        free(curr);
        return -1;
    }

    #pragma omp parallel for
    for (size_t j = 0; j <= len_b; ++j) {
        prev[j] = (int)j;
    }

    for (size_t i = 1; i <= len_a; ++i) {
        curr[0] = (int)i;
        for (size_t j = 1; j <= len_b; ++j) {
            int cost = (a[i - 1] == b[j - 1]) ? 0 : 1;
            int deletion = prev[j] + 1;
            int insertion = curr[j - 1] + 1;
            int substitution = prev[j - 1] + cost;
            int min = deletion < insertion ? deletion : insertion;
            curr[j] = min < substitution ? min : substitution;
        }
        int *tmp = prev;
        prev = curr;
        curr = tmp;
    }
    int result = prev[len_b];
    free(prev);
    free(curr);
    return result;
}
