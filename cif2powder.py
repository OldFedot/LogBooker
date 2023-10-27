import string

import numpy as np
from cif_manager import CifManager
import itertools


class Reflection:
    def __init__(self, h, k, l, d_spacing, intensity=None, multiplicity=1):
        self.h = h
        self.k = k
        self.l = l
        self.multiplicity = multiplicity
        self.d_spacing = d_spacing

    def __repr__(self):
        return "({},{},{}) x {} {:.5f}".format(self.h, self.k, self.l, self.multiplicity,
                                                    self.d_spacing)


class CifPhase:
    def __init__(self):
        self.cm = CifManager()
        self.wavelength = 0
        self.a = 0
        self.b = 0
        self.c = 0
        self.alpha = 0
        self.beta = 0
        self.gamma = 0
        self.symmetry = ""

    def update(self, path_to_cif):
        cif_dict = self.cm.get_all_parameters(path_to_cif)
        self.a = self.cm.error_from_brackets(cif_dict["_cell_length_a"])[0]
        self.b = self.cm.error_from_brackets(cif_dict["_cell_length_b"])[0]
        self.c = self.cm.error_from_brackets(cif_dict["_cell_length_c"])[0]
        self.alpha = self.cm.error_from_brackets(cif_dict["_cell_angle_alpha"])[0]
        self.beta = self.cm.error_from_brackets(cif_dict["_cell_angle_beta"])[0]
        self.gamma = self.cm.error_from_brackets(cif_dict["_cell_angle_gamma"])[0]
        self.wavelength = cif_dict["_diffrn_radiation_wavelength"]
        self.symmetry = cif_dict["_space_group_crystal_system"].upper()
        self.symmetry = "".join([symb for symb in self.symmetry if symb not in string.punctuation])

    def show_attr(self):
        print("Wavelength: ", self.wavelength)
        print("Symmetry: ", self.symmetry)
        print("a: ", self.a)
        print("b: ", self.b)
        print("c: ", self.c)
        print("alpha: ", self.alpha)
        print("beta: ", self.beta)
        print("gamma: ", self.gamma)


class Cif2D:
    def __init__(self, path_to_cif="D:/Python_Projects/LogBooker2.0/test_data/Bhaskar\p098.cif"):
        self.cif_phase = CifPhase()
        self.cif_phase.update(path_to_cif)
        self.cif_phase.show_attr()
        self.wavelength = 0.29
        self.min_d_spacing = 1

    def calculate_hkl_within_sphere_and_min_d_spacing(self):
        """
        Generates a list of hkl reflections which can satisfy the diffraction condition using the given wavelength and
        also the minimum d spacing
        :return: list of reflections
        :rtype: list[Reflection]
        """
        max_h = np.floor(2 * self.cif_phase.a / self.wavelength)
        max_k = np.floor(2 * self.cif_phase.b / self.wavelength)
        max_l = np.floor(2 * self.cif_phase.c / self.wavelength)

        h = list(reversed(np.arange(-max_h + 1, max_h, 1)))
        k = list(reversed(np.arange(-max_k + 1, max_k, 1)))
        l = list(reversed(np.arange(-max_l + 1, max_l, 1)))
        s = [h, k, l]

        reciprocal_hkl = np.array(list(itertools.product(*s)))
        h = reciprocal_hkl[:, 0]
        k = reciprocal_hkl[:, 1]
        l = reciprocal_hkl[:, 2]

        d_hkl = self.compute_d_hkl(h, k, l)

        good_indices = np.argwhere(d_hkl > self.min_d_spacing)
        reflections = []
        for i in good_indices:
            print(d_hkl[i][0])

            #reflections.append(Reflection(int(h[i][0]), int(k[i][0]), int(l[i][0]), d_hkl[i][0]))

        return reflections

    def compute_d_hkl(self, h, k, l):
        a = self.cif_phase.a
        b = self.cif_phase.b
        c = self.cif_phase.c
        alpha = np.deg2rad(self.cif_phase.alpha)
        beta = np.deg2rad(self.cif_phase.beta)
        gamma = np.deg2rad(self.cif_phase.gamma)
        symmetry = str(self.cif_phase.symmetry)

        if symmetry == 'CUBIC':
            d2inv = (h ** 2 + k ** 2 + l ** 2) / a ** 2
        elif symmetry == 'TETRAGONAL':
            d2inv = (h ** 2 + k ** 2) / a ** 2 + l ** 2 / c ** 2
        elif symmetry == 'ORTHORHOMBIC':
            d2inv = h ** 2 / a ** 2 + k ** 2 / b ** 2 + l ** 2 / c ** 2
        elif symmetry == 'HEXAGONAL' or symmetry == 'TRIGONAL':
            d2inv = (h ** 2 + h * k + k ** 2) * 4. / 3. / a ** 2 + l ** 2 / c ** 2
        elif symmetry == 'RHOMBOHEDRAL':
            d2inv = (((1. + np.cos(alpha)) * ((h ** 2 + k ** 2 + l ** 2) -
                                              (1 - np.tan(0.5 * alpha) ** 2) * (h * k + k * l + l * h))) /
                     (a ** 2 * (1 + np.cos(alpha) - 2 * np.cos(alpha) ** 2)))
        elif symmetry == 'MONOCLINIC':
            d2inv = (h ** 2 / np.sin(beta) ** 2 / a ** 2 +
                     k ** 2 / b ** 2 +
                     l ** 2 / np.sin(beta) ** 2 / c ** 2 +
                     2 * h * l * np.cos(beta) / (a * c * np.sin(beta) ** 2))
        elif symmetry == 'TRICLINIC':
            V = (a * b * c *
                 np.sqrt(1. - np.cos(alpha) ** 2 - np.cos(beta) ** 2 -
                         np.cos(gamma) ** 2 +
                         2 * np.cos(alpha) * np.cos(beta) * np.cos(gamma)))
            s11 = b ** 2 * c ** 2 * np.sin(alpha) ** 2
            s22 = a ** 2 * c ** 2 * np.sin(beta) ** 2
            s33 = a ** 2 * b ** 2 * np.sin(gamma) ** 2
            s12 = a * b * c ** 2 * (np.cos(alpha) * np.cos(beta) -
                                    np.cos(gamma))
            s23 = a ** 2 * b * c * (np.cos(beta) * np.cos(gamma) -
                                    np.cos(alpha))
            s31 = a * b ** 2 * c * (np.cos(gamma) * np.cos(alpha) -
                                    np.cos(beta))
            d2inv = (s11 * h ** 2 + s22 * k ** 2 + s33 * l ** 2 +
                     2. * s12 * h * k + 2. * s23 * k * l + 2. * s31 * l * h) / V ** 2

        d2inv = d2inv[d2inv != 0]
        d_spacings = np.sqrt(1. / d2inv)
        return d_spacings


def main():
    cif_2_powder = Cif2D()
    cif_2_powder.calculate_hkl_within_sphere_and_min_d_spacing()


if __name__ == "__main__":
    main()
