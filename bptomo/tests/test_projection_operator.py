import numpy as np
from ..build_projection_operator import build_projection_operator

def test_build_projection_operator():
    op = build_projection_operator(4, 2)
    assert np.all(op.sum(axis=1) == 4)
    assert np.all(op.sum(axis=0) == 2)
    # write a test with non perpendicular directions, check that
    # corner pixels don't have as many measures as central pixels
    # user reorder_pixels
