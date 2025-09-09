const std = @import("std");

pub export fn cosine_similarity(a: [*]const f64, b: [*]const f64, n: std.c_int) callconv(.C) f64 {
    const len: usize = @as(usize, @intCast(n));
    const VecLen = 4; // 256-bit vector for f64
    const Vec = @Vector(VecLen, f64);
    var i: usize = 0;
    var dot_vec: Vec = @splat(0.0);
    var na_vec: Vec = @splat(0.0);
    var nb_vec: Vec = @splat(0.0);
    while (i + VecLen <= len) : (i += VecLen) {
        const va = @ptrCast(*const Vec, a + i).*;
        const vb = @ptrCast(*const Vec, b + i).*;
        dot_vec += va * vb;
        na_vec += va * va;
        nb_vec += vb * vb;
    }
    var dot = @reduce(.Add, dot_vec);
    var na = @reduce(.Add, na_vec);
    var nb = @reduce(.Add, nb_vec);
    while (i < len) : (i += 1) {
        const av = a[i];
        const bv = b[i];
        dot += av * bv;
        na += av * av;
        nb += bv * bv;
    }
    if (na == 0.0 or nb == 0.0) return 0.0;
    return dot / (std.math.sqrt(na) * std.math.sqrt(nb));
}

pub export fn cosine_similarityf(a: [*]const f32, b: [*]const f32, n: std.c_int) callconv(.C) f32 {
    const len: usize = @as(usize, @intCast(n));
    const VecLen = 8; // 256-bit vector for f32
    const Vec = @Vector(VecLen, f32);
    var i: usize = 0;
    var dot_vec: Vec = @splat(0.0);
    var na_vec: Vec = @splat(0.0);
    var nb_vec: Vec = @splat(0.0);
    while (i + VecLen <= len) : (i += VecLen) {
        const va = @ptrCast(*const Vec, a + i).*;
        const vb = @ptrCast(*const Vec, b + i).*;
        dot_vec += va * vb;
        na_vec += va * va;
        nb_vec += vb * vb;
    }
    var dot = @reduce(.Add, dot_vec);
    var na = @reduce(.Add, na_vec);
    var nb = @reduce(.Add, nb_vec);
    while (i < len) : (i += 1) {
        const av = a[i];
        const bv = b[i];
        dot += av * bv;
        na += av * av;
        nb += bv * bv;
    }
    if (na == 0.0 or nb == 0.0) return 0.0;
    return dot / (std.math.sqrt(na) * std.math.sqrt(nb));
}
