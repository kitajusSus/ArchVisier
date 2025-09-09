/*
 * MIT License
 *
 * Copyright (c) 2025 Archiwizator
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
#include "token_similarity.h"
#include <string.h>
#include <stdlib.h>

static int contains(char** arr, int n, const char* tok) {
    for (int i = 0; i < n; ++i) {
        if (strcmp(arr[i], tok) == 0) {
            return 1;
        }
    }
    return 0;
}

double token_similarity(const char* a, const char* b) {
    char* a_copy = strdup(a ? a : "");
    char* b_copy = strdup(b ? b : "");
    char* tokens_a[256];
    char* tokens_b[256];
    int count_a = 0, count_b = 0;

    char* tok = strtok(a_copy, " \t\n\r");
    while (tok && count_a < 256) {
        tokens_a[count_a++] = tok;
        tok = strtok(NULL, " \t\n\r");
    }

    tok = strtok(b_copy, " \t\n\r");
    while (tok && count_b < 256) {
        tokens_b[count_b++] = tok;
        tok = strtok(NULL, " \t\n\r");
    }

    int intersection = 0;
    for (int i = 0; i < count_a; ++i) {
        if (contains(tokens_b, count_b, tokens_a[i])) {
            intersection++;
        }
    }

    int union_count = count_a;
    for (int i = 0; i < count_b; ++i) {
        if (!contains(tokens_a, count_a, tokens_b[i])) {
            union_count++;
        }
    }

    free(a_copy);
    free(b_copy);

    if (union_count == 0) {
        return 0.0;
    }
    return (double)intersection / (double)union_count;
}
