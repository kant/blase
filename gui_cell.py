import bpy
import bmesh
from mathutils import Vector
from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )

from blase.gui_io import import_blase


import os
from math import sqrt
from copy import copy
from ase import Atom, Atoms
from ase.build import molecule, bulk
import json
from blase.bio import Blase
from blase.butils import read_batoms_collection_list, read_batoms_collection, read_atoms_list


# The panel.
class Cell_PT_prepare(Panel):
    bl_label       = "Blase Cell"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    # bl_options     = {'DEFAULT_CLOSED'}
    bl_category = "Cell"
    bl_idname = "BLASE_PT_Cell"

  
    def draw(self, context):
        layout = self.layout
        clpanel = context.scene.clpanel

        box = layout.box()
        row = box.row()
        row.prop(clpanel, "collection_list")

        box = layout.box()
        row = box.row()
        row.prop(clpanel, "pbc")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Cell")
        row = box.row()
        row.prop(clpanel, "cell_a")
        row.prop(clpanel, "cell_b")
        row.prop(clpanel, "cell_c")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="SuperCell")
        row = box.row()
        row.prop(clpanel, "supercell_a")
        row.prop(clpanel, "supercell_b")
        row.prop(clpanel, "supercell_c")
        #
        box = layout.box()
        col = box.column()
        col.prop(clpanel, "boundary")



class CellProperties(bpy.types.PropertyGroup):
    def Callback_collection_list(self, context):
        items = read_batoms_collection_list()
        items = [(item, item, "") for item in items]
        items = tuple(items)
        return items
    def Callback_modify_supercell(self, context):
        clpanel = bpy.context.scene.clpanel
        print('Callback_modify_supercell')
        supercell = [clpanel.supercell_a, clpanel.supercell_b, clpanel.supercell_c]
        modify_supercell(clpanel.collection_list, supercell)
    def Callback_modify_cell(self, context):
        clpanel = bpy.context.scene.clpanel
        print('Callback_modify_cell')
        cell = [clpanel.cell_a, clpanel.cell_b, clpanel.cell_c]
        modify_cell(clpanel.collection_list, cell)
    def Callback_modify_pbc(self, context):
        clpanel = bpy.context.scene.clpanel
        print('Callback_modify_pbc')
        pbc = clpanel.pbc
        modify_pbc(clpanel.collection_list, pbc)
    def Callback_modify_boundary(self, context):
        clpanel = bpy.context.scene.clpanel
        print('Callback_modify_boundary')
        modify_boundary(clpanel.collection_list, clpanel.boundary)

    collection_list: EnumProperty(
        name="Collection",
        description="Collection",
        items=Callback_collection_list)
    pbc: StringProperty(
        name = "pbc", default='True',
        description = "pbc", update = Callback_modify_pbc)
    cell_a: FloatProperty(
        name = "a", default=1,
        description = "cell a")
    cell_b: FloatProperty(
        name = "b", default=1,
        description = "cell b")
    cell_c: FloatProperty(
        name = "c", default=1,
        description = "cell c", update = Callback_modify_cell)
    supercell_a: IntProperty(
        name = "a", default=1,
        description = "cell a")
    supercell_b: IntProperty(
        name = "b", default=1,
        description = "cell b")
    supercell_c: IntProperty(
        name = "c", default=1,
        description = "cell c", update = Callback_modify_supercell)
    boundary: FloatVectorProperty(
        name="Boundary", default=(0.00, 0.0, 0.0),
        subtype = "XYZ",
        description = "boundary  in a, b, c axis", update = Callback_modify_boundary)
    


def modify_cell(collection_name, cell, batoms = None):
    # Modify atom scale (all selected)
    coll = bpy.data.collections[collection_name]
    if not batoms:
        batoms = read_batoms_collection(coll)
    print('drawing atoms')
    batoms.set_cell(cell)
    batoms.draw()

def modify_supercell(collection_name, supercell, batoms = None):
    # Modify atom scale (all selected)
    coll = bpy.data.collections[collection_name]
    if not batoms:
        batoms = read_batoms_collection(coll)
    print('drawing atoms')
    batoms*=supercell
    batoms.draw()
def modify_pbc(collection_name, pbc, batoms = None):
    # Modify atom scale (all selected)
    coll = bpy.data.collections[collection_name]
    if not batoms:
        batoms = read_batoms_collection(coll)
    batoms.atoms.pbc = pbc
def modify_boundary(collection_name, cutoff, batoms = None):
    # Modify atom cutoff (all selected)
    coll = bpy.data.collections[collection_name]
    if not batoms:
        batoms = read_batoms_collection(coll)
    print('drawing atoms')
    batoms.coll.blase.boundary = cutoff
    # if batoms.atoms.pbc.any():
        # batoms.draw_atoms_boundary(cutoff=cutoff)
    batoms.draw()