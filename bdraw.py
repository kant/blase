import bpy
import numpy as np
from mathutils import Matrix
from scipy.spatial.transform import Rotation as R
from blase.data import material_styles_dict
from blase.tools import get_cell_vertices
import time
######################################################
#========================================================
def draw_cell(coll_cell, cell_vertices, label = None, celllinewidth = 0.01):
    """
    Draw unit cell
    """
    if cell_vertices is not None:
        # build materials
        material = bpy.data.materials.new('cell_{0}'.format(label))
        # material.label = 'cell'
        material.diffuse_color = (0.8, 0.25, 0.25, 1.0)
        # draw points
        bpy.ops.mesh.primitive_uv_sphere_add(radius = celllinewidth) #, segments=32, ring_count=16)
        sphere = bpy.context.view_layer.objects.active
        sphere.name = 'instancer_cell_%s_sphere'%label
        sphere.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        sphere.hide_set(True)
        mesh = bpy.data.meshes.new('point_cell' )
        obj_cell = bpy.data.objects.new('cell_%s_point'%label, mesh )
        # Associate the vertices
        obj_cell.data.from_pydata(cell_vertices, [], [])
        sphere.parent = obj_cell
        obj_cell.instance_type = 'VERTS'
        coll_cell.objects.link(sphere)
        coll_cell.objects.link(obj_cell)
        #
        # edges
        edges = [[0, 1], [0, 2], [0, 4], 
                 [1, 3], [1, 5], [2, 3], 
                 [2, 6], [3, 7], [4, 5], 
                 [4, 6], [5, 7], [6, 7],
        ]
        cell_edges = {'lengths': [], 
                      'centers': [],
                      'normals': []}
        for e in edges:
            center = (cell_vertices[e[0]] + cell_vertices[e[1]])/2.0
            vec = cell_vertices[e[0]] - cell_vertices[e[1]]
            length = np.linalg.norm(vec)
            nvec = vec/length
            # print(center, nvec, length)
            cell_edges['lengths'].append(length/2.0)
            cell_edges['centers'].append(center)
            cell_edges['normals'].append(nvec)
        #
        source = bond_source(vertices=4)
        verts, faces = cylinder_mesh_from_instance(cell_edges['centers'], cell_edges['normals'], cell_edges['lengths'], celllinewidth, source)
        # print(verts)
        mesh = bpy.data.meshes.new("edge_cell")
        mesh.from_pydata(verts, [], faces)  
        mesh.update()
        for f in mesh.polygons:
            f.use_smooth = True
        obj_edge = bpy.data.objects.new("cell_%s_edge"%label, mesh)
        obj_edge.data = mesh
        obj_edge.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        coll_cell.objects.link(obj_edge)


def draw_text(coll_text = None, atoms = None, type = None):
    tstart = time.time()
    positions = atoms.positions
    n = len(positions)
    for i in range(n):
        location = positions[i] + np.array([0, 0, 1.0])
        FontCurve = bpy.data.curves.new(type="FONT",name="myFontCurve")
        ob = bpy.data.objects.new("myFontOb",FontCurve)
        if type == 0:
            ob.data.body = "%s"%i
        elif type == 1:
            ob.data.body = "%s"%atoms[i].symbol
        ob.location = location
        coll_text.objects.link(ob)
    print('text: {0:10.2f} s'.format(time.time() - tstart))


def draw_bond_kind(kind, 
                   datas, 
                   label = None,
                   coll = None,
                   source = None, 
                   bondlinewidth = 0.10,
                   bsdf_inputs = None, 
                   material_style = 'plastic'):
    if not bsdf_inputs:
        bsdf_inputs = material_styles_dict[material_style]
    vertices = 16
    source = bond_source(vertices = vertices)
    tstart = time.time()
    material = bpy.data.materials.new('bond_kind_{0}'.format(kind))
    material.diffuse_color = np.append(datas['color'], datas['transmit'])
    material.metallic = bsdf_inputs['Metallic']
    material.roughness = bsdf_inputs['Roughness']
    # material.blend_method = 'BLEND'
    material.use_nodes = True
    principled_node = material.node_tree.nodes['Principled BSDF']
    principled_node.inputs['Base Color'].default_value = np.append(datas['color'], datas['transmit'])
    principled_node.inputs['Alpha'].default_value = datas['transmit']
    for key, value in bsdf_inputs.items():
        principled_node.inputs[key].default_value = value
    datas['materials'] = material
    #
    verts, faces = cylinder_mesh_from_instance(datas['centers'], datas['normals'], datas['lengths'], bondlinewidth, source)
    mesh = bpy.data.meshes.new("mesh_kind_{0}".format(kind))
    mesh.from_pydata(verts, [], faces)  
    mesh.update()
    for f in mesh.polygons:
        f.use_smooth = True
    obj_bond = bpy.data.objects.new("bond_{0}_{1}".format(label, kind), mesh)
    obj_bond.data = mesh
    obj_bond.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    coll.objects.link(obj_bond)
    print('bonds: {0}   {1:10.2f} s'.format(kind, time.time() - tstart))
    

def draw_bonds_2(coll_bond_kinds, bond_kinds, bondlinewidth = 0.10, vertices = None, bsdf_inputs = None, material_style = 'plastic'):
    '''
    Draw atom bonds. Using instancing method
    
    '''
    if not bsdf_inputs:
        bsdf_inputs = material_styles_dict[material_style]
    vertices = 16
    for kind, datas in bond_kinds.items():
        tstart = time.time()
        material = bpy.data.materials.new('bond_kind_{0}'.format(kind))
        material.diffuse_color = np.append(datas['color'], datas['transmit'])
        material.use_nodes = True
        principled_node = material.node_tree.nodes['Principled BSDF']
        principled_node.inputs['Base Color'].default_value = np.append(datas['color'], datas['transmit'])
        principled_node.inputs['Alpha'].default_value = datas['transmit']
        for key, value in bsdf_inputs.items():
            principled_node.inputs[key].default_value = value
        datas['materials'] = material
        #
        bpy.ops.mesh.primitive_cylinder_add(vertices = vertices, radius=0.1, depth = 1.0)
        cylinder = bpy.context.view_layer.objects.active
        cylinder.name = 'cylinder_atom_kind_{0}'.format(kind)
        cylinder.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        cylinder.hide_set(True)
        mesh = bpy.data.meshes.new('mesh_kind_{0}'.format(kind) )
        obj_bond = bpy.data.objects.new('bond_kind_{0}'.format(kind), mesh )
        # Associate the vertices
        obj_bond.data.from_pydata(datas['verts'], [], datas['faces'])
        # Make the object parent of the cube
        cylinder.parent = obj_bond
        # Make the object dupliverts
        obj_bond.instance_type = 'FACES'
        obj_bond.use_instance_faces_scale = True
        obj_bond.show_instancer_for_render = False
        obj_bond.show_instancer_for_viewport = False
        # bpy.context.view_layer.objects.active = obj_bond
        # obj_bond.select_set(True)
        # bpy.data.objects['bond_kind_{0}'.format(kind)].select_set(True)
        # STRUCTURE.append(obj_bond)
        bpy.data.collections['instancer'].objects.link(cylinder)
        coll_bond_kinds.objects.link(obj_bond)        
        print('bonds: {0}   {1:10.2f} s'.format(kind, time.time() - tstart))

def draw_polyhedra_kind(kind, 
                        datas, 
                        label = None,
                        coll = None,
                        source = None, 
                        bsdf_inputs = None, 
                        material_style = 'blase'):
        """
        """
        source = bond_source(vertices=4)
        if not bsdf_inputs:
            bsdf_inputs = material_styles_dict[material_style]
        tstart = time.time()
        material = bpy.data.materials.new('polyhedra_kind_{0}'.format(kind))
        material.diffuse_color = np.append(datas['color'], datas['transmit'])
        # material.blend_method = 'BLEND'
        material.use_nodes = True
        principled_node = material.node_tree.nodes['Principled BSDF']
        principled_node.inputs['Base Color'].default_value = np.append(datas['color'], datas['transmit'])
        principled_node.inputs['Alpha'].default_value = datas['transmit']
        for key, value in bsdf_inputs.items():
            principled_node.inputs[key].default_value = value
        datas['materials'] = material
        #
        # create new mesh structure
        mesh = bpy.data.meshes.new("mesh_kind_{0}".format(kind))
        # mesh.from_pydata(datas['vertices'], datas['edges'], datas['faces'])  
        mesh.from_pydata(datas['vertices'], [], datas['faces'])  
        mesh.update()
        for f in mesh.polygons:
            f.use_smooth = True
        obj_polyhedra = bpy.data.objects.new("polyhedra_{0}_{1}_face".format(label, kind), mesh)
        obj_polyhedra.data = mesh
        obj_polyhedra.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        #---------------------------------------------------
        material = bpy.data.materials.new('polyhedra_edge_kind_{0}'.format(kind))
        material.diffuse_color = np.append(datas['edge_cylinder']['color'], datas['edge_cylinder']['transmit'])
        # material.blend_method = 'BLEND'
        material.use_nodes = True
        principled_node = material.node_tree.nodes['Principled BSDF']
        principled_node.inputs['Base Color'].default_value = np.append(datas['edge_cylinder']['color'], datas['edge_cylinder']['transmit'])
        principled_node.inputs['Alpha'].default_value = datas['transmit']
        for key, value in bsdf_inputs.items():
            principled_node.inputs[key].default_value = value
        datas['edge_cylinder']['materials'] = material
        verts, faces = cylinder_mesh_from_instance(datas['edge_cylinder']['centers'], datas['edge_cylinder']['normals'], datas['edge_cylinder']['lengths'], 0.01, source)
        # print(verts)
        mesh = bpy.data.meshes.new("mesh_kind_{0}".format(kind))
        mesh.from_pydata(verts, [], faces)  
        mesh.update()
        for f in mesh.polygons:
            f.use_smooth = True
        obj_edge = bpy.data.objects.new("polyhedra_{0}_{1}_edge".format(label, kind), mesh)
        obj_edge.data = mesh
        obj_edge.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        # STRUCTURE.append(obj_polyhedra)
        coll.objects.link(obj_polyhedra)
        coll.objects.link(obj_edge)
        print('polyhedras: {0}   {1:10.2f} s'.format(kind, time.time() - tstart))

def draw_isosurface(coll_isosurface, volume, cell = None, level = None,
                    closed_edges = False, gradient_direction = 'descent',
                    color=(0.85, 0.80, 0.25) , icolor = None, transmit=0.4,
                    verbose = False, step_size = 1, 
                    bsdf_inputs = None, material_style = 'blase'):
    """Computes an isosurface from a volume grid.
    
    Parameters:     
    """
    from skimage import measure
    colors = [(1, 1, 0), (0.0, 0.0, 1.0)]
    if icolor:
        color = colors[icolor]
    cell_vertices = get_cell_vertices(cell)
    cell_vertices.shape = (2, 2, 2, 3)
    cell_origin = cell_vertices[0,0,0]
    #
    spacing = tuple(1.0/np.array(volume.shape))
    mlevel = np.mean(volume)
    if not level:
        level = mlevel*10
    print('iso level: {0:1.9f}, iso mean: {1:1.9f}'.format(level, mlevel))
    scaled_verts, faces, normals, values = measure.marching_cubes_lewiner(volume, level = level,
                    spacing=spacing,gradient_direction=gradient_direction , 
                    allow_degenerate = False, step_size=step_size)
    #
    scaled_verts = list(scaled_verts)
    nverts = len(scaled_verts)
    # transform
    for i in range(nverts):
        scaled_verts[i] = scaled_verts[i].dot(cell)
        scaled_verts[i] -= cell_origin
    faces = list(faces)
    print('Draw isosurface...')
    # print('verts: ', scaled_verts[0:5])
    # print('faces: ', faces[0:5])
    #material
    if not bsdf_inputs:
        bsdf_inputs = material_styles_dict[material_style]
    material = bpy.data.materials.new('isosurface')
    material.name = 'isosurface'
    material.diffuse_color = color + (transmit,)
    # material.alpha_threshold = 0.2
    # material.blend_method = 'BLEND'
    material.use_nodes = True
    principled_node = material.node_tree.nodes['Principled BSDF']
    principled_node.inputs['Base Color'].default_value = color + (transmit,)
    principled_node.inputs['Alpha'].default_value = transmit
    for key, value in bsdf_inputs.items():
            principled_node.inputs[key].default_value = value
    #
    # create new mesh structure
    isosurface = bpy.data.meshes.new("isosurface")
    isosurface.from_pydata(scaled_verts, [], faces)  
    isosurface.update()
    for f in isosurface.polygons:
        f.use_smooth = True
    iso_object = bpy.data.objects.new("isosurface", isosurface)
    iso_object.data = isosurface
    iso_object.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    coll_isosurface.objects.link(iso_object)

def clean_default():
    if 'Camera' in bpy.data.cameras:
        bpy.data.cameras.remove(bpy.data.cameras['Camera'])
    if 'Light' in bpy.data.lights:
        bpy.data.lights.remove(bpy.data.lights['Light'])
    if 'Cube' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['Cube'])



# draw bonds
def bond_source(vertices = 16):
    bpy.ops.mesh.primitive_cylinder_add(vertices = vertices)
    cyli = bpy.context.view_layer.objects.active
    me = cyli.data
    verts = []
    faces = []
    for vertices in me.vertices:
        verts.append(np.array(vertices.co))
    for poly in me.polygons:
        face = []
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            # print("    Vertex: %d" % me.loops[loop_index].vertex_index)
            face.append(me.loops[loop_index].vertex_index)
        faces.append(face)
    cyli.select_set(True)
    bpy.ops.object.delete()
    return [verts, faces]
# draw atoms
def atom_source():
    bpy.ops.mesh.primitive_uv_sphere_add() #, segments=32, ring_count=16)
    # bpy.ops.mesh.primitive_cylinder_add()
    sphe = bpy.context.view_layer.objects.active
    me = sphe.data
    verts = []
    faces = []
    for vertices in me.vertices:
        verts.append(np.array(vertices.co))
    for poly in me.polygons:
        face = []
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            # print("    Vertex: %d" % me.loops[loop_index].vertex_index)
            face.append(me.loops[loop_index].vertex_index)
        faces.append(face)
    sphe.select_set(True)
    bpy.ops.object.delete()
    return [verts, faces]



def sphere_mesh_from_instance(centers, radius, source):
    verts = []
    faces = []
    vert0, face0 = source
    nvert = len(vert0)
    nb = len(centers)
    for i in range(nb):
        center = centers[i]
        # r = radius[i]
        # normal = normal/np.linalg.norm(normal)
        for vert in vert0:
            vert = vert*[radius, radius, radius]
            vert += center
            verts.append(vert)
        for face in face0:
            face = [x+ i*nvert for x in face]
            faces.append(face)
    return verts, faces
def cylinder_mesh_from_instance(centers, normals, lengths, scale, source):
    # verts = np.empty((0, 3), float)
    
    tstart = time.time()
    verts = []
    faces = []
    vert0, face0 = source
    nvert = len(vert0)
    nb = len(centers)
    for i in range(nb):
        center = centers[i]
        normal = normals[i]
        length = lengths[i]
        # normal = normal/np.linalg.norm(normal)
        vec = np.cross([0.0000014159, 0.000001951, 1], normal)
        # print(center, normal, vec)
        vec = vec/np.linalg.norm(vec)
        # print(vec)
        # ang = np.arcsin(np.linalg.norm(vec))
        ang = np.arccos(normal[2]*0.999999)
        vec = -1*ang*vec
        r = R.from_rotvec(vec)
        matrix = r.as_matrix()
        # print(vec, ang)
        vert1 = vert0.copy()
        vert1 = vert1*np.array([scale, scale, length])
        vert1 = vert1.dot(matrix)
        vert1 += center
        for vert in vert1:
            verts.append(vert)
        for face in face0:
            face = [x+ i*nvert for x in face]
            faces.append(face)
    print('cylinder_mesh_from_instance: {0:10.2f} s'.format( time.time() - tstart))

    return verts, faces

