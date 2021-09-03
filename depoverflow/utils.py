def batch(iterable, n):
    r = []
    for item in iterable:
        r.append(item)
        if len(r) == n:
            yield r
            r = []

    if r:
        yield r
