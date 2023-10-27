from plotly.subplots import make_subplots
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import xlwings as xw
import os
from exceler import xl_shape
import numpy as np


class Plotter:
    def __init__(self):
        self.path_to_save = ""
        self.save_each = False
        self.xl_sheet = "Bonds"
        self.max_cols = 4
        self.max_rows = 1
        self.h_space = 0.08
        self.v_space = 0.08
        self.height_px = 400
        self.width_px = 2500
        self.marker_color = 'rgb(80,80,80)'
        self.marker_size = 12
        self.title_font_size = 25
        self.font_family = "Arial"
        self.bcg = True
        self.frame = True
        self.grid = True
        self.bcg_color = 'rgba(0,0,0,0)'
        self.x_title = "Pressure, GPa"
        self.y_title = ""

    def get_data_from_exel(self, xl_file, sheet):
        height, width = xl_shape(xl_file, sheet=sheet)
        data = xw.Book(xl_file).sheets[sheet][0:height, 0:width].value
        if data is None:
            return data
        df = pd.DataFrame(data=data[1:], columns=data[0])
        df.set_index("Filename", inplace=True)
        self.xl_sheet = sheet
        return df

    def update_fig_layout(self, fig, height, width, title, font_size):
        # Update axis titles
        if title == "Bonds":
            self.y_title = "Bond length, \u212B"
        elif title == "Angles":
            self.y_title = "Bonds angle, deg(\u00b0)"
        elif title == "Torsions":
            self.y_title = "Torsion angle, deg(\u00b0)"

        # Update background color
        if self.bcg:
            self.bcg_color = "rgb(239,246,255)"
        else:
            self.bcg_color = 'rgba(0,0,0,0)'

        fig.update_annotations(font_size=20)
        fig.update_layout(title=title, font=dict(size=font_size, family="Arial"),
                          height=height, width=width, plot_bgcolor=self.bcg_color,
                          )
        # Update axes
        fig.update_xaxes(title_text=self.x_title, title_standoff=0,
                         title_font={"size": self.title_font_size, "family": self.font_family},
                         showline=True, linewidth=2, linecolor='black', zeroline=False, mirror=self.frame,
                         nticks=10, ticks="inside", tickwidth=2, ticklen=6,
                         tickfont=dict(family=self.font_family, size=20, color='black'), tickformat=".2f",
                         showgrid=self.grid, gridwidth=2, gridcolor='lightgrey', griddash='dot',
                         rangeslider=dict(visible=False)
                         )

        fig.update_yaxes(title_text=self.y_title,
                         title_font={"size": self.title_font_size, "family": self.font_family},
                         title_standoff=5,
                         showline=True, linewidth=2, linecolor='black', zeroline=False, mirror=self.frame,
                         nticks=10, ticks="inside", tickwidth=2, ticklen=6,
                         tickfont=dict(family=self.font_family, size=20, color='black'), tickformat=".3f",
                         showgrid=self.grid, gridwidth=2, gridcolor='lightgrey', griddash="dot"
                         )

    def multiple_plot(self, xl_file, sheet, frame=True, grid=True, bcg=True, path=""):
        # Check plotting options
        self.frame = frame
        self.grid = grid
        self.bcg = bcg
        self.path_to_save = path

        # Extract data
        data = self.get_data_from_exel(xl_file, sheet)
        if data is None:
            return "Spreadsheet " + sheet + " is empty"
        if data["P / T"].isnull().all():
            return "The condition (P/T) column is not filled"
        if any(data[col].isnull().all() for col in data.columns):
            return "There are missing columns in " + sheet + " table"

        # Calculate optimal plots framework
        n_plots = int(0.5 * (data.shape[1] - 1))
        self.max_rows = int(np.ceil(n_plots / self.max_cols))

        vertical_spacing_adaptive = 120 / (self.height_px * self.max_rows)
        # Create figure framework
        fig = make_subplots(rows=self.max_rows, cols=self.max_cols, subplot_titles=data.columns[1::2],
                            horizontal_spacing=self.h_space, vertical_spacing=vertical_spacing_adaptive)

        # Update figure layout
        self.update_fig_layout(fig, title=self.xl_sheet, font_size=30,
                               height=self.height_px * self.max_rows, width=self.width_px)

        # Plotting
        x = data["P / T"].values  # Always the same over the dataset
        for i in range(self.max_rows):
            for k in range(self.max_cols):
                n = i * self.max_cols + k
                if n > n_plots - 1:
                    break
                y = data.iloc[:, 2 * n + 1].values
                err_y = data.iloc[:, 2 * n + 2].values
                graph = go.Scatter(x=x, y=abs(y),
                                   mode="markers", marker=dict(color=self.marker_color, size=self.marker_size),
                                   error_y=dict(type='data', array=err_y, visible=True),
                                   name=data.columns[2 * n + 1])
                fig.add_trace(graph, row=i + 1, col=k + 1)

                if self.path_to_save:
                    full_name = os.path.join(self.path_to_save, self.xl_sheet+"-"+(data.columns[2 * n + 1]) + ".png")
                    single_plot = go.Figure()
                    single_plot.add_trace(graph)
                    self.update_fig_layout(single_plot, height=600, width=800,
                                           title=data.columns[2 * n + 1], font_size=20)
                    pio.write_image(single_plot, full_name)
        fig.show()
        return "The figures were successfully plotted"


def main():
    # read dataset
    plt = Plotter()
    plt.get_data_from_exel("D:\Python_Projects\LogBooker1.9\\1.xlsx", sheet="Bonds")


if __name__ == "__main__":
    main()
