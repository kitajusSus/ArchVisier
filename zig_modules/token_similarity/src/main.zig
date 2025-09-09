const std = @import("std");

/// Calculates Jaccard similarity between two strings.
/// Takes C-style null terminated UTF-8 strings.
pub export fn token_similarity(a_ptr: [*c]const u8, b_ptr: [*c]const u8) f64 {
    const a = std.mem.span(a_ptr);
    const b = std.mem.span(b_ptr);

    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    var set = std.StringHashMap(void).init(allocator);
    defer set.deinit();

    var it_a = std.mem.tokenizeAny(u8, a, " \t\n");
    while (it_a.next()) |tok| {
        set.put(tok, {}) catch {};
    }

    var intersection: usize = 0;
    var union_count: usize = set.count();

    var it_b = std.mem.tokenizeAny(u8, b, " \t\n");
    while (it_b.next()) |tok| {
        if (set.contains(tok)) {
            intersection += 1;
        } else {
            union_count += 1;
        }
    }

    if (union_count == 0) return 1.0;
    return @as(f64, @floatFromInt(intersection)) / @as(f64, @floatFromInt(union_count));
}
