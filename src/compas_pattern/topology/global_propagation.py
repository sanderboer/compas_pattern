from compas.datastructures.mesh import Mesh

from compas.utilities import geometric_key

from compas.geometry.algorithms.interpolation import discrete_coons_patch

from compas_pattern.datastructures.mesh import insert_vertices_in_halfedge

__author__     = ['Robin Oval']
__copyright__  = 'Copyright 2018, Block Research Group - ETH Zurich'
__license__    = 'MIT License'
__email__      = 'oval@arch.ethz.ch'

__all__ = [
    'face_propagation',
    'mesh_propagation',
]

def face_propagation(mesh, fkey, original_vertices):

    face_vertices = mesh.face_vertices(fkey)

    face_vertex_map = {geometric_key(mesh.vertex_coordinates(vkey)): vkey for vkey in face_vertices}

    if len(original_vertices) != 4:
        return None

    for vkey in original_vertices:
        if vkey not in face_vertices:
            return None

    a, b, c, d = sorted([face_vertices.index(vkey) for vkey in original_vertices])

    ab = face_vertices[a : b + 1 - len(face_vertices)]
    bc = face_vertices[b : c + 1 - len(face_vertices)]
    cd = face_vertices[c : d + 1 ]#- len(face_vertices)]
    da = face_vertices[d :] + face_vertices[: a + 1 - len(face_vertices)]
    #print ab, bc, cd, da

    if len(ab) != len(cd) and len(ab) != 2 and len(cd) != 2:
        return None
    if len(bc) != len(da) and len(bc) != 2 and len(da) != 2:
        return None

    update = {}

    if len(ab) == len(cd):
        m = len(ab)
        ab = [mesh.vertex_coordinates(vkey) for vkey in ab]
        dc = list(reversed([mesh.vertex_coordinates(vkey) for vkey in cd]))
    elif len(ab) == 2:
        m = len(cd)
        a, b = ab
        ab = [mesh.edge_point(a, b, t / (float(m) - 1)) for t in range(m)]
        dc = list(reversed([mesh.vertex_coordinates(vkey) for vkey in cd]))
        update[(a, b)] = ab
    else:
        m = len(ab)
        c, d = cd
        dc = [mesh.edge_point(d, c, t / (float(m) - 1)) for t in range(m)]
        ab = [mesh.vertex_coordinates(vkey) for vkey in ab]
        update[(c, d)] = list(reversed(dc))


    if len(bc) == len(da):
        n = len(bc)
        bc = [mesh.vertex_coordinates(vkey) for vkey in bc]
        ad = list(reversed([mesh.vertex_coordinates(vkey) for vkey in da]))
    elif len(da) == 2:
        n = len(bc)
        d, a = da
        ad = [mesh.edge_point(a, d, t / (float(n) - 1)) for t in range(n)]
        bc = [mesh.vertex_coordinates(vkey) for vkey in bc]
        update[(d, a)] = list(reversed(ad))
    else:
        n = len(da)
        b, c = bc
        bc = [mesh.edge_point(b, c, t / (float(n) - 1)) for t in range(n)]
        ad = list(reversed([mesh.vertex_coordinates(vkey) for vkey in da]))
        update[(b, c)] = bc

    new_vertices, new_face_vertices = discrete_coons_patch(ab, bc, dc, ad)
    
    vertex_remap = []
    for vertex in new_vertices:
        geom_key = geometric_key(vertex)
        if geom_key in face_vertex_map:
            vertex_remap.append(face_vertex_map[geom_key])
        else:
            x, y, z = vertex
            vkey = mesh.add_vertex(attr_dict = {'x': x, 'y': y, 'z': z})
            vertex_remap.append(vkey)

    mesh.delete_face(fkey)

    for face in new_face_vertices:
        mesh.add_face(list(reversed([vertex_remap[vkey] for vkey in face])))
    
    vertex_map = {geometric_key(mesh.vertex_coordinates(vkey)): vkey for vkey in mesh.vertices()}

    for edge, points in update.items():
        u, v = edge
        if u in mesh.halfedge[v] and mesh.halfedge[v][u] is not None:
            vertices = [vertex_map[geometric_key(point)] for point in points]
            insert_vertices_in_halfedge(mesh, v, u, list(reversed(vertices[1 : -1])))

    return mesh

def mesh_propagation(mesh, original_vertices):

    count = mesh.number_of_faces()

    while count > 0:
        count -= 1
        propagated = False
        for fkey in mesh.faces():
            face_vertices = mesh.face_vertices(fkey)
            if len(face_vertices) != 4:
                face_original_vertices = [vkey for vkey in face_vertices if vkey in original_vertices]
                face_propagation(mesh, fkey, face_original_vertices)
                propagated = True
                break
        if propagated:
            continue
        else:
            break

    return mesh

# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    import compas