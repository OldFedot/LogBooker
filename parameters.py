import string


class Settings:
    def __init__(self):
        self.path = ""
        self.xl_file = ""
        self.exceptions = ""
        self.requests = ""
        self.chemistry = ""
        self.skip_crys = True
        self.hyper = True
        self.light = True
        self.filter = ""
        self.filter_limit = 0.05
        self.columns_to_display = []
        self.split_errors = True

    def update_attr(self, name, value):
        self.__setattr__(name, value)

    @staticmethod
    def decompose_command(command):
        return command.lower().split(sep="-")[1:]

    @staticmethod
    def decompose_ud_parameters(str_values):
        decomposed_params = []
        # default format with "-" separator
        val_list = str_values.split("\n")
        for item in val_list:
            if item == "":
                continue
            elif "-" in item:
                decomposed_params.append(item.replace(" ", "").split("-"))
            else:
                atom_list = item.split(" ")
                atom_list = [atom for atom in atom_list if atom != ""]
                decomposed_params.append(atom_list)
        return decomposed_params


def main():
    s = Settings()


if __name__ == "__main__":
    main()
