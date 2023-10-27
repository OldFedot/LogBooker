import os
import numpy as np
import pandas as pd
import string
from decimal import Decimal
from sum_manager import SumManager


class CifManager:
    def __init__(self):
        self.blank = "---"
        self.delta = "\u0394"
        # Settings
        self.exceptions = []
        self.requests = []
        # General cif data
        self.data_columns = {"Path": "Path",  # Filename
                             "Filename": "Filename",  # Filename
                             "_chemical_formula_sum": "Formula",  # chemical formula
                             "_symmetry_cell_setting": "CS",  # symmetry setting Jana
                             "_space_group_crystal_system": "CS",  # symmetry setting Olex
                             "_symmetry_space_group_name_H-M": "SG",  # space group Jana
                             "_space_group_name_H-M_alt": "SG",  # space group Olex
                             "_diffrn_reflns_av_R_equivalents": "Rint",  # R_int
                             "_refine_ls_R_factor_gt": "R1",  # R1 factor
                             "_refine_ls_wR_factor_ref": "wR2",  # wR2 factor
                             "_cell_length_a": "a(\u212B)",  # a
                             "_cell_length_b": "b(\u212B)",  # b
                             "_cell_length_c": "c(\u212B)",  # c
                             "_cell_angle_alpha": "\u03B1(\u00b0)",  # alpha
                             "_cell_angle_beta": "\u03B2(\u00b0)",  # betta
                             "_cell_angle_gamma": "\u03B3(\u00b0)",  # gamma
                             "_cell_volume": "V(" + u"\u212B^3)",  # volume
                             "_diffrn_radiation_wavelength": "Wavelength(\u212B)",  # Wavelength
                             "_cell_formula_units_Z": "Z",  # formula units
                             "_reflns_number_total": "N_all.",  # number of all reflections
                             "_reflns_number_gt": "N_obs",  # number of observed reflections
                             "_audit_creation_method": "Program",
                             "_exptl_absorpt_correction_type": "Abs.cor.",
                             "UB matrix": "UM"
                             }
        # Relation of errors
        self.error_columns = {"a(\u212B)": "\u0394a(\u212B)",  # delta_a
                              "b(\u212B)": "\u0394b(\u212B)",  # delta_b
                              "c(\u212B)": "\u0394c(\u212B)",  # delta_c
                              "\u03B1(\u00b0)": "\u0394\u03B1(\u00b0)",  # delta_alpha
                              "\u03B2(\u00b0)": "\u0394\u03B2(\u00b0)",  # delta_betta
                              "\u03B3(\u00b0)": "\u0394\u03B3(\u00b0)",  # delta_gamma
                              "V(" + u"\u212B^3)": "\u0394V" + "(\u212B^3)"  # delta_volume
                              }
        # Ub matrix
        self.ub_dict = {"_diffrn_orient_matrix_UB_11": "",
                        "_diffrn_orient_matrix_UB_12": "",
                        "_diffrn_orient_matrix_UB_13": "",
                        "_diffrn_orient_matrix_UB_21": "",
                        "_diffrn_orient_matrix_UB_22": "",
                        "_diffrn_orient_matrix_UB_23": "",
                        "_diffrn_orient_matrix_UB_31": "",
                        "_diffrn_orient_matrix_UB_32": "",
                        "_diffrn_orient_matrix_UB_33": ""}
        # Atomic coordinates
        self.atom_site_order = {}
        self.atom_site_relations = {"Filename": "---",
                                    "atom label": "_atom_site_label",
                                    "atom type": "_atom_site_type_symbol",
                                    "x": "_atom_site_fract_x",
                                    "y": "_atom_site_fract_y",
                                    "z": "_atom_site_fract_z",
                                    "adp_type": "_atom_site_adp_type",
                                    "U_iso_or_equiv": "_atom_site_U_iso_or_equiv",
                                    "occupancy": "_atom_site_occupancy"
                                    }
        # Atomic ADP's
        self.atom_adp_order = {}
        self.atom_adp_relations = {"atom label": "_atom_site_aniso_label",
                                   "U_11": "_atom_site_aniso_U_11",
                                   "U_22": "_atom_site_aniso_U_22",
                                   "U_33": "_atom_site_aniso_U_33",
                                   "U_12": "_atom_site_aniso_U_12",
                                   "U_13": "_atom_site_aniso_U_13",
                                   "U_23": "_atom_site_aniso_U_23",
                                   }
        # Bond distances
        self.bond_distance_relations = {"atom_label_1": "_geom_bond_atom_site_label_1",
                                        "atom_label_2": "_geom_bond_atom_site_label_2",
                                        "bond_distance": "_geom_bond_distance"}
        self.bond_distance_order = {}
        # Interatomic angles
        self.angle_relations = {"atom_label_1": "_geom_angle_atom_site_label_1",
                                "atom_label_2": "_geom_angle_atom_site_label_2",
                                "atom_label_3": "_geom_angle_atom_site_label_3",
                                "angle": "_geom_angle"}
        self.angle_order = {}
        # Interatomic torsions
        self.torsion_relations = {"atom_label_1": "_geom_torsion_atom_site_label_1",
                                  "atom_label_2": "_geom_torsion_atom_site_label_2",
                                  "atom_label_3": "_geom_torsion_atom_site_label_3",
                                  "atom_label_4": "_geom_torsion_atom_site_label_4",
                                  "torsion": "_geom_torsion"
                                  }
        self.torsion_order = {}
        # Default Data Frames
        self.default_df = self.default_cif_df()
        self.atom_coord_df = pd.DataFrame(
            columns=list(self.atom_site_relations.keys()) + list(self.atom_adp_relations.keys())[1:])

        # User defined bonds/angles/torsions
        self.ud_bonds = []
        self.ud_angles = []
        self.ud_torsions = []

        # Containers for bonds/angles/tortions data
        self.bonds_df = pd.DataFrame()
        self.angles_df = pd.DataFrame()
        self.torsions_df = pd.DataFrame()

    def extract_loop(self, cif_file):
        buffer = ""
        counter = 0
        params = {}
        while True:
            line = cif_file.readline()
            if not line.split():
                break
            elif not line.startswith(" "):
                break
            elif line.split()[0].startswith("_"):
                params[line.split()[0]] = counter
                counter += 1
            else:
                buffer += line + "\t"

        return params, buffer

    def get_all_parameters(self, path):
        """ Every command in cif file starts with "_", but there are several cases to parse:
        1st: single line command + value
          In that case value is at the same line with command
        2nd: command + single line values
          Single line value after the command, values is in between "'" single quotes.
        3rd: command + multiple lines values
          Multiple lines values surrounded by ";" lines on the top and bottom
        """
        cif_dict = {}
        with open(path, "r") as cif_file:
            line = True
            while line:
                line = cif_file.readline()
                # If the line is empty, go the next line
                if not line.split():
                    continue
                # Extracting _loop
                elif line.startswith("loop_\n"):
                    params, buffer = self.extract_loop(cif_file)
                    # Extracting atomic coordinates
                    if any(key in self.atom_site_relations.values() for key in params.keys()):
                        self.atom_site_order = params
                        cif_dict["atomic_coordinates"] = buffer
                        continue
                    # Extracting ADP parameters
                    elif any(key in self.atom_adp_relations.values() for key in params.keys()):
                        self.atom_adp_order = params
                        cif_dict["adp"] = buffer
                        continue
                    # Extracting bond distances
                    elif any(key in self.bond_distance_relations.values() for key in params.keys()):
                        self.bond_distance_order = params
                        cif_dict["bonds"] = buffer
                        continue
                    # Extracting interatomic angles
                    elif any(key in self.angle_relations.values() for key in params.keys()):
                        self.angle_order = params
                        cif_dict["angles"] = buffer
                        continue
                    # Extract torsions
                    elif any(key in self.torsion_relations.values() for key in params.keys()):
                        self.torsion_order = params
                        cif_dict["torsions"] = buffer
                        continue

                # Extracting normal command-value pairs
                if not line.split():
                    continue
                # If parameter is not in the aoi
                if not line.split()[0] in (list(self.data_columns.keys()) + list(self.ub_dict.keys())):
                    continue
                # 1st case: Single line comment + value
                if line.startswith("_") and len(line.split()) > 1:
                    buffer = line
                # 2nd case: Single line value
                elif line.startswith("_") and len(line.split()) == 1:
                    buffer = line
                    buffer += cif_file.readline()
                    if buffer.endswith("'\n"):
                        continue
                    # 3rd case: Multiple lines value
                    elif buffer.endswith(";\n"):
                        while True:
                            buffer += cif_file.readline()
                            if buffer.endswith(";\n"):
                                break
                # Reformat software name
                if buffer.split()[0].startswith("_audit_creation_method"):
                    cif_dict[buffer.split()[0]] = self.reformat_software(buffer)
                else:
                    cif_dict[buffer.split()[0]] = "".join(buffer.split()[1:])
        return cif_dict

    def default_cif_df(self):
        data_columns = list(dict.fromkeys(list(self.data_columns.values())))
        error_columns = list(dict.fromkeys(list(self.error_columns.values())))
        excel_cols = data_columns + error_columns
        default_df = pd.DataFrame(columns=excel_cols)
        default_df.loc["Path"] = ""
        default_df = default_df.set_index("Path")
        for i in range(default_df.values.shape[1]):
            default_df.loc[""].values[i] = self.blank
        return default_df

    def default_ud_df(self):
        if self.ud_bonds:
            cols = ["P / T"]
            for pair in self.ud_bonds:
                col_name = "-".join(pair)
                cols.append(col_name)
                cols.append(self.delta + "(" + col_name + ")")
            self.bonds_df = pd.DataFrame(columns=cols)
            self.bonds_df.index.name = "Filename"

        if self.ud_angles:
            cols = ["P / T"]
            for triple in self.ud_angles:
                col_name = "-".join(triple)
                cols.append("-".join(triple))
                cols.append(self.delta + "(" + col_name + ")")
            self.angles_df = pd.DataFrame(columns=cols)
            self.angles_df.index.name = "Filename"

        if self.ud_torsions:
            cols = ["P / T"]
            for quad in self.ud_torsions:
                col_name = "-".join(quad)
                cols.append("-".join(quad))
                cols.append(self.delta + "(" + col_name + ")")
            self.torsions_df = pd.DataFrame(columns=cols)
            self.torsions_df.index.name = "Filename"

    def cif_to_pandas(self, path, settings):
        cif_dict = self.get_all_parameters(path)
        cif_df = self.default_cif_df()
        cif_df.rename(index={"": path}, inplace=True)
        cif_df["Filename"] = [os.path.basename(path)]
        ub_matrix = "um s "
        # Extract base parameters from cif

        for command, value in cif_dict.items():
            # Extract UB matrix
            if command.startswith("_diffrn_orient_matrix_UB"):
                ub_matrix += " " + value
                continue
            # Handle atomic coordinates and ADPs
            elif command.startswith("atomic_coordinates"):
                self.handle_atomic_coordinates(value, path)
            elif command.startswith("adp"):
                self.handle_adp(value, path)
            # Handle bond_distances
            elif command.startswith("bonds"):
                self.handle_distances(value, path)
            # Handle angles
            elif command.startswith("angles"):
                self.handle_angles(value, path)
            # Handle torsions
            elif command.startswith("torsions"):
                self.handle_torsions(value, path)
                pass
            # Handle standardized values
            else:
                cif_df.loc[path, self.data_columns[command]] = self.format_value(value)
        # Split values with errors
        if settings.split_errors:
            self.handle_errors(cif_df)
        if ub_matrix != "um s ":
            cif_df["UM"] = ub_matrix
        return cif_df

    @staticmethod
    def format_value(value):
        if type(value) == str and (value.startswith("'") or value.startswith(";")):
            return value[1:-1]
        else:
            return value

    def handle_errors(self, cif_df):
        for val, err in self.error_columns.items():
            cif_df[val], cif_df[err] = self.error_from_brackets(cif_df[val].iloc[0])
        return cif_df

    def handle_atomic_coordinates(self, coord_buffer, fname):
        counter = 0
        for line in coord_buffer.split("\t"):
            values = line.split()
            if not values:
                continue
            else:
                for key, value in self.atom_site_relations.items():
                    if key == "Filename" and counter == 0:
                        self.atom_coord_df.loc["_".join([fname, values[0]]), "Filename"] = fname
                    elif key == "Filename" and counter > 0:
                        self.atom_coord_df.loc["_".join([fname, values[0]]), "Filename"] = self.blank
                    else:
                        self.atom_coord_df.loc["_".join([fname, values[0]]), key] = values[self.atom_site_order[value]]
            counter += 1

    def handle_adp(self, adp_buffer, fname):
        for line in adp_buffer.split("\t"):
            values = line.split()
            if "?" in values:
                break
            if not values:
                continue
            else:
                values = line.split()
                for key, value in self.atom_adp_relations.items():
                    self.atom_coord_df.loc["_".join([fname, values[0]]), key] = values[self.atom_adp_order[value]]

    def handle_distances(self, dist_buffer, fname):
        if not self.ud_bonds:
            return None

        for line in dist_buffer.split("\t"):
            values = line.split()
            if not values:
                continue
            else:
                values = line.split()
                atom_lbl_1 = values[self.bond_distance_order['_geom_bond_atom_site_label_1']]
                atom_lbl_2 = values[self.bond_distance_order['_geom_bond_atom_site_label_2']]
                dist = values[self.bond_distance_order["_geom_bond_distance"]]

                for ud_bond in self.ud_bonds:
                    if set(ud_bond) == {atom_lbl_1, atom_lbl_2}:
                        col_name = "-".join(ud_bond)
                        err_col_name = self.delta + "(" + col_name + ")"
                        self.bonds_df.loc[fname, [col_name, err_col_name]] = self.error_from_brackets(dist)

    def handle_angles(self, angles_buffer, fname):
        if not self.ud_angles:
            return None

        for line in angles_buffer.split("\t"):
            values = line.split()
            if not values:
                continue
            else:
                values = line.split()
                atom_lbl_0 = values[self.angle_order['_geom_angle_atom_site_label_1']]
                atom_lbl_1 = values[self.angle_order['_geom_angle_atom_site_label_2']]
                atom_lbl_2 = values[self.angle_order['_geom_angle_atom_site_label_3']]
                angle = values[self.angle_order["_geom_angle"]]
                for ud_angle in self.ud_angles:
                    if (ud_angle[1] == atom_lbl_1) and {atom_lbl_0, atom_lbl_2} == {ud_angle[0], ud_angle[2]}:
                        col_name = "-".join(ud_angle)
                        err_col_name = self.delta + "(" + col_name + ")"
                        self.angles_df.loc[fname, [col_name, err_col_name]] = self.error_from_brackets(angle)

    def handle_torsions(self, torsions_buffer, fname):
        if not self.ud_torsions:
            return None

        for line in torsions_buffer.split("\t"):
            values = line.split()
            if not values:
                continue
            else:
                values = line.split()
                atom_lbl_0 = values[self.torsion_order['_geom_torsion_atom_site_label_1']]
                atom_lbl_1 = values[self.torsion_order['_geom_torsion_atom_site_label_2']]
                atom_lbl_2 = values[self.torsion_order['_geom_torsion_atom_site_label_3']]
                atom_lbl_3 = values[self.torsion_order['_geom_torsion_atom_site_label_4']]
                torsion = values[self.torsion_order["_geom_torsion"]]
                torsion_name = [atom_lbl_0, atom_lbl_1, atom_lbl_2, atom_lbl_3]
                for ud_torsion in self.ud_torsions:
                    if ud_torsion == torsion_name or ud_torsion == torsion_name[::-1]:
                        col_name = "-".join(ud_torsion)
                        err_col_name = self.delta + "(" + col_name + ")"
                        self.torsions_df.loc[fname, [col_name, err_col_name]] = self.error_from_brackets(torsion)

    def error_from_brackets(self, value):
        if "(" in value:
            val = Decimal(value.split("(")[0])
            err = Decimal(value.split("(")[1][:-1])
            magnitude = Decimal(val).as_tuple().exponent
            err = err * Decimal(np.power(10., magnitude))
            err = np.round(float(err), np.abs(magnitude))
            return float(val), err
        else:
            return float(value), self.blank

    @staticmethod
    def find_all_cifs(path, exceptions="", requests=""):
        list_of_cifs = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if (file.endswith(".cif") and not
                    any(exception.lower() in os.path.join(root, file).lower() for exception in exceptions) and
                        all(request.lower() in os.path.join(root, file).lower() for request in requests)):
                    list_of_cifs.append(os.path.join(root, file))
        return list_of_cifs

    def create_static_logbook(self, settings, echo):
        logbook = pd.DataFrame()
        list_of_cifs = self.find_all_cifs(settings.path, settings.exceptions, settings.requests)
        failed_cifs = []
        echo.append_log_message("SUCCESSFULLY CONVERTED:")
        for cif in list_of_cifs:
            try:
                cif_df = self.cif_to_pandas(cif, settings)
            except:
                failed_cifs.append(cif)
                continue
            if set(settings.chemistry) and set(settings.chemistry) != set(self.list_atoms(cif_df["Formula"][0])):
                continue
            if settings.skip_crys and "CrysAlisPro" in cif_df["Program"][0]:
                continue
            else:
                logbook = pd.concat((logbook, cif_df))
                echo.append_log_message(cif)

        if failed_cifs:
            echo.append_log_message("Conversion failed for the following cif files:", err=True)
            [echo.append_log_message(cif, err=True) for cif in failed_cifs]

        return logbook

    def save_static_logbook(self, logbook, file_to_save, split_errors=True):
        with pd.ExcelWriter(file_to_save + ".xlsx") as writer:
            # General info
            logbook.to_excel(writer, sheet_name="CIFs")
            # Integrations
            SumManager.default_sum_df().to_excel(writer, sheet_name="Integrations")
            # Atomic Coordinates
            self.atom_coord_df.fillna(self.blank, inplace=True)
            self.atom_coord_df.to_excel(writer, sheet_name="Atomic_Coordinates", index=False)
            # Bonds
            self.bonds_df.to_excel(writer, sheet_name="Bonds")
            # Angles
            self.angles_df.to_excel(writer, sheet_name="Angles")
            # Torsions
            self.torsions_df.to_excel(writer, sheet_name="Torsions")
            # EOS
            if split_errors:
                self.generate_eos_df(logbook).to_excel(writer, sheet_name="EOS")
        return file_to_save + ".xlsx"

    @staticmethod
    def list_atoms(chem_formula):
        # remove numbers from formula
        nonumbers = "".join([symb for symb in chem_formula.lower() if not symb.isdigit()])
        # remove punctuations
        nopunct = "".join([symb for symb in nonumbers if not (symb in string.punctuation)])
        # Return list of atoms
        return nopunct.split()

    @staticmethod
    def reformat_software(software):
        if "Olex" in software:
            return "Olex"
        elif "Jana" in software:
            return "Jana"
        elif "CrysAlisPro" in software:
            return "CrysAlisPro"
        else:
            return "".join([symb for symb in software if not (symb in string.punctuation)]).split()[0]

    def generate_eos_df(self, all_cif_df):
        eosfit_logbook_relation = {"V(" + u"\u212B^3)": "V",
                                   "\u0394V" + "(\u212B^3)": "SIGV",
                                   "a(\u212B)": "A",
                                   "\u0394a(\u212B)": "SIGA",
                                   "b(\u212B)": "B",
                                   "\u0394b(\u212B)": "SIGB",
                                   "c(\u212B)": "C",
                                   "\u0394c(\u212B)": "SIGC",
                                   "\u03B1(\u00b0)": "ALPHA",
                                   "\u0394\u03B1(\u00b0)": "SIGAL",
                                   "\u03B2(\u00b0)": "BETA",
                                   "\u0394\u03B2(\u00b0)": "SIGBE",
                                   "\u03B3(\u00b0)": "GAMMA",
                                   "\u0394\u03B3(\u00b0)": "SIGGA"
                                   }
        eos_df = all_cif_df[eosfit_logbook_relation.keys()]
        eos_df = eos_df.rename(mapper=eosfit_logbook_relation, axis="columns")
        eos_df.insert(loc=0, column="P", value=np.full(shape=eos_df.shape[0], fill_value=0))
        eos_df.insert(loc=1, column="SIGP", value=np.full(shape=eos_df.shape[0], fill_value=0))
        eos_df.insert(loc=2, column="T", value=np.full(shape=eos_df.shape[0], fill_value=293))
        eos_df.insert(loc=3, column="SIGT", value=np.full(shape=eos_df.shape[0], fill_value=0))
        eos_df.replace(to_replace=self.blank, value=0, inplace=True)
        return eos_df


def main():
    test_file = "D:\\Python_Projects\\LogBooker1.9\\test_data\\bags\\vida_c_p14.cif"
    # manager = CifManager()
    # manager.cif_to_pandas(test_file)
    # manager.get_all_parameters(test_file)
    # manager.get_all_parameters(test_file)


if __name__ == "__main__":
    main()
