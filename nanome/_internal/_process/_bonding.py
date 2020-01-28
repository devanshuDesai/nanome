from nanome.util import Process, Logs
from nanome._internal._structure import _Complex, _Bond
from nanome._internal._structure._io import _pdb, _sdf

import tempfile
import os


class _Bonding():
    def __init__(self, complex_list, callback, fast_mode=None, nano=False):
        self.__complexes = complex_list
        self.__framed_complexes = [complex.convert_to_frames() for complex in complex_list]
        self.__callback = callback

        atom_count = 0
        if fast_mode == None:
            for complex in complex_list:
                atom_count += sum(atom._conformer_count for atom in complex.atoms)
            self.__fast_mode = atom_count > 20000
        else:
            self.__fast_mode = fast_mode

    def _start(self):
        self.__complex_idx = 0
        self.__molecule_idx = -1
        self.__input = tempfile.NamedTemporaryFile(delete=False, suffix='.pdb')
        self.__output = tempfile.NamedTemporaryFile(delete=False, suffix='.mol')

        self.__proc = Process()
        self.__proc.executable_path = 'nan' if nano else '' + 'obabel'
        self.__proc.args = ['-ipdb', self.__input.name, '-osdf', '-O' + self.__output.name]
        self.__proc.output_text = True
        self.__proc.on_error = self.__on_error
        self.__proc.on_done = self.__bonding_done
        if self.__fast_mode:
            self.__proc.args.append('-f')

        self.__next()

    def __next(self):
        # Go to next molecule
        complex = self.__complexes[self.__complex_idx]
        framed_complex = self.__framed_complexes[self.__complex_idx]

        self.__molecule_idx += 1
        if self.__molecule_idx >= len(framed_complex._molecules):
            self.__complex_idx += 1
            if self.__complex_idx >= len(self.__complexes):
                self.__done()
                return

            complex = self.__complexes[self.__complex_idx]
            framed_complex = self.__framed_complexes[self.__complex_idx]
            self.__molecule_idx = 0

        self.__saved_complex = complex
        self.__saved_is_conformer = len(complex._molecules) == 1

        molecule = framed_complex._molecules[self.__molecule_idx]
        single_frame = _Complex._create()
        single_frame._add_molecule(molecule)
        _pdb.to_file(self.__input.name, single_frame)

        self.__proc.start()

    def __on_error(self, msg):
        if not "molecule converted" in msg:
            Logs.warning("[Bond Generation]", msg)

    def __bonding_done(self, result_code):
        if result_code == -1:
            Logs.error("Couldn't execute openbabel to generate bonds. Is it installed?")
            self.__callback(self.__complexes)
            return
        with open(self.__output.name) as f:
            lines = f.readlines()
        content = _sdf.parse_lines(lines)
        result = _sdf.structure(content)
        self.__match_and_bond(result)
        self.__next()

    def __get_bond(self, atom1, atom2):
        if atom1.serial > atom2.serial:
            atom1, atom2 = atom2, atom1
        for bond in atom1._bonds:
            if bond._atom1 == atom1 and bond._atom2 == atom2:
                return bond
        return None

    def __match_and_bond(self, bonding_result):
        if self.__molecule_idx == 0:
            for atom in self.__saved_complex.atoms:
                atom._bonds.clear()
            for residue in self.__saved_complex.residues:
                residue._bonds.clear()

        if self.__molecule_idx == 0 or not self.__saved_is_conformer:
            self.__atom_by_serial = dict()
            molecule = self.__saved_complex._molecules[self.__molecule_idx]
            for atom in molecule.atoms:
                self.__atom_by_serial[atom._serial] = atom

        for bond in bonding_result.bonds:
            serial1 = bond._atom1._serial
            serial2 = bond._atom2._serial
            if serial1 in self.__atom_by_serial and serial2 in self.__atom_by_serial:
                atom1 = self.__atom_by_serial[serial1]
                atom2 = self.__atom_by_serial[serial2]
                residue = atom1._residue

                new_bond = self.__get_bond(atom1, atom2)
                if new_bond is None:
                    new_bond = _Bond._create()
                    if self.__saved_is_conformer:
                        conformer_count = atom1.conformer_count
                        new_bond._kinds = [new_bond._kind] * conformer_count
                        new_bond._in_conformer = [False] * conformer_count

                    new_bond._atom1 = atom1
                    new_bond._atom2 = atom2
                    residue._add_bond(new_bond)

                if self.__saved_is_conformer:
                    current_conformer = self.__molecule_idx
                    new_bond._in_conformer[current_conformer] = True

    def __done(self):
        self.__input.close()
        self.__output.close()
        os.remove(self.__input.name)
        os.remove(self.__output.name)
        self.__callback(self.__complexes)
