import compas

try:
	import rhinoscriptsyntax as rs

except ImportError:
	compas.raise_if_ironpython()

from compas.utilities import geometric_key

import compas_rhino as rhino

__author__     = ['Robin Oval']
__copyright__  = 'Copyright 2017, Block Research Group - ETH Zurich'
__license__    = 'MIT License'
__email__      = 'oval@arch.ethz.ch'


__all__ = [
	'clear_layer',
	'is_point_on_curve',
	'surface_borders',
	'surface_border_kinks',
	'curve_discretisation',
	'draw_mesh',
	'draw_graph',
]

def clear_layer(layer):
	"""Delete all the objects in a layer.

	Parameters
	----------
	layer : str
		The layer's name or id.

	Returns
	-------

	"""

	objects = rs.ObjectsByLayer(layer)
	rs.DeleteObjects(objects)

def is_point_on_curve(curve_guid, point_xyz):
	geom_key = geometric_key(point_xyz)
	t = rs.CurveClosestPoint(curve_guid, point_xyz)
	pt_on_crv = rs.EvaluateCurve(curve_guid, t)
	geom_key_pt_on_crv = geometric_key(pt_on_crv)
	if geom_key == geom_key_pt_on_crv:
		return True
	else:
		return False

def surface_borders(surface, border_type = 0):
		border = rs.DuplicateSurfaceBorder(surface, border_type)
		curves = rs.ExplodeCurves(border, delete_input = True)
		return curves

def surface_border_kinks(surface_guid):
	kinks = []
	borders = surface_borders(surface_guid)
	for curve_guid in borders:
		start_tgt = rs.CurveTangent(curve_guid, rs.CurveParameter(curve_guid, 0))
		end_tgt = rs.CurveTangent(curve_guid, rs.CurveParameter(curve_guid, 1))
		if not rs.IsCurveClosed(curve_guid) or not rs.IsVectorParallelTo(start_tgt, end_tgt):
			start = rs.CurveStartPoint(curve_guid)
			end = rs.CurveEndPoint(curve_guid)
			if start not in kinks:
				kinks.append(start)
			if end not in kinks:
				kinks.append(end)
	return kinks

def curve_discretisation(curve_guid, discretisation_spacing):
	points = []
	n = int(rs.CurveLength(curve_guid) / discretisation_spacing) + 1
	curve_guids = rs.ExplodeCurves(curve_guid, delete_input = True)

	if len(curve_guids) == 0:
		points += rs.DivideCurve(curve_guid, n)
		if rs.IsCurveClosed(curve_guid):
			points.append(points[0])
	
	else:
		for guid in curve_guids:
			points += rs.DivideCurve(guid, n)[: -1]
		pts = rs.DivideCurve(curve_guids[-1], n)
		points.append(pts[-1])

	rs.DeleteObjects(curve_guids)
	
	return rs.AddPolyline(points)

def draw_mesh(mesh, layer = None):
	# if quad/tri mesh add mesh, else add edges

	if mesh.number_of_vertices() == 0:
		return None

	for fkey in mesh.faces():
		if len(mesh.face_vertices(fkey)) > 4:
			#return edges
			rs.EnableRedraw(True)
			edges =  [rs.AddLine(mesh.vertex_coordinates(u), mesh.vertex_coordinates(v)) for u, v in mesh.edges() if mesh.vertex_coordinates(u) != mesh.vertex_coordinates(v)]
			rs.EnableRedraw(False)
			group = rs.AddGroup()
			rs.AddObjectsToGroup(edges, group)
			return edges
	# return mesh
	vertices, faces = mesh.to_vertices_and_faces()
	mesh_guid = rhino.utilities.drawing.xdraw_mesh(vertices, faces, None, None)

	if layer is not None:
		rs.ObjectLayer(mesh_guid, layer)

	return mesh_guid

def draw_graph(graph):
	
	vertices = [rs.AddPoint(graph.vertex_coordinates(vkey)) for vkey in graph.vertices()]
	edges = [rs.AddLine(graph.vertex_coordinates(ukey), graph.vertex_coordinates(vkey)) for ukey, vkey in graph.edges()]
	
	return edges, vertices

# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

	import compas
