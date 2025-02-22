"""Definition of the Batom class.

This module defines the Batom object in the blase package.

"""

import bpy
import bmesh
from mathutils import Vector
from blase.btools import object_mode
from blase.data import material_styles_dict
from blase.tools import get_atom_kind
from blase.bdraw import draw_text
import numpy as np
import time

subcollections = ['atom', 'bond', 'instancer', 'instancer_atom', 'polyhedra', 'isosurface', 'text']

class Vertice():
    """Vertice Class
    
    Parameters:

    species: list of str
        The atomic structure built using ASE

    positions: array

    Examples:
    >>> from blase.batom import Batom
    >>> c = Batom('C', [[0, 0, 0], [1.2, 0, 0]])
    >>> c.draw_atom()
    """
    

    def __init__(self, 
                species = None,
                position = None,
                element = None,
                x = None,
                y = None,
                z = None,
                ):
        #
        self.species = species
        self.position = position
        self.element = element
        self.x = x
        self.y = y
        self.z = z


class Batom():
    """Batom Class
    
    Then, a Batom object is linked to this main collection in Blender. 

    Parameters:

    label: str

    species: list of str
        The atomic structure built using ASE

    positions: array

    batom_name: str
        Name of the batom

    color_style: str
        "JMOL", "ASE", "VESTA"

    Examples:
    >>> from blase.batom import Batom
    >>> c = Batom('C', [[0, 0, 0], [1.2, 0, 0]])
    >>> c.draw_atom()
    """
    

    def __init__(self, 
                label = None,
                species = None,
                positions = None,
                element = None,
                from_batom = None,
                scale = 1.0, 
                kind_props = {},
                color_style = 'JMOL',
                material_style = 'blase',
                bsdf_inputs = None,
                draw = False, 
                 ):
        #
        self.scene = bpy.context.scene
        if not from_batom:
            self.label = label
            self.species = species
            if not element:
                self.element = species.split('_')[0]
            else:
                self.element = element
            self.name = 'atom_%s_%s'%(self.label, self.species)
            self.kind_props = kind_props
            self.color_style = color_style
            self.material_style = material_style
            self.bsdf_inputs = bsdf_inputs
            self.species_data = get_atom_kind(self.element, scale = scale, props = self.kind_props, color_style = self.color_style)
            self.radius = self.species_data['radius']
            self.set_material()
            self.set_instancer()
            self.set_object(positions)
        else:
            self.from_batom(from_batom)
            #todo self.radius = self.species_data['radius']

        self.bond_data = {}
        self.polyhedra_data = {}
        if draw:
            self.draw_atom()
    def set_material(self):
        name = 'material_atom_{0}_{1}'.format(self.label, self.species)
        if name not in bpy.data.materials:
            if not self.bsdf_inputs:
                bsdf_inputs = material_styles_dict[self.material_style]
            material = bpy.data.materials.new(name)
            material.diffuse_color = np.append(self.species_data['color'], self.species_data['transmit'])
            material.metallic = bsdf_inputs['Metallic']
            material.roughness = bsdf_inputs['Roughness']
            material.blend_method = 'BLEND'
            material.use_nodes = True
            principled_node = material.node_tree.nodes['Principled BSDF']
            principled_node.inputs['Base Color'].default_value = np.append(self.species_data['color'], self.species_data['transmit'])
            principled_node.inputs['Alpha'].default_value = self.species_data['transmit']
            for key, value in bsdf_inputs.items():
                principled_node.inputs[key].default_value = value
    def object_mode(self):
        for object in bpy.data.objects:
            if object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode = 'OBJECT')
    def set_instancer(self):
        object_mode()
        name = 'instancer_atom_{0}_{1}'.format(self.label, self.species)
        if name not in bpy.data.objects:
            bpy.ops.mesh.primitive_uv_sphere_add(radius = self.species_data['radius']) #, segments=32, ring_count=16)
            sphere = bpy.context.view_layer.objects.active
            if isinstance(self.species_data['scale'], float):
                self.species_data['scale'] = [self.species_data['scale']]*3
            sphere.scale = self.species_data['scale']
            sphere.name = 'instancer_atom_{0}_{1}'.format(self.label, self.species)
            sphere.data.materials.append(self.material)
            bpy.ops.object.shade_smooth()
            sphere.hide_set(True)
    def set_object(self, positions):
        """
        build child object and add it to main objects.
        """
        if self.name not in bpy.data.objects:
            mesh = bpy.data.meshes.new(self.name)
            obj_atom = bpy.data.objects.new(self.name, mesh)
            obj_atom.data.from_pydata(positions, [], [])
            obj_atom.is_batom = True
            bpy.data.collections['Collection'].objects.link(obj_atom)
        elif hasattr(bpy.data.objects[self.name], 'batom'):
            obj_atom = bpy.data.objects[self.name]
        else:
            raise Exception("Failed, the name %s already in use and is not blase object!"%self.name)
        obj_atom.species = self.species
        obj_atom.element = self.element
        obj_atom.label = self.label
        self.instancer.parent = obj_atom
        obj_atom.instance_type = 'VERTS'
    def from_batom(self, batom_name):
        if batom_name not in bpy.data.objects:
            raise Exception("%s is not a object!"%batom_name)
        elif not bpy.data.objects[batom_name].is_batom:
            raise Exception("%s is not Batom object!"%batom_name)
        ba = bpy.data.objects[batom_name]
        self.species = ba.species
        self.label = ba.label
        self.element = ba.element
    @property
    def batom(self):
        return self.get_batom()
    def get_batom(self):
        return bpy.data.objects['atom_%s_%s'%(self.label, self.species)]
    @property
    def instancer(self):
        return self.get_instancer()
    def get_instancer(self):
        return bpy.data.objects['instancer_atom_%s_%s'%(self.label, self.species)]
    @property
    def material(self):
        return self.get_material()
    def get_material(self):
        return bpy.data.materials['material_atom_%s_%s'%(self.label, self.species)]
    @property
    def scale(self):
        return self.get_scale()
    @scale.setter
    def scale(self, scale):
        """
        >>> h.scale = 2
        """
        self.set_scale(scale)
    def get_scale(self):
        return self.instancer.scale
    def set_scale(self, scale):
        if isinstance(scale, float) or isinstance(scale, int):
            scale = [scale]*3
        self.instancer.scale = scale
    @property
    def positions(self):
        return self.get_positions()
    @positions.setter
    def positions(self, positions):
        self.set_positions(positions)
    def get_positions(self):
        """
        Get array of positions.
        """
        return np.array([self.batom.matrix_world @ self.batom.data.vertices[i].co for i in range(len(self))])
    def set_positions(self, positions):
        """
        Set positions
        """
        natom = len(self)
        if len(positions) != natom:
            raise ValueError('positions has wrong shape %s != %s.' %
                                (len(positions), natom))
        for i in range(natom):
            self.batom.data.vertices[i].co = np.array(positions[i]) - np.array(self.batom.location)
        
    def clean_blase_objects(self, object):
        """
        remove all bond object in the bond collection
        """
        for obj in bpy.data.collections['%s_%s'%(self.label, object)].all_objects:
            if obj.name == '%s_%s_%s'%(object, self.label, self.species):
                bpy.data.objects.remove(obj)
    def delete_verts(self, index = []):
        """
        delete verts
        """
        object_mode()
        obj = self.batom
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        verts_select = [bm.verts[i] for i in index] 
        bmesh.ops.delete(bm, geom=verts_select, context='VERTS')
        if len(bm.verts) == 0:
            bpy.data.objects.remove(obj)
        else:
            bm.to_mesh(obj.data)
    def delete(self, index = []):
        """
        delete atom.

        index: list
            index of atoms to be delete
        
        For example, delete the second atom in h species. 
        Please note that index start from 0.

        >>> h.delete([1])

        """
        self.delete_verts(index)
    def __delitem__(self, index):
        """
        """
        self.delete(index)
    def draw_constraints(self):
        """
        """
        #
        constr = self.atoms.constraints
        self.constrainatom = []
        for c in constr:
            if isinstance(c, FixAtoms):
                for n, i in enumerate(c.index):
                    self.constrainatom += [i]
    
    def load_frames(self, images = []):
        """
        images: list
            list of positions
        >>> from blase import Batom
        >>> import numpy as np
        >>> positions = np.array([[0, 0 ,0], [1.52, 0, 0]])
        >>> h = Batom('h2o', 'H', positions)
        >>> images = []
        >>> for i in range(10):
                images.append(positions + [0, 0, i])
        >>> h.load_frames(images)
        """
        # render settings
        nimage = len(images)
        batom = self.batom
        nverts = len(batom.data.vertices)
        for i in range(0, nimage):
            positions = images[i]
            for j in range(nverts):
                batom.data.vertices[j].co = np.array(positions[j]) - np.array(batom.location)
                batom.data.vertices[j].keyframe_insert('co', frame=i + 1)
        self.scene.frame_start = 1
        self.scene.frame_end = nimage
    
    def __len__(self):
        return len(self.batom.data.vertices)
    
    def __getitem__(self, index):
        """Return a subset of the Batom.

        i -- int, describing which atom to return.
        """
        batom = self.batom
        if isinstance(index, int):
            natom = len(self)
            if index < -natom or index >= natom:
                raise IndexError('Index out of range.')
            return batom.matrix_world @ batom.data.vertices[index].co
        if isinstance(index, list):
            positions = np.array([batom.matrix_world @ batom.data.vertices[i].co for i in index])
            return positions

    def __setitem__(self, index, value):
        """Return a subset of the Batom.

        i -- int, describing which atom to return.
        """
        batom  =self.batom
        if isinstance(index, int):
            natom = len(self)
            if index < -natom or index >= natom:
                raise IndexError('Index out of range.')
            batom.data.vertices[index].co = np.array(value) - np.array(batom.location)
        if isinstance(index, list):
            for i in index:
                batom.data.vertices[i].co = np.array(value[i]) - np.array(batom.location)

    def repeat(self, m, cell):
        """
        In-place repeat of atoms.

        >>> from blase.batom import Batom
        >>> c = Batom('co', 'C', [[0, 0, 0], [1.2, 0, 0]])
        >>> c.repeat([3, 3, 3], np.array([[5, 0, 0], [0, 5, 0], [0, 0, 5]]))
        """
        if isinstance(m, int):
            m = (m, m, m)
        for x, vec in zip(m, cell):
            if x != 1 and not vec.any():
                raise ValueError('Cannot repeat along undefined lattice '
                                 'vector')
        M = np.product(m)
        n = len(self)
        
        self.positions = self.positions
        positions = np.tile(self.positions, (M,) + (1,) * (len(self.positions.shape) - 1))
        i0 = 0
        for m0 in range(m[0]):
            for m1 in range(m[1]):
                for m2 in range(m[2]):
                    i1 = i0 + n
                    positions[i0:i1] += np.dot((m0, m1, m2), cell)
                    i0 = i1
        self.add_vertices(positions[n:])
    def copy(self, label, species):
        """
        Return a copy.

        name: str
            The name of the copy.

        For example, copy H species:
        
        >>> h_new = h.copy(label = 'h_new', species = 'H')

        """
        object_mode()
        batom = Batom(label, species, self.positions, scale = self.scale)
        return batom
    def extend(self, other):
        """
        Extend batom object by appending batom from *other*.
        
        >>> from blase.batoms import Batom
        >>> h1 = Batom('h2o', 'H_1', [[0, 0, 0], [2, 0, 0]])
        >>> h2 = Batom('h2o', 'H_2', [[0, 0, 2], [2, 0, 2]])
        >>> h = h1 + h2
        """
        # could also use self.add_vertices(other.positions)
        object_mode()
        bpy.ops.object.select_all(action='DESELECT')
        self.batom.select_set(True)
        other.batom.select_set(True)
        bpy.context.view_layer.objects.active = self.batom
        bpy.ops.object.join()
    def __iadd__(self, other):
        """
        >>> h1 += h2
        """
        self.extend(other)
        return self
    def __add__(self, other):
        """
        >>> h1 = h1 + h2
        """
        self += other
        return self
    def __iter__(self):
        batom = self.batom
        for i in range(len(self)):
            yield batom.matrix_world @ batom.data.vertices[i].co
    def __repr__(self):
        s = "Batoms('%s', positions = %s" % (self.species, list(self.positions))
        return s
    def add_vertices(self, positions):
        """
        """
        object_mode()
        bm = bmesh.new()
        bm.from_mesh(self.batom.data)
        bm.verts.ensure_lookup_table()
        verts = []
        for pos in positions:
            bm.verts.new(pos)
        bm.to_mesh(self.batom.data)
    def translate(self, displacement):
        """Translate atomic positions.

        The displacement argument is an xyz vector.

        For example, move H species molecule by a vector [0, 0, 5]

        >>> h.translate([0, 0, 5])
        """
        object_mode()
        bpy.ops.object.select_all(action='DESELECT')
        self.batom.select_set(True)
        bpy.ops.transform.translate(value=displacement)
    def rotate(self, angle, axis = 'Z', orient_type = 'GLOBAL'):
        """Rotate atomic based on a axis and an angle.

        Parameters:

        angle: float
            Angle that the atoms is rotated around the axis.
        axis: str
            'X', 'Y' or 'Z'.

        For example, rotate h2o molecule 90 degree around 'Z' axis:
        
        >>> h.rotate(90, 'Z')

        """
        object_mode()
        bpy.ops.object.select_all(action='DESELECT')
        self.batom.select_set(True)
        bpy.ops.transform.rotate(value=angle, orient_axis=axis.upper(), orient_type = orient_type)
    
    
    