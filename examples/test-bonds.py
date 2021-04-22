from ase.io import read, write
from ase.visualize import view
from blase.tools import write_blender, get_polyhedra_kinds, get_bondpairs
import numpy as np
from pprint import pprint
from ase.data import covalent_radii


atoms = read('datas/tio2.cif')
atoms = atoms*[2, 2, 2]
# view(atoms)
bond_list = get_bondpairs(atoms, cutoff=1.0)
# pprint(bond_list)
kwargs = {'name': 'tio2',
          'show_unit_cell': 1, 
          'engine': 'BLENDER_WORKBENCH', #'BLENDER_EEVEE' #'BLENDER_WORKBENCH', CYCLES
          'radii': 0.3,
          'bond_cutoff': 1.0,
          'display': True,
          # 'search_pbc': {'bonds_dict': {'O': [['Ti'], -1]}},
        #   'polyhedra_dict': {'Ti': ['O']},
          'outfile': 'figs/test-search-bonds',
          }
write_blender(atoms, **kwargs)
