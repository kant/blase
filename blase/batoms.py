"""Definition of the Batoms class.

This module defines the atoms object in the blase package.

"""

from ase import Atom, Atoms
import os
import bpy
import mathutils as mu
import bmesh
from mathutils import Vector
from math import sqrt
from copy import copy
from blase.tools import get_atom_kinds, get_bond_kinds, get_bondpairs, get_cell_vertices, get_polyhedra_kinds, search_pbc, get_bbox
from blase.bdraw import draw_cell, draw_atoms, draw_atom_kind, draw_bonds, draw_polyhedras, draw_isosurface, bond_source, cylinder_mesh_from_instance, clean_default
import numpy as np
from ase.cell import Cell
import time





subcollections = ['atoms', 'bonds', 'instancers', 'cell', 'polyhedras', 'isosurfaces', 'boundary']


class Batoms():
    """Batoms Class
    In Blender, the atoms objects and collections are organised in the following way, 
    take water molecule as a example:
    --h2o                            --main collection
    ----h2o_atoms                    --atoms collection
    ------atom_h2o_H                 --atoms object
    ------atom_h2o_O                 --atoms object
    ----h2o_bonds                    --bonds collection
    ------bond_h2o_H                 --bond object
    ------bond_h2o_O                 --bond object
    ----h2o_cell                     --cell collection
    ----h2o_instancers               --instancer collection
    ------sphere_h2o_H               --sphere object
    ------sphere_h2o_O               --sphere object
    
    Then, a Batoms object is linked to this main collection in Blender. 
    The main collection has two parameters:
    (1) blase, it has 'is_blase', 'pbc', 'unit cell', 'boundary' and 'model_type'
    (2) batoms, it has all the symbols and postions


    Parameters:

    atoms: 
        ASE atom object
    coll: 
        Blender collection
    model_type: str
        enum in '0', '1', '2', '3'
    boundary:  list 
        search atoms at the boundary
    add_bonds: dict
        add bonds not in the default
    
    Examples:

    These three are equivalent:

    >>> from ase.build import molecule
    >>> from blase.batoms import Batoms
    >>> h2o = molecule('H2O')
    >>> h2o = Batoms(h2o)
    >>> h2o.draw()

    
    """

    def __init__(self, 
                 coll = None,
                 atoms = None, 
                 name = None,
                 model_type = '0', 
                 scale = 1.0, 
                 boundary = [0.0, 0.0, 0.0],
                 add_bonds = {}, 
                 remove_bonds = {},
                 polyhedra_dict = {},
                 show_unit_cell = True,
                 kind_props = {},
                 color = 'JMOL',
                 movie = False,
                 draw = False, 
                 ):
        #
        self.scene = bpy.context.scene
        self.scale = scale,
        self.add_bonds = add_bonds
        self.remove_bonds = remove_bonds
        self.polyhedra_dict = polyhedra_dict
        self.show_unit_cell = show_unit_cell
        self.kind_props = kind_props
        self.name = name
        self.color = color
        if atoms:
            print('Build from atoms')
            print(atoms.info)
            if not isinstance(atoms, list):
                atoms = [atoms]
            self.images = atoms
            # batoms save the real objects
            self.batoms = atoms[0]
            # atms save all the atoms to be drawed. including the boundary atoms.
            self.atoms = self.batoms.copy()
            if not self.name:
                self.name = self.batoms.symbols.formula.format('abc')
            # add new collection
            self.set_collection()
            # save atoms to blase.atoms
            self.atoms2batoms()
            self.coll.blase.model_type = model_type
            self.coll.blase.boundary = boundary
            self.coll.blase.pbc = self.npbool2bool(self.batoms.pbc)
            self.coll.blase.cell = self.batoms.cell[:].flatten()
        elif coll:
            print('Build from collection')
            self.coll = coll
            self.batoms = self.batoms2atoms()
            self.atoms = self.batoms.copy()
        else:
            raise Exception("Failed, either atoms or coll should be provided!"%self.name)
        if draw:
            self.draw()
        if movie:
            self.load_frames()
    def npbool2bool(self, pbc):
        newpbc = []
        for i in range(3):
            if pbc[i]:
                newpbc.append(True)
            else:
                newpbc.append(False)
        return newpbc
    def atoms2batoms(self, atoms = None):
        """
        """
        tstart = time.time()
        if not atoms:
            atoms = self.atoms
        for atom in atoms:
            batom = self.coll.batoms.add()
            batom.symbol = atom.symbol
            batom.position = atom.position
        print('set atoms2batoms: {0:10.2f} s'.format(time.time() - tstart))
    def batoms2atoms(self, coll = None):
        """
        """
        from ase import Atom, Atoms
        atoms = Atoms()
        tstart = time.time()
        if not coll:
            coll = self.coll
        for batom in coll.batoms:
            atom = Atom(symbol = batom.symbol, 
                        position = batom.position)
            atoms.append(atom)
        atoms.pbc = coll.blase.pbc
        atoms.cell = np.array(coll.blase.cell).reshape(3, 3)
        print('set batoms2atoms: {0:10.2f} s'.format(time.time() - tstart))
        return atoms
    def set_collection(self):
        """
        """
        for coll in bpy.data.collections:
            if self.name == coll.name:
                raise Exception("Failed, the name %s already in use!"%self.name)
        self.coll = bpy.data.collections.new(self.name)
        self.coll.blase.is_blase = True
        self.scene.collection.children.link(self.coll)
        for sub_name in subcollections:
            subcoll = bpy.data.collections.new('%s_%s'%(self.name, sub_name))
            self.coll.children.link(subcoll)
    def search_boundary(self, ):
        """
        """
        boundary =  np.array(self.coll.blase.boundary[:]) > 0.0
        if self.atoms.pbc.any() and boundary.any():
            bd_atoms, bd_index = search_pbc(self.atoms, self.coll.blase.boundary)
            self.atoms = self.batoms + bd_atoms
            self.atoms.info['species'] = self.atoms.info['species'] + bd_atoms.info['species']
        else:
            self.atoms = self.batoms
    def draw_cell(self):
        """
        """
        print('--------------Draw cell--------------')
        cell_vertices = get_cell_vertices(self.coll.blase.cell)
        for obj in self.coll.children['%s_cell'%self.name].all_objects:
            bpy.data.objects.remove(obj)
        if self.show_unit_cell:
            draw_cell(self.coll.children['%s_cell'%self.name], cell_vertices)
    def draw_atoms(self, scale = None, kind_props = {}):
        """
        atom_kinds
        """
        print('--------------Draw atoms--------------')
        for obj in self.coll.children['%s_atoms'%self.name].all_objects:
            bpy.data.objects.remove(obj)
        for obj in self.coll.children['%s_instancers'%self.name].all_objects:
            bpy.data.objects.remove(obj)
        if scale:
            self.scale = scale
        if not kind_props:
            kind_props = self.kind_props
        self.search_boundary()
        self.atom_kinds = get_atom_kinds(self.atoms, scale = self.scale, props = kind_props, color = self.color)
        draw_atoms(self.coll.children['%s_atoms'%self.name], self.atom_kinds)
    def draw_bonds(self, cutoff = 1.0):
        """
        bond_kinds
        """
        print('--------------Draw bonds--------------')
        for obj in self.coll.children['%s_bonds'%self.name].all_objects:
            bpy.data.objects.remove(obj)
        print(self.atoms.info)
        self.bond_list = get_bondpairs(self.atoms, add_bonds = self.add_bonds, remove_bonds=self.remove_bonds)
        self.bond_kinds = get_bond_kinds(self.atoms, self.atom_kinds, self.bond_list, color = self.color)
        draw_bonds(self.coll.children['%s_bonds'%self.name], self.bond_kinds)
    def draw_polyhedras(self, cutoff = 1.0):
        """
        bond_kinds
        """
        print('--------------Draw bonds--------------')
        for obj in self.coll.children['%s_polyhedras'%self.name].all_objects:
            bpy.data.objects.remove(obj)
        polyhedra_kinds = get_polyhedra_kinds(self.atoms, self.atom_kinds, self.bond_list, polyhedra_dict = self.polyhedra_dict)
        draw_polyhedras(self.coll.children['%s_polyhedras'%self.name], polyhedra_kinds)
    def draw_isosurface(self):
        """
        """
        if self.isosurface:
            volume = self.isosurface[0]
            icolor = 0
            if len(self.isosurface) == 1:
                draw_isosurface(self.coll.children['%s_isosurface'%self.name], volume, level=None, icolor = icolor)
            for level in self.isosurface[1:]:
                draw_isosurface(self.coll.children['%s_isosurface'%self.name], volume, level=level, icolor = icolor)
                icolor += 1
    def draw(self, model_type = None):
        """
        """
        if not model_type:
            model_type = self.coll.blase.model_type
        else:
            self.coll.blase.model_type = model_type
        self.draw_cell()
        if model_type == '0':
            self.scale = 1.0
            self.draw_atoms()
        elif model_type == '1':
            # view(images)
            self.scale = 0.4
            self.draw_atoms()
            self.draw_bonds()
        elif model_type == '2':
            self.scale = 0.4
            self.draw_atoms()
            self.draw_bonds()
            self.draw_polyhedras()
        elif model_type == '3':
            self.scale = 0.4
            self.draw_atoms()
            self.draw_bonds()
    def replace(self, index = [], element = None):
        """
        replace atoms
        """
        from blase.tools import default_atom_kind
        # delete old verts
        self.delete_verts(index)
        # if kind exists, merger, otherwise build a new kind and add.
        name = 'atom_kind_{0}'.format(element)
        positions = self.atoms.positions[index]
        if name in self.coll.children['%s_atoms'%self.name].objects:
            obj = self.coll.children['%s_atoms'%self.name].objects[name]
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            verts = []
            for pos in positions:
                bm.verts.new(pos)
            bm.to_mesh(obj.data)
        else:
            atom_kind = default_atom_kind(element, positions, color=self.color)
            draw_atom_kind(element, self.coll.children['%s_atoms'%self.name], atom_kind)
        # ase atoms
        self.atoms.symbols[index] = element
    def delete_verts(self, index = []):
        """
        delete atoms
        (1) atoms kinds, positions
        (2) obj_atom
        """
        # atoms.bobj.coll.children[1].all_objects[0].data.vertices[0].co
        for kind, obj in self.coll.children['%s_atoms'%self.name].objects.items():
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            inds = [atom.index for atom in self.atoms if atom.symbol==kind.split('_')[-1]]
            verts_select = [bm.verts[i] for i in range(len(bm.verts)) if inds[i] in index] 
            bmesh.ops.delete(bm, geom=verts_select, context='VERTS')
            if len(bm.verts) == 0:
                bpy.data.objects.remove(obj)
            else:
                bm.to_mesh(obj.data)
    def delete(self, index = []):
        self.delete_verts(index)
        del self.atoms[index]
    def translate(self, displacement):
        """Translate atomic positions.

        The displacement argument can be a float an xyz vector or an
        nx3 array (where n is the number of atoms)."""

        self.atoms.arrays['positions'] += np.array(displacement)
        for kind, obj in self.coll.children['%s_atoms'%self.name].objects.items():
            for vertice in obj.data.vertices:
                vertice.co += mu.Vector(displacement)
    def __add__(self, other):
        self += other
        return self
    def __iadd__(self, other):
        self.extend(other)
        return self
    def extend(self, other):
        """Extend atoms object by appending atoms from *other*."""
        self.atoms = self.atoms + other.atoms
        for kind, obj in other.coll.children['%s_atoms'%other.name].objects.items():
            if kind in self.coll.children['%s_atoms'%self.name].objects:
                objs = [obj, self.coll.children['%s_atoms'%self.name].objects[kind]]
                bpy.ops.object.join(objs)
            else:
                self.coll.children['%s_atoms'%self.name].objects.link(obj)
        bpy.data.collections.remove(other.coll)
    def __imul__(self, m):
        """In-place repeat of atoms."""
        self.atoms *= m
        if 'kinds' in self.atoms.info:
            del self.atoms.info['kinds']
        self.update()
        return self
    def repeat(self, rep):
        """Create new repeated atoms object."""
        self.__imul__(rep)
    def __mul__(self, rep):
        self.repeat(rep)
        return self
    def copy(self, name = None):
        """Return a copy."""
        if not name:
            name = self.name + 'copy'
        batoms = self.__class__(self.atoms, name = name, draw = True)
        return batoms
    def update(self):
        """
        """
        self.draw()

    def set_cell(self, cell, scale_atoms=False):
        """Set unit cell vectors.

        Parameters:

        Examples:

        """

        # Override pbcs if and only if given a Cell object:
        self.atoms.set_cell(cell, scale_atoms = scale_atoms)
        self.coll.blase.cell = self.atoms.cell[:].flatten()
        self.update()
    
    def draw_constraints(self):
        #
        constr = self.atoms.constraints
        self.constrainatoms = []
        for c in constr:
            if isinstance(c, FixAtoms):
                for n, i in enumerate(c.index):
                    self.constrainatoms += [i]
    
    def highlight_atoms(self, indexs, shape = 'sphere', radius_scale=1.4,
                           color=(0.0, 1.0, 0.0), transmit=0.6):
        """
        """
        # Draw atoms
        #
        coll_highlight = bpy.data.collections.new('highlight')
        self.coll.children.link(coll_highlight)
        # build materials
        material = bpy.data.materials.new('highlight')
        material.name = 'highlight'
        material.diffuse_color = color + (transmit,)
        # material.alpha_threshold = 0.2
        material.blend_method = 'BLEND'
        material.use_nodes = True
        principled_node = material.node_tree.nodes['Principled BSDF']
        principled_node.inputs['Alpha'].default_value = transmit
        # i = 0
        for index in indexs:
            loc = self.positions[index]
            ele = self.symbols[index]
            radii = radius_scale * self.atom_kinds[ele]['radius']
            if shape == 'cube':
                bpy.ops.mesh.primitive_cube_add(location=loc, size=radii*2)
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(location=loc, radius=radii)
            ball = bpy.context.view_layer.objects.active
            bpy.ops.object.shade_smooth()
            ball.data.materials.append(material)
            ball.show_transparent = True
            coll_highlight.objects.link(ball)
    def load_frames(self, nimages = None):
        # render settings
        if not nimages:
            nimages = len(self.images)
        for i in range(0, nimages):
            atom_kinds = get_atom_kinds(self.images[i])
            # bond_kinds = get_bond_kinds(self.images[i], bond_list, self.nbins)
            for kind, datas in atom_kinds.items():
                obj_atom = bpy.data.objects['atom_{0}_{1}'.format(self.name, kind)]
                nverts = len(obj_atom.data.vertices)
                for j in range(nverts):
                    obj_atom.data.vertices[j].co = datas['positions'][j]
                    obj_atom.data.vertices[j].keyframe_insert('co', frame=i + 1)
        self.scene.frame_start = 1
        self.scene.frame_end = nimages
    
    def render(self, **kwargs):
        """
        """
        from blase.bio import Blase
        print('--------------Render--------------')
        print('Rendering atoms')
        if 'bbox' not in kwargs:
            bbox = get_bbox(bbox = None, atoms = self.atoms)
            kwargs['bbox'] = bbox
        if 'output_image' not in kwargs:
            kwargs['output_image'] = '%s.png'%self.name
        # print(kwargs)
        obj = Blase(**kwargs)
        obj.render()

