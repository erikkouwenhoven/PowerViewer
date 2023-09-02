import math


invphi = (math.sqrt(5) - 1) / 2  # 1 / phi
invphi2 = (3 - math.sqrt(5)) / 2  # 1 / phi^2


def gssrec(f, a, b, tol=1e-5, h=None, c=None, d=None, fc=None, fd=None):

    """
    Golden-section search, recursive. From https://en.wikipedia.org/wiki/Golden-section_search.

    Given a function f with a single local minimum in    the interval [a,b], gss returns a subset interval
    [c,d] that contains the minimum with d-c <= tol.
    """
    (a, b) = (min(a, b), max(a, b))
    if h is None:
        h = b - a
    if h <= tol:
        return a, b
    if c is None:
        c = a + invphi2 * h
    if d is None:
        d = a + invphi * h
    if fc is None:
        fc = f(c)
    if fd is None:
        fd = f(d)
    if fc < fd:  # fc > fd to find the maximum
        return gssrec(f, a, d, tol, h * invphi, c=None, fc=None, d=c, fd=fc)
    else:
        return gssrec(f, c, b, tol, h * invphi, c=d, fc=fd, d=None, fd=None)