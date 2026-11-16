"""Adversarial geometry checks for spill detection in a concave bag."""
import unittest
import numpy as np
from scipy.spatial import ConvexHull
from containment import closed_triangles, contains_points
from realistic_meshes_v32 import dirty_mesh

class NonConvexContainmentTests(unittest.TestCase):
    def test_outside_fold_is_rejected_despite_inside_convex_hull(self):
        vertices,faces,mouth=dirty_mesh()
        # Press the +x wall inward while retaining the lip and bottom:
        # a point in that indentation is outside film but inside its hull.
        x,y,z=vertices.T
        dent=np.clip(1-np.abs(y)/.06,0,1)*np.clip(1-np.abs(z-.08)/.06,0,1)
        vertices[:,0]-=.065*dent*(x>0)
        point=np.array([[.060,0,.08]])
        hull=ConvexHull(vertices)
        self.assertTrue(np.all(point@hull.equations[:,:3].T+hull.equations[:,3]<=0))
        self.assertFalse(contains_points(point,closed_triangles(vertices,faces,mouth))[0])
    def test_interior_and_above_mouth(self):
        v,f,m=dirty_mesh();tri=closed_triangles(v,f,m)
        np.testing.assert_array_equal(contains_points([[0,0,.1],[0,0,.27]],tri),[True,False])
    def test_contact_tolerance_has_a_numeric_boundary(self):
        v,f,m=dirty_mesh();tri=closed_triangles(v,f,m)
        np.testing.assert_array_equal(contains_points([[.078,0,.08],[.082,0,.08]],tri),[True,False])
    def test_rigid_transform_invariance(self):
        from scipy.spatial.transform import Rotation
        v,f,m=dirty_mesh();p=np.array([[0,0,.1],[.2,0,.1]])
        r=Rotation.from_euler('xyz',[.3,.6,-.2]);delta=[.4,-.7,.2]
        np.testing.assert_array_equal(contains_points(p,closed_triangles(v,f,m)),contains_points(r.apply(p)+delta,closed_triangles(r.apply(v)+delta,f,m)))

if __name__=='__main__':unittest.main()
