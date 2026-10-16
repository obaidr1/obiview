"""Window growth in logical pixels, independent of desktop scale factors."""
import math


def growth_target(image_size, zoom, current, viewport, available):
    chrome = tuple(max(0, outer-inner) for outer,inner in zip(current,viewport))
    desired = tuple(max(old, math.ceil(pixels*zoom)+extra+8)
                    for old,pixels,extra in zip(current,image_size,chrome))
    if desired == tuple(current):
        return None
    if any(want >= limit for want,limit in zip(desired,available)):
        return 'maximize'
    return desired
