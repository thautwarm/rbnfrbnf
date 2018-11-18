def iterate(s):
    while s is not ():
        a, s = s
        yield a


def reverse(s):
    r = ()
    while s is not ():
        a, s = s
        r = a, r
    return r
