import pandas as pd
import os
import string


class SumManager:
    def __init__(self, path):
        self.path = path
        self.sum_df = self.default_sum_df()
        self.filter_methods = [self.__getattribute__(method) for method in self.__dir__() if method.startswith("get_")]

    def sum_to_pandas(self, path_to_sum_file):
        self.path = path_to_sum_file
        self.sum_df["Path"] = [self.path]
        with open(path_to_sum_file, "r") as sum_file:
            line = True
            while line:
                line = sum_file.readline()
                args = [line, sum_file]
                any(method(*args) for method in self.filter_methods)
        return self.sum_df

    def get_hp_cone(self, *args):
        line = args[0]
        attr = "HP cone rejection active"
        if attr in line:
            value = line.split(attr)[-1]
            self.sum_df["HP opening"] = [self.punctuation_filter(value).split()[-1]]

    def get_mask_size(self, *args):
        line = args[0]
        attr = "Override integration mask size:"
        if attr in line:
            value = line.split(attr)[-1]
            self.sum_df["Mask size"] = [self.punctuation_filter(value).split()[-1]]

    def get_bcg_param(self, *args):
        line = args[0]
        attr = "General average background pars:"
        if attr in line:
            value = line.split(attr)[-1]
            Re, Fr = self.punctuation_filter(value).split()
            self.sum_df["Bcg_Re"] = ["".join(symb for symb in Re if symb.isdigit())]
            self.sum_df["Bcg_Fr"] = ["".join(symb for symb in Fr if symb.isdigit())]

    def get_smart_bcg(self, *args):
        line = args[0]
        attr = "Smart background:"
        if attr in line:
            value = line.split(attr)[-1]
            self.sum_df["Smart_range"] = [self.punctuation_filter(value).split()[2]]

    def get_bad_refl(self, *args):
        line = args[0]
        attr = "Reject reflections with bad profiles"
        if attr in line:
            self.sum_df["Reject_bad"] = line.split(":")[-1].split()

    def get_frame_limits(self, *args):
        line = args[0]
        attr = "Min/max for:"
        if attr in line:
            value = line.split(attr)[-1].split()[1].split(":")[-1].split("/")
            self.sum_df["First"] = [value[0]]
            self.sum_df["Last"] = [value[1]]

    def get_outlier(self, *args):
        line = args[0]
        attr = "Laue symmetry par settings:"
        if attr in line:
            value = line.split(attr)[-1]
            self.sum_df["Outlier"] = " ".join(value.split()[:-1])

    def get_sg(self, *args):
        line = args[0]
        attr = "TITL"
        if attr in line:
            value = line.split(attr)[-1]
            self.sum_df["Final SG"] = ["".join(value.split()[-1])]

    def get_resolution_limit(self, *args):
        line = args[0]
        reader = args[1]
        attr = "Statistics vs resolution (taking redundancy into account)"
        table_sep = "---------"
        if attr in line:
            table_counter = 0
            while line:
                line = reader.readline()
                if table_sep in line:
                    table_counter += 1
                if table_counter == 2:
                    break

            # Output at high resolution limit:
            int_high_rl = reader.readline().split()
            self.sum_df["RL_high"] = [int_high_rl[0]]
            self.sum_df["Rint_high"] = [int_high_rl[8]]
            self.sum_df["F2/sig(F2)_high"] = [int_high_rl[7]]

            # Output at low resolution limit:
            int_low_rl = reader.readline().split()
            self.sum_df["RL_low"] = [int_low_rl[0]]
            self.sum_df["Rint_low"] = [int_low_rl[8]]
            self.sum_df["F2/sig(F2)_low"] = [int_low_rl[7]]

    def get_date_time(self, *args):
        attr = "Data reduction ended at"
        line = args[0]
        if attr in line:
            value = line.split(attr)[-1]
            self.sum_df.rename(index={"": " ".join(value.split())}, inplace=True)
            self.sum_df["Filename"] = [os.path.basename(self.path)]

    @staticmethod
    def default_sum_df():
        columns = ["Date", "Filename", "First", "Last", "HP opening", "Reject_bad", "Mask size",
                   "Bcg_Re", "Bcg_Fr", "Smart_range", "Outlier", "Final SG",
                   "RL_high", "Rint_high", "F2/sig(F2)_high",
                   "RL_low", "Rint_low", "F2/sig(F2)_low", "Path"]

        sum_df = pd.DataFrame(columns=columns)
        sum_df.loc["Date"] = ""
        sum_df["Mask size"] = ["1"]
        sum_df = sum_df.set_index("Date")
        return sum_df

    @staticmethod
    def punctuation_filter(value):
        to_filter = string.punctuation.replace(".", "")
        new_val = "".join(symb for symb in value if symb not in to_filter)
        return new_val

    @staticmethod
    def is_finished(filepath):
        end_key = "Data reduction ended"
        lines = open(filepath).readlines()
        counter = 0
        for line in lines[::-1]:
            if end_key in line:
                return True
            elif counter > 5:
                return False
            counter += 1


def main():
    sum_manager = SumManager("D:\\Python_Projects\\LogBooker1.9\\test_data\\enst\\enst_dom1_red.sum")
    # sum_df = sum_manager.sum_to_pandas(sum_manager.path)
    # sum_df.to_excel("test.xlsx")
    # print(sum_manager.is_finished("F:\Mg2CO4\Data\Single_Crystal\TF069\TF069_p02_s8\TF069_p02_s8_scan1\g3_dom1_mP_red.sum"))


if __name__ == "__main__":
    main()
