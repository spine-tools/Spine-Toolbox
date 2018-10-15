######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Widget to show Network Map Form.

:author: M. Marin (KTH), J. Olauson (KTH)
:date:   7.9.2018
"""

import os
from ui.network_map_form import Ui_Form
from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt
import numpy as np
from numpy import flatnonzero as find
from numpy import atleast_1d as arr
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import collections as mcoll
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import minimize


class NetworkMapForm(QWidget):
    """A widget to show network map.

    Attributes:
        view (View): View DataStore instance that owns this form
    """

    def __init__(self, toolbox, view, mapping, settings_path=""):
        """Initialize class."""
        super().__init__(parent=toolbox, f=Qt.Window)  # Setting the parent inherits the stylesheet
        self._view = view
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.network_map = NetworkMap(mapping, settings_path)
        # self.button = QPushButton('Plot')
        # self.button.clicked.connect(self.plot)
        self.ui.horizontalLayout_network_map_placeholder.addWidget(self.network_map.qt_canvas)

    def plot(self):
        self.network_map.make_map()


class NetworkMap:
    """Class for making network plots, see documentation and methods for more info."""

    def __init__(self, mapping, settings_path=""):
        """ Initialize class."""
        self.mapping = mapping
        # Class attributes
        self.settings = None
        self.unique_conns = None
        self.parallel_ind = None
        self.parallel = None
        self.sets_variable = None
        self.sets_variable_lim = None
        self.node_set = None
        self.node_color = None
        self.node_name_color = None
        self.node_length = None
        self.node_lw = None
        self.node_name_fs = None
        self.conn_set = None
        self.conn_lw = None
        self.conn_color = None
        self.arrow_scaling = None
        self.interactive = None
        self.picker_node = None
        self.picker_conn = None
        self.significant_figures = None
        self.info_fc = None
        self.info_ec = None
        self.info_lw = None
        self.equal_aspect = None
        self.x = None
        self.y = None
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None
        self.extent = None
        self.x_range = None
        self.y_range = None
        self.sub_borders = None
        self.x_grid_points = None
        self.y_grid_points = None
        self.conn_colored = None
        self.conn_widthed = None
        self.heatmap = None
        self.fig = None
        self.qt_canvas = None
        self.ax = None
        self.segments_index = None
        self.segments = None
        self.segments_object = None
        self.node_text = None
        self.node_text_index = None
        self.mpl_id = None
        self.mult_event = None
        self.mode = None
        self.event_id = None
        self.node_cng = None
        self.old_pos = None
        self.new_pos = None
        self.interactive_info_display = None
        self.hm = None
        self.arrows_drawn = False
        self.heatmap_drawn = False
        self.annot = None
        self.node_name_list = None
        self.N = None
        self.node = None
        self.node_status = None
        self.node_info = None
        self.node_parameter_dict = None
        self.node_info_param = None
        self.from_node_index_arr = None
        self.to_node_index_arr = None
        self.conn_name_list = None
        self.conn_status = None
        self.conn_info = None
        self.conn_parameter_dict = None
        self.conn_info_param = None
        self.node_parameter_keys = None
        self.conn_parameter_keys = None
        self.init_settings(settings_path)
        self.init_network_data()
        self.make_map()

    # noinspection PyMethodMayBeStatic
    def text_angle(self, x1, y1, x2, y2):
        """Calculate angle of text based on two points
        Betweeen -90 and 90 degrees, also returns dx and dy for displacement. """
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0:
            ang = np.sign(dy)*np.pi/2
        else:
            ang = np.arctan(dy/dx)
        sy = 1 if np.sign(dy) == 0 else np.sign(dy)
        return np.rad2deg(ang), -np.sign(dx)/sy*abs(np.sin(ang)), abs(np.cos(ang))

    # noinspection PyMethodMayBeStatic
    def mult_ind(self, a, b, miss=np.nan):
        """Get indices for elements of a in b, returns numpy array.
        E.g. mult_ind([1, 2, 1, 4], [3, 2, 1]) -> array([2., 1., 2., nan]) """
        bind = {}
        for i, elt in enumerate(b):
            if elt not in bind:
                bind[elt] = i
        return arr([bind.get(itm, miss) for itm in a])

    # noinspection PyMethodMayBeStatic
    def str_sig(self, number, sign_figs):
        """Returns number as string with specified significant figures.
        Special treatment of bool, str, nan and complex. """
        if type(number) == np.bool_ and number is True:
            return 'True'
        if type(number) == np.bool_ and number is False:
            return 'False'
        if type(number) is str:
            return number
        if np.isnan(number):
            return 'nan'
        if np.iscomplex(number):
            real = str_sig(np.real(number),sign_figs)
            imag = str_sig(np.imag(number),sign_figs)
            if imag[0] == '-':
                return real + ' - j' + imag[1:]
            else:
                return real + ' + j' + imag
        a = float("{1:.{0}e}".format(sign_figs-1, number))
        if abs(a) < 10**(sign_figs-1):
            if a == 0:
                return '0'
            else:
                return str(a)
        else:
            return str(int(a))

    # noinspection PyMethodMayBeStatic
    def parallel_coupling(self, x):
        """Parallel coupling of elements in x. """
        x = arr(x)  # make sure we have a numpy array
        if sum(x == 0) > 0:
            return 0
        else:
            return sum(1/x) ** -1

    # noinspection PyMethodMayBeStatic
    def lambda_vector(self, fun):
        """Vector functions, eg min([1,2,4]) = 1 """
        if fun == 'min':
            return min
        elif fun == 'max':
            return max
        elif fun == 'parallel coupling':
            def parallel_coupling(x):
                if sum(x == 0) > 0:
                    return 0
                else:
                    return sum(1/x) ** -1
            return parallel_coupling
        elif fun == 'mean':
            return np.mean
        elif fun == 'sum':
            return np.sum

    # noinspection PyMethodMayBeStatic
    def lambda_pairwise(self, fun):
        """Pairwise functions, eg min([1,2,4],[4,3,1]) = [1,2,1] """
        if fun == 'min':
            return np.minimum
        elif fun == 'max':
            return np.maximum
        elif fun == 'mean':
            def mean_el(a, b):
                return np.average(np.column_stack((a, b)), axis=1)
            return mean_el
        elif fun == 'sum':
            def sum_el(a, b):
                return np.sum(np.column_stack((a, b)), axis=1)
            return sum_el

    def init_network_data(self):
        """Initialize node and conn data to plot, by querying mapping."""
        conn_node_node_relationship_class = self.mapping.single_wide_relationship_class(
            name='connection__node__node').one_or_none()
        if not conn_node_node_relationship_class:
            return
        # Iterate connection__node__node to get the names
        node_name_set = set()
        self.conn_name_list = list()
        for relationship in self.mapping.wide_relationship_list(class_id=conn_node_node_relationship_class.id):
            conn_name, from_node_name, to_node_name = relationship.object_name_list.split(',')
            self.conn_name_list.append(conn_name)
            node_name_set.add(from_node_name)
            node_name_set.add(to_node_name)
        self.node_name_list = list(node_name_set)
        self.N = len(self.node_name_list)
        self.node = np.arange(self.N)
        # Node info and status
        self.node_info = arr(['']*len(self.node_name_list))
        self.node_status = np.ones(len(self.node_name_list), int)
        self.node_info_param = self.settings['node_info_parameter']
        # Node parameters
        self.node_parameter_dict = {}
        node_object_class = self.mapping.single_object_class(name='node').one_or_none()
        if not node_object_class:
            return
        self.node_parameter_dict = {}
        node_parameter_list = self.mapping.parameter_list(object_class_id=node_object_class.id)
        for parameter in node_parameter_list:
            node_parameter_value_list = list()
            for node_name in self.node_name_list:
                node = self.mapping.single_object(name=node_name).one_or_none()
                parameter_value = self.mapping.single_object_parameter_value(
                        parameter_id=parameter.id, object_id=node.id).one_or_none()
                node_parameter_value_list.append(parameter_value.value)
            self.node_parameter_dict[parameter.name] = arr(node_parameter_value_list)
        self.node_parameter_keys = sorted(list(self.node_parameter_dict.keys()))
        # Connection info and status
        self.conn_info = arr(['']*len(self.conn_name_list))
        self.conn_status = np.ones(len(self.conn_name_list), int)
        self.conn_info_param = self.settings['conn_info_parameter']
        # Connection parameters
        conn_object_class = self.mapping.single_object_class(name='connection').one_or_none()
        if not conn_object_class:
            return
        self.conn_parameter_dict = {}
        conn_parameter_list = self.mapping.parameter_list(object_class_id=conn_object_class.id)
        for parameter in conn_parameter_list:
            conn_parameter_value_list = list()
            for conn_name in self.conn_name_list:
                conn = self.mapping.single_object(name=conn_name).one_or_none()
                parameter_value = self.mapping.single_object_parameter_value(
                        parameter_id=parameter.id, object_id=conn.id).one_or_none()
                conn_parameter_value_list.append(parameter_value.value)
            self.conn_parameter_dict[parameter.name] = arr(conn_parameter_value_list)
        self.conn_parameter_keys = sorted(list(self.conn_parameter_dict.keys()))
        # From node, to node
        from_node_index_list = list()
        to_node_index_list = list()
        for relationship in self.mapping.wide_relationship_list(class_id=conn_node_node_relationship_class.id):
            conn_name, from_node_name, to_node_name = relationship.object_name_list.split(',')
            try:
                index = self.node_name_list.index(from_node_name)
            except ValueError:
                index = np.nan
            from_node_index_list.append(index)
            try:
                index = self.node_name_list.index(to_node_name)
            except ValueError:
                index = np.nan
            to_node_index_list.append(index)
        self.from_node_index_arr = arr(from_node_index_list)
        self.to_node_index_arr = arr(to_node_index_list)

        # def mult_data(self, a, b, c, miss=np.nan):
        #    """Get values (c) for elements of a in b, returns numpy array. """
        #    bind = {}
        #    for i, elt in enumerate(b):
        #        if elt not in bind:
        #            bind[elt] = c[i]
        #    return arr([bind.get(itm, miss) for itm in a])
        # unit_id = object_id[object_class_id==unit_class_id].astype(int)
        # unit_name = object_name[object_class_id==unit_class_id]
        # # node info (connected units)
        # node_info = np.zeros(len(node_name),dtype='<U1000')
        # relationship_class_unit_node = relationship_class_id[relationship_class_name == 'unit_node'][0]
        # if int(child_object[relationship_class_name == 'unit_node'][0]) == unit_class_id:
        #    unit_col = relationship_head.index('child_object_id')
        #    node_col = relationship_head.index('parent_object_id')
        # else:
        #    node_col = relationship_head.index('child_object_id')
        #    unit_col = relationship_head.index('parent_object_id')
        # unit_info = mult_data(relationship_data[relationship_id==relationship_class_unit_node,unit_col].astype(int),
        #   unit_id,unit_name)
        # unit_node_ind = mult_data(relationship_data[relationship_id==relationship_class_unit_node,node_col]
        #   .astype(int),node_id, np.arange(len(node_id)))
        # for i,n in zip(unit_info,unit_node_ind):
        #    if node_info[n] == '':
        #        node_info[n] += '\n\nUnits:'
        #    node_info[n] += '\n' + i

    def init_settings(self, path=""):
        """Initialize settings, either from path or default ones."""
        if os.path.exists(path):
            settings = np.load(path)
            self.settings = settings.item()
        else:
            self.settings = self.default_settings()

    # noinspection PyMethodMayBeStatic
    def default_settings(self):
        """Return default settings."""
        # FIXME: somehow the 200 limit here need to be set by user, or configuration
        large = False  # for now # len(self.node_name_list) >= 200 # large network -> somewhat different settings
        settings = dict()
        settings['node_info_parameter'] = []  # parameters to be displayed in interactive mode
        settings['conn_info_parameter'] = []  # For now # self.conn_parameter_keys.copy()
        settings['current_tab'] = 0  # tab shown in settings window
        settings['xy_params'] = None  # parameters that directly gives coordinates
        settings['xy_type'] = 1  # 1,2,3 for new layout, from parameters and previous
        settings['set_var'] = None  # parameter used for making different sets with different plot design
        settings['set_var_func'] = 'min'  # conn sets depend on set_var_func(set_var_to_node, set_var_from_node)
        settings['set_var_lim'] = []  # break points for sets
        settings['node_length'] = [0, 0, 0, 0] if large else [4, 3, 0, 0]
        settings['node_name_fs'] = [0, 0, 0, 0] if large else [13, 11, 8, 8]
        settings['node_lw'] = [2, 1, 1, 1] if large else [3, 2, 2, 1]
        settings['node_color'] = ['r', 'g', 'k', 'y']
        settings['node_name_color'] = ['k']*4
        settings['conn_lw'] = [1, 1, 1, 1]
        settings['conn_color'] = ['k']*4
        settings['equal_aspect'] = False
        settings['add_legend'] = True
        settings['arrow_scaling'] = 1
        settings['interactive'] = True
        settings['picker_node'] = 7
        settings['picker_conn'] = 3
        settings['significant_figures'] = 3
        settings['info_ec'] = 'k'
        settings['info_fc'] = [213/255, 230/255, 255/255]
        settings['info_lw'] = 1
        settings['node_var'] = None  # layout; d = node_func(node_var)^node_exp * conn_func(conn_var)^conn_exp
        settings['node_func'] = 'min'
        settings['node_exp'] = 1
        settings['conn_var'] = None
        settings['conn_func'] = 'parallel coupling'
        settings['conn_exp'] = 1
        settings['largest_dim'] = 'x'
        settings['iterations'] = 10
        settings['heavy'] = None
        settings['rescale_iter'] = 100
        settings['min_d'] = 0.001
        settings['w_exp'] = -2
        settings['conn_colors_var'] = None
        settings['conn_colors_cmap'] = 'viridis'
        settings['conn_lw_var'] = None
        settings['conn_lw_w_max'] = 5
        settings['conn_lw_w_min'] = 0.1
        settings['heatmap_var'] = None
        settings['heatmap_method'] = 0
        settings['heatmap_num'] = 15
        settings['heatmap_w_exp'] = -3
        settings['heatmap_fill_hull'] = False
        settings['heatmap_clim'] = None
        settings['heatmap_cmap'] = 'jet'
        settings['heatmap_resolution'] = 1
        settings['heatmap_clim_button'] = 'auto'
        # fig_size; [w,h] in inches for limiting (auto), height in inches or [x,y,dx,dy] in pixels
        # if [w,h] is given below, this also needs to be updated in fig_size_changed() in view_settings_widget
        settings['fig_size'] = [13, 8]
        settings['arrow_var'] = None
        settings['arrow_func'] = 'sum'
        settings['file_save'] = 'test.pdf'
        settings['x_coordinate'] = None  # calculated coordinates
        settings['y_coordinate'] = None
        return settings

    def make_map(self):
        """Make map and show it."""
        self.compute_unique_conns()
        self.setup_plot()
        # layout
        if self.settings['xy_type'] == 1:
            self.calculate_layout()
        elif self.settings['xy_type'] == 2:
            self.x = self.node_parameter_dict[self.settings['xy_params'][0]]
            self.y = self.node_parameter_dict[self.settings['xy_params'][1]]
        elif self.settings['xy_type'] == 3:
            self.x = self.settings['x_coordinate']
            self.y = self.settings['y_coordinate']
        # map properties and initiate plot
        self.set_map_properties()
        self.init_plot()
        # conn colors from parameter?
        if self.settings['conn_colors_var'] is not None:
            self.set_conn_colors()
        # conn widths from parameter?
        if self.settings['conn_lw_var'] is not None:
            self.set_conn_widths()
        # add topology
        self.add_topo()
        # * arrows for conn flow?
        # if self.settings['arrow_var'] not in [None,'None']:
        #    self.add_arrows()
        # * heatmap?
        # if self.settings['heatmap_var'] not in [None,'None']:
        #    self.x_grid_points *= self.settings['heatmap_resolution']
        #    self.y_grid_points *= self.settings['heatmap_resolution']
        #    self.calculate_heatmap()
        #    if s['heatmap_clim_button'] == 'auto':
        #        self.add_heatmap(None)
        #    else:
        #        self.add_heatmap()
        # * legend
        # if self.settings['add_legend']:
        #    self.add_legend()
        # * show map and save coordinates
        self.qt_canvas = FigureCanvas(self.fig)
        self.mpl_id = [self.fig.canvas.mpl_connect('close_event', self.handle_close)]
        if self.interactive:
            self.annot = self.ax.annotate("", xy=(0, 0), xytext=(-100, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc=self.info_fc, ec=self.info_ec,
                                                    lw=self.info_lw),
                                          arrowprops=dict(arrowstyle="->"), zorder=100, fontsize=8)
            self.annot.set_visible(False)
            self.mpl_id.append(self.fig.canvas.mpl_connect('pick_event', self.display_info))
            self.mpl_id.append(self.fig.canvas.mpl_connect('key_press_event', self.keypress))
            self.mult_event = []  # keep track of multiple events (parallel conns)
            self.mode = 'info'  # information or layout editor
            self.event_id = ''  # currently displated info (annotation box)
            self.node_cng = None  # node that is to be moved
            self.old_pos = []  # previous position (to undo a move) [node_index,x,y]
            self.new_pos = []  # to redo a move
            self.interactive_info_display = 1
            # print("\nInformation mode:\nClick on nodes and conn for info\nPress 'm' to change to layout edit mode")

    def compute_unique_conns(self):
        """Compute unique conns and related info."""
        pairs = np.sort(np.column_stack((self.from_node_index_arr, self.to_node_index_arr)))
        unique_conns, ia, ib = np.unique(pairs, axis=0, return_counts=True, return_inverse=True)
        ib = find(ib > 1)
        self.unique_conns = unique_conns  # unique pairs of conns (lowest conn first)
        self.parallel_ind = ia  # index of which aggregated conn each conn belongs to
        self.parallel = {'conn'+str(t): ['conn'+str(t)] for t in range(len(pairs))}  # conn index dict
        for i in ib:
            temp = find(ia == i)
            for t in temp:
                self.parallel['conn'+str(t)] = ['conn'+str(b) for b in temp]

    def setup_plot(self):
        """Plotting settings (colors, linewidths etc.), possibly depending on (node) variable var.
        var_func is used for assigning sets to conns; var_conn = var_func(var[node1],var[node2])

        Example with var = 'V_base' (base voltages)
            breakpoints for different sets (var_lim[0] > var_lim[1] > ...)
            Eg 10 gives one set for all V_base >= 10 kV (<10 belongs to set -1; not shown)
            [220,110,0] gives three sets: [220,inf), [110,220) and [0,110)
        """
        set_var = self.settings['set_var']
        set_var_lim = self.settings['set_var_lim']
        set_var_func = self.lambda_pairwise(self.settings['set_var_func'])
        # Node settings
        self.sets_variable = set_var
        self.sets_variable_lim = list(arr(set_var_lim))
        if set_var is None or len(set_var_lim) == 0:
            self.node_set = np.zeros(self.N, int)  # all shown and same symbols
        else:
            var = self.node_parameter_dict[set_var]
            self.node_set = arr([find(v >= arr(set_var_lim))[0] if v >= set_var_lim[-1] else -1 for v in var])
        self.node_color = self.settings['node_color']
        self.node_name_color = self.settings['node_name_color']
        self.node_length = self.settings['node_length']
        self.node_lw = self.settings['node_lw']
        self.node_name_fs = self.settings['node_name_fs']
        # Connection settings
        if set_var is None or len(set_var_lim) == 0:
            self.conn_set = np.zeros(len(self.from_node_index_arr), int)  # all shown and same symbols
        else:
            var_conn = set_var_func(set_var[self.from_node_index_arr], set_var[self.to_node_index_arr])
            self.conn_set = arr([find(v >= arr(set_var_lim))[0] if v >= set_var_lim[-1] else -1 for v in var_conn])
        self.conn_lw = self.settings['conn_lw']
        self.conn_color = self.settings['conn_color']
        self.arrow_scaling = self.settings['arrow_scaling']  # size of flow arrows (1 for default)
        # Interactive plot settings
        self.interactive = self.settings['interactive']  # interactive map mode
        self.picker_node = self.settings['picker_node']  # tolerance for interactive picking
        self.picker_conn = self.settings['picker_conn']
        self.significant_figures = self.settings['significant_figures']  # when info is displayed
        self.info_fc = self.settings['info_fc']  # color for info box (SPINE)
        self.info_ec = self.settings['info_ec']  # color info-box edge
        self.info_lw = self.settings['info_lw']  # info-box edge width
        self.equal_aspect = self.settings['equal_aspect']

    def calculate_layout(self):
        """Layout of grid (node coordinates).
        See J.Olauson et al. "Creating power system network layouts: A fast algorithm suitable
        for Python and Matlab", IEEE journal, 2019
        1. Calculate distances between adjacent nodes
        2. Calculate distance matrix using dijkstra's algorithm
        3. Find coordinates with multidimensional scaling.

        Distance possibly depend on node and conn variables (set to None to exclude)
        The node variable is computed for conn (using mean, min etc.) with node_func
        The conn variable needs special care if parallel conns exist
        conn_exp,node_exp: exponents for calculating distance matrix

        For power systems d = min(V_base)^0.3 * parallel_coupling(X)^0.3 gives nice layouts

        largest_dim: 'x','y' or None, e.g. 'x' gives landscape-like format
        iterations: number of iterations in MDS
        """
        # Calculate distance matrix d
        node1, node2, conn_v, node_v = self.aggregate_conns()
        conn_exp = self.settings['conn_exp']
        node_exp = self.settings['node_exp']
        heavy = self.settings['heavy']
        iterations = self.settings['iterations']
        min_d = self.settings['min_d']
        w_exp = self.settings['w_exp']
        rescale_iter = self.settings['rescale_iter']
        largest_dim = self.settings['largest_dim']
        d = self.calculate_distance(self.node, node1, node2, conn_v, node_v, conn_exp, node_exp)
        # Calculate coordinates with multidimensional scaling (mostly default settings)
        xy = self.VSGD_MDS(d, heavy, self.node, iterations, min_d, w_exp, rescale_iter)
        # Possibly switch dimensions (default is landscape-like orientation)
        temp = np.max(xy, axis=0) - np.min(xy, axis=0)
        a = largest_dim == 'x' and temp[1] > temp[0] and heavy is None
        b = largest_dim == 'y' and temp[0] > temp[1] and heavy is None
        if a or b:
            self.x = xy[:, 1]
            self.y = xy[:, 0]
        else:
            self.x = xy[:, 0]
            self.y = xy[:, 1]

    def aggregate_conns(self):
        """Aggregate parallel conns."""
        node_func = self.lambda_pairwise(self.settings['node_func'])
        conn_func = self.lambda_vector(self.settings['conn_func'])
        node_var = self.settings['node_var']
        conn_var = self.settings['conn_var']
        if node_var is not None:
            nv1 = self.node_parameter_dict[node_var][self.from_node_index_arr]  # Node variable at from node
            nv2 = self.node_parameter_dict[node_var][self.to_node_index_arr]  # Node variable at to node
        if conn_var is not None:
            av = self.conn_parameter_dict[conn_var]
        node1, node2 = self.unique_conns[:, 0], self.unique_conns[:, 1]
        conn_v = np.ones(len(node1))  # conn variable
        node_v = np.ones(len(node1))  # node variable
        for n in range(len(node1)):
            ind = find(self.parallel_ind == n)
            if node_var is not None:
                node_v[n] = node_func(nv1[ind[0]], nv2[ind[0]])
            if conn_var is not None:
                conn_v[n] = conn_func(av[ind])
        return node1, node2, conn_v, node_v

    def calculate_distance(self, bus, bus1, bus2, X, V, e1, e2):
        """Calculate distance matrix with Dijkstra's algorithm."""
        dist = np.zeros((len(bus), len(bus)))  # branch distances
        ind1 = self.mult_ind(bus1, bus)
        ind2 = self.mult_ind(bus2, bus)
        val = np.abs(X)**e1*V**e2
        val /= min(val[val > 0])  # handle zero distances...
        val[val == 0] = 1e-6  # ...which are now 1/1e6 of smallest non-zero but not too small
        dist[ind1, ind2] = dist[ind2, ind1] = val
        d = dijkstra(dist, directed=False)  # shortest path between all bus-pairs
        d = d / np.max(d) * 100  # normalise so system diameter = 100 units
        return d

    # noinspection PyMethodMayBeStatic
    def create_sets(self, N):
        """Make sets of bus pairs (indices)."""
        sets = []
        for n in range(1, N):
            pairs = np.zeros((N - n, 2), int)  # pairs on diagonal n
            pairs[:, 0] = np.arange(N - n)
            pairs[:, 1] = pairs[:, 0] + n
            mask = np.mod(range(N - n), 2*n) < n
            s1 = pairs[mask]
            s2 = pairs[~mask]
            if len(s1) > 0:
                sets.append(s1)
            if len(s2) > 0:
                sets.append(s2)
        return sets

    # noinspection PyMethodMayBeStatic
    def heavy_data(self, heavy, bus):
        """Extract indices, coordinates and weights from dict with heavy buses."""
        h_ind = mult_ind([k for k in heavy.keys()], bus)  # indices for buses
        h_xy = np.zeros((len(heavy), 2))  # pre-defined coordinates
        h_weight = np.zeros(len(heavy))  # weight (>1 -> moves shorter, np.inf (default) -> no movement)
        for n, (k, v) in enumerate(heavy.items()):
            h_xy[n, :] = v[0:2]
            if len(v) == 3:
                h_weight[n] = v[2]
            else:
                h_weight[n] = np.inf
        return h_ind, h_xy, h_weight

    # noinspection PyMethodMayBeStatic
    def xy_rescale(self, X, d, rescale_iter):
        """Find scaling and shift in x and y compatible with predefined coordinates."""
        def OF(s):
            d2 = ((s[0]*(x1 - x2))**2 + (s[1]*(y1 - y2))**2)**0.5
            return np.sum(np.abs(d-d2))
        N = len(X)
        if N == 1:  # no rescaling possible
            scale = [1, 1]
        elif N == 2:  # same scaling in x and y
            scale = [d[0, 1] / cdist(X, X)[0, 1]] * 2
        else:  # optimise scaling in x and y
            mask = np.ones((N, N)) == 1 - np.tril(np.ones((N, N)))
            d = d[mask]  # upper triangular as vector
            ind2, ind1 = np.meshgrid(range(N), range(N))
            x1 = X[ind1[mask], 0]
            y1 = X[ind1[mask], 1]
            x2 = X[ind2[mask], 0]
            y2 = X[ind2[mask], 1]
            scale = minimize(OF, [1, 1], method='Nelder-Mead', options={'maxiter': rescale_iter}).x
        shift = np.mean(X, axis=0)  # move center of random layout to center of heavy buses
        return scale[0], scale[1], shift[0], shift[1]

    # noinspection PyMethodMayBeStatic
    def VSGD_MDS(self, d, heavy, bus, iterations, min_d, w_exp, rescale_iter):
        """Find layout with multidimensional scaling using vectorised stochastic gradient descent."""
        d[d <= np.max(d)*min_d] = np.max(d)*min_d  # not too small distances
        N = len(d)
        mask = np.ones((N, N)) == 1 - np.tril(np.ones((N, N)))  # upper triangular except diagonal
        X = np.random.rand(N, 2) * 100 - 50  # random layout with diameter 100
        # Some operations to account for predefined coordinates
        if heavy is not None:
            h_ind, h_xy, h_weight = self.heavy_data(heavy, bus)
            xs, ys, dx, dy = self.xy_rescale(h_xy, d[h_ind, :][:, h_ind], rescale_iter)  # scale and shift
            X[:, 0] += dx  # center of initial layout moved
            X[:, 1] += dy
            X[h_ind, :] = h_xy
            bw = np.ones(len(bus))  # bus weight
            bw[h_ind] = h_weight
        w = d**w_exp  # bus-pair weights (lower for distant buses)
        stepmax = 1/np.min(w[mask])
        stepmin = 1/np.max(w[mask])
        lambda1 = -np.log(stepmin/stepmax) / (iterations - 1)  # exponential decay of allowed adjustment
        sets = self.create_sets(N)  # construct sets of bus pairs
        for iteration in range(iterations):
            step = stepmax * np.exp(-lambda1*iteration)  # how big adjustments are allowed?
            rand_order = np.random.permutation(N)  # we don't want to use the same pair order each iteration
            for p in sets:
                b1, b2 = rand_order[p[:, 0]], rand_order[p[:, 1]]  # arrays of bus1 and bus2
                # current distance (possibly accounting for rescaling of system)
                if heavy is not None:
                    d2 = ((xs*(X[b1, 0] - X[b2, 0]))**2 + (ys*(X[b1, 1] - X[b2, 1]))**2)**0.5
                else:
                    d2 = ((X[b1, 0] - X[b2, 0])**2 + (X[b1, 1] - X[b2, 1])**2)**0.5
                r = (d[b1, b2] - d2)[:, None] / 2 * (X[b1] - X[b2]) / d2[:, None]  # desired change
                dx1 = r * np.minimum(1, w[b1, b2] * step)[:, None]
                dx2 = -dx1
                if heavy is not None:
                    dx1 /= bw[b1, None]  # divide change with heaviness
                    dx2 /= bw[b2, None]
                X[b1, :] += dx1  # update position
                X[b2, :] += dx2
        return X

    def set_map_properties(self):
        """Map properties such as range, depend on visible nodes."""
        # exclude nodes that are not shown
        x = self.x[self.node_set >= 0]
        y = self.y[self.node_set >= 0]
        # Default map properties
        self.x_min = min(x) - 0.05 * (max(x) - min(x))
        self.x_max = max(x) + 0.05 * (max(x) - min(x))
        self.y_min = min(y) - 0.05 * (max(y) - min(y))
        self.y_max = max(y) + 0.05 * (max(y) - min(y))
        self.extent = [self.x_min, self.x_max, self.y_min, self.y_max]
        self.x_range = self.x_max - self.x_min
        self.y_range = self.y_max - self.y_min
        self.sub_borders = [0.01, 0.99, 0.01, 0.99]  # bottom, top, left, right for subplots
        # Default heat map properties
        gp = max(self.N, 300) * 100  # ~100*N grid points in heat maps
        self.x_grid_points = (gp**0.5 * (self.x_range/self.y_range)**0.5).astype(int)
        self.y_grid_points = (gp / self.x_grid_points).astype(int)

    def set_conn_colors(self):
        """Let the color of the conns depend on variable var (e.g. 'conn_loading')."""
        conn_colors_var = self.settings['conn_colors_var']
        conn_colors_cmap = self.settings['conn_colors_cmap']
        var = self.conn_parameter_dict[conn_colors_var]
        if np.nanmax(var) > np.nanmin(var):
            var = (var - np.nanmin(var))/(np.nanmax(var) - np.nanmin(var))  # normalise 0-1
        var[np.isnan(var)] = 0
        cmap = cm.get_cmap(conn_colors_cmap)
        self.conn_colored = cmap(var)

    def set_conn_widths(self):
        """Let the width of the conns depend on absolute value of variable var (e.g. 'P1')."""
        conn_lw_var = self.settings['conn_lw_var']
        conn_lw_w_max = self.settings['conn_lw_w_max']
        conn_lw_w_min = self.settings['conn_lw_w_min']
        var = self.conn_parameter_dict[conn_lw_var]
        var = var*conn_lw_w_max/np.nanmax(var)  # normalise to conn_lw_w_max
        var[np.isnan(var)] = conn_lw_w_min
        var[var < conn_lw_w_min] = conn_lw_w_min
        self.conn_widthed = var

    def calculate_heatmap(self, var, method, num, w_exp, fill_hull):
        """Calculate heatmap for node variable 'var' using interpolation.
        method = 0: weighted on distance^w_exp (only num nearest neighbours considered)
        method = 1: LinearNDInterpolator
        method = 2: NearestNDInterpolator
        method = 3: griddata (cubic)
        fill_hull: fill outside interpolation region
        kwargs can be passed to scipy (method 1-3)
        """
        if method > 0:
            import scipy.interpolate
        else:
            from scipy.spatial import cKDTree
            num = min(self.N, num)
        var = self.node_parameter_dict[var]
        xx = np.linspace(self.x_min, self.x_max, self.x_grid_points)  # points for interpolation
        yy = np.linspace(self.y_min, self.y_max, self.y_grid_points)
        xx2, yy2 = np.meshgrid(xx, yy)
        ind = (self.node_set >= 0) & (self.node_status == 1)  # nodes displayed and in service
        xy = np.column_stack((self.x[ind], self.y[ind]))  # nnode * 2 matrix
        if method == 0:
            xy2 = np.column_stack((xx2.flatten(), yy2.flatten()))
            tree = cKDTree(xy)  # build tree
            d, ind = tree.query(xy2, np.arange(1, num+1))  # query nearest distances
            w = d**w_exp
            hm = (np.sum(w*var[ind], axis=1) / np.sum(w, axis=1)).reshape((len(yy), -1))
        elif method == 1:
            f = scipy.interpolate.LinearNDInterpolator(xy, var)
            hm = f(xx2, yy2)
        elif method == 2:
            f = scipy.interpolate.NearestNDInterpolator(xy, var)
            hm = f(xx2, yy2)
        elif method == 3:
            hm = scipy.interpolate.griddata(xy, var, (xx2, yy2), method='cubic')
        # fill outside hull (nearest neighbour)
        if fill_hull and np.sum(np.isnan(hm)) > 0 and method > 0:
            xy = np.column_stack((xx2.flatten(), yy2.flatten()))
            var2 = hm.flatten()
            ind = ~np.isnan(var2)
            hm2 = scipy.interpolate.griddata(xy[ind, :], var2[ind], (xx2, yy2), method='nearest')
            hm[np.isnan(hm)] = hm2[np.isnan(hm)]
        self.heatmap = hm

    def init_plot(self):
        """Initialize plot.

        Examples:
            fig_size can be:
                1) [w,h] in inches, the one that limits sets size
                2) height in inches
                3) [x,y,dx,dy] in pixels
        """
        fig_size = self.settings['fig_size']
        if type(fig_size) in [float, int]:  # fig height given
            fs = (fig_size*self.x_range/self.y_range, fig_size)
            self.fig, self.ax = plt.subplots(figsize=fs)
        elif len(fig_size) == 2:
            if self.x_range/self.y_range > fig_size[0]/fig_size[1]:  # width limits size
                fs = (fig_size[0], fig_size[0]*self.y_range/self.x_range)
            else:  # height limits size
                fs = (fig_size[1]*self.x_range/self.y_range, fig_size[1])
            self.fig, self.ax = plt.subplots(figsize=fs)
        else:  # [x,y,dx,dy] given
            self.fig, self.ax = plt.subplots()
            mngr = plt.get_current_fig_manager()
            s = fig_size
            mngr.window.setGeometry(s[0], s[1], s[2], s[3])
        sb = self.sub_borders
        self.fig.subplots_adjust(bottom=sb[0], top=sb[1], left=sb[2], right=sb[3])
        plt.subplots_adjust(wspace=0, hspace=0)
        self.ax.set_xlim([self.x_min, self.x_max])
        self.ax.set_ylim([self.y_min, self.y_max])
        self.ax.tick_params(axis='both', which='both', bottom=False, labelbottom=False,
                            top=False, labeltop=False, left=False, labelleft=False,
                            right=False, labelright=False)
        if self.equal_aspect:
            self.ax.set_aspect('equal')

    def add_topo(self):
        """Add topology for nodes and conns with plotting properties set with plot_settings()."""
        # Lists used to update plot after manual editing of node positions
        self.segments_index = []  # node index
        self.segments = []  # coordinates
        self.segments_object = []  # plotting object (LineCollection or plot)
        self.node_text = []
        self.node_text_index = []
        # nodes + labels
        for s in np.unique(self.node_set[self.node_set >= 0]):
            l, lw, c = self.node_length[s], self.node_lw[s], self.node_color[s]
            fs, c2 = self.node_name_fs[s], self.node_name_color[s]
            ind = find((self.node_set == s) & (self.node_status == 1))
            # x, y, text = self.x[ind], self.y[ind], self.node_name_list[ind]
            x, y, text = self.x, self.y, self.node_name_list
            # label
            temp = self.sets_variable_lim
            temp = [int(b) if int(b) == b else b for b in temp]
            if self.sets_variable is None:
                label = 'All nodes'
            elif s == 0:
                label = self.sets_variable + ' $\in \, [%s, \infty)$' % temp[s]
            else:
                label = self.sets_variable + ' $\in \, [%s, %s)$' % (temp[s], temp[s-1])
            # plot nodes
            gid = ['node%d' % i for i in ind]
            self.segments_index.append(ind)
            if l == 0:  # dots
                self.segments.append(np.column_stack((x, y)))
                self.segments_object.append(self.ax.plot(x, y, ms=lw**2, marker='o', ls='', c=c,
                                                         zorder=10, label=label, picker=5, gid=gid)[0])
            else:  # node bars
                dx = l/200*self.x_range
                segments = [[(xs - dx, ys), (xs + dx, ys)] for xs, ys in zip(x, y)]
                self.segments.append(segments)
                lc = mcoll.LineCollection(segments, colors=c, linewidths=lw, label=label,
                                          picker=self.picker_node, gid=gid, zorder=10)
                self.segments_object.append(self.ax.add_collection(lc))
            # node text
            if fs > 0:
                dy = lw * self.y_range / 2000  # displacement of text
                self.node_text_index.extend(list(ind))
                for n in range(len(ind)):
                    self.node_text.append(self.ax.text(x[n], y[n]+dy, text[n], va='bottom', ha='center',
                                                       color=c2, size=fs, zorder=15))
        # conns
        for s in np.unique(self.conn_set[self.conn_set >= 0]):
            ind = find((self.conn_set == s) & (self.conn_status > 0))
            lw, c = self.conn_lw[s], self.conn_color[s]
            if self.conn_colored is not None:
                c = self.conn_colored[ind]  # color depending on some variable
            if self.conn_widthed is not None:
                lw = self.conn_widthed[ind]  # line width depending on some variable
            # plot lines
            gid = ['conn%d' % i for i in ind]
            ind1 = self.from_node_index_arr[ind]  # indices to get coordinates for "from nodes"
            ind2 = self.to_node_index_arr[ind]
            self.segments_index.append(np.column_stack((ind1, ind2)))
            segments = list()
            for x1, y1, x2, y2 in zip(self.x[ind1], self.y[ind1], self.x[ind2], self.y[ind2]):
                segments.append([(x1, y1), (x2, y2)])
            self.segments.append(segments)
            lc = mcoll.LineCollection(segments, colors=c, linewidths=lw, gid=gid, zorder=5, picker=self.picker_conn)
            self.segments_object.append(self.ax.add_collection(lc))

    def add_arrows(self, var, para_func):
        """Draw arrows on conns representing some variable.
        If variable > 0 -> arrow from node1 to node2 and vice versa.
        para_func defines how parallel conns are handled."""

        para_func = lambda_vector(para_func)

        self.arrows_drawn = True
        var = self.conn_parameter_dict[var]
        sc = self.arrow_scaling / np.max(np.abs(var))**0.5 * self.y_range * 0.015  # scale for arrow size
        ind1, ind2 = self.from_node_index_arr, self.to_node_index_arr  # indices of node1,node2 in node
        for n in range(len(self.unique_conns)):
            conns = find(self.parallel_ind == n)  # all parallel conns between current nodes

            # find signs; 0 for set -1 or out-of service, 1 for lowest to highest node,
            # -1 for highest to lowest node
            signs = arr([0 if s < 0 or st <= 0 else 1 for s, st in zip(self.conn_set[conns], self.conn_status[conns])])
            signs[self.from_node_index_arr[conns] > self.to_node_index_arr[conns]] *= -1
            v = var[conns] * signs  # variable with sign
            v = para_func(v)  # aggregation of parallel conns

            # get coordinates, (x1,y1) is lowest node index
            x1, y1 = self.x[ind1[conns[0]]], self.y[ind1[conns[0]]]
            x2, y2 = self.x[ind2[conns[0]]], self.y[ind2[conns[0]]]
            if self.from_node_index_arr[conns[0]] > self.to_node_index_arr[conns[0]]:
                x1, x2, y1, y2 = x2, x1, y2, y1
            if hasattr(self, 'conn_colored'):  # conn color based on parameter
                c = self.conn_colored[conns[0]]
            else:  # conn color for sets
                c = self.conn_color[self.conn_set[conns[0]]]
            hw = abs(v)**0.5 * sc
            dx = (x2-x1) / 2
            dy = (y2-y1) / 2
            adjust = 1 - (hw * 0.75) / (dx**2 + dy**2) ** 0.5  # put arrow in middle of line
            dx *= adjust
            dy *= adjust
            if v > 0:
                self.ax.arrow(x1, y1, dx, dy, head_width=hw, linestyle=None, fc=c, ec=c, width=0, zorder=5)
            else:
                self.ax.arrow(x2, y2, -dx, -dy, head_width=hw, linestyle=None, fc=c, ec=c, width=0, zorder=5)

    def add_heatmap(self, clim, cmap):
        """Add heatmap, clim e.g. [0.9, 1.1], cmap e.g. 'jet','viridis'."""
        if hasattr(self, 'heatmap'):
            hm = np.flipud(self.heatmap)
            aspect = 'equal' if self.equal_aspect else 'auto'
            if clim is None:
                self.hm = self.ax.imshow(hm, extent=self.extent, cmap=cmap, zorder=0, aspect=aspect)
            else:
                self.hm = self.ax.imshow(hm, extent=self.extent, clim=clim, cmap=cmap, zorder=0, aspect=aspect)
        else:
            pass
            # print('First use obj.calculate_heatmap() to calculate heatmap of selected variable.')
        self.heatmap_drawn = True

    def add_legend(self):
        """Adds legend and colorbar (if heatmap present)."""
        handles, labels = self.ax.get_legend_handles_labels()
        labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0], reverse=True))  # Largest to smallest
        corners = arr([[self.x_max, self.y_max], [self.x_min, self.y_max],  # best corners for legend and colorbars
                       [self.x_min, self.y_min], [self.x_max, self.y_min]])
        min_dist = [min(x) for x in cdist(corners, np.column_stack((self.x, self.y))[self.node_set >= 0, :])]
        if labels[0] != 'All nodes':
            loc = np.argmax(min_dist) + 1
            self.ax.legend(handles, labels, frameon=False, loc=loc, fontsize=9)
            min_dist[np.argmax(min_dist)] = 0  # do not use same corner again

        # colorbar(s)
        pos_cb = [[0.9, 0.8, 0.03, 0.15], [0.05, 0.8, 0.03, 0.15], [0.05, 0.05, 0.03, 0.15], [0.9, 0.05, 0.03, 0.15]]
        if hasattr(self, 'hm'):
            pos_cb_hm = pos_cb[np.argmax(min_dist)]
            min_dist[np.argmax(min_dist)] = 0
            cbaxes_hm = self.fig.add_axes(pos_cb_hm)
            cbar_hm = self.fig.colorbar(self.hm, cax=cbaxes_hm)
            cbar_hm.ax.set_xlabel(self.parent.settings['heatmap_var'], size=9)
            cbar_hm.ax.tick_params(labelsize=9)
        if hasattr(self, 'conn_colored'):
            import matplotlib as mpl
            var = self.parent.settings['conn_colors_var']
            cmap = self.parent.settings['conn_colors_cmap']
            norm = mpl.colors.Normalize(vmin=0, vmax=1)
            pos_cb_conn = pos_cb[np.argmax(min_dist)]
            cbaxes_conn = self.fig.add_axes(pos_cb_conn)
            cbar_conn = mpl.colorbar.ColorbarBase(cbaxes_conn, cmap=cmap, norm=norm, ticks=[0, 1])
            cbar_conn.ax.set_xlabel(var, size=9)
            y1 = str_sig(min(self.conn_parameter_dict[var]), self.significant_figures)
            y2 = str_sig(max(self.conn_parameter_dict[var]), self.significant_figures)
            cbar_conn.ax.set_yticklabels([y1, y2])
            cbar_conn.ax.tick_params(labelsize=9)

    def save(self, file_save):
        """Save the map, e.g. pdf, png."""
        try:
            plt.savefig(file_save)
            self.map_saved = file_save
        except PermissionError:
            pass
            # print('%s already open or permission denied' % file_save)

    def update_plot(self, node, x, y):
        """Update plot after one node has been moved (layout edit mode)."""
        for ind, seg, obj in zip(self.segments_index, self.segments, self.segments_object):
            if type(obj) is mcoll.LineCollection:
                if ind.ndim == 1:  # move node bar
                    ii = find(ind == node)
                    for i in ii:
                        dx = seg[i][1][0]-np.mean([seg[i][0][0], seg[i][1][0]])
                        y0 = seg[i][0][1]
                        seg[i] = [(x-dx, y), (x+dx, y)]
                        obj.set_paths(seg)
                else:  # move conns
                    update = False
                    ii = find(ind[:, 0] == node)  # from node is moved
                    for i in ii:
                        seg[i] = [(x, y), seg[i][1]]
                        update = True
                    ii = find(ind[:, 1] == node)  # to node is moved
                    for i in ii:
                        seg[i] = [seg[i][0], (x, y)]
                        update = True
                    if update:
                        obj.set_paths(seg)
            else:  # move node dot
                ii = find(ind == node)
                for i in ii:
                    y0 = seg[i][1]
                    seg[i] = (x, y)
                    obj.set_xdata(seg[:, 0])
                    obj.set_ydata(seg[:, 1])
        # move node text
        ii = find(arr(self.node_text_index) == node)
        for i in ii:
            dy = self.node_text[i].get_position()[1] - y0  # text y vs. old node y
            self.node_text[i].set_position((x, y + dy))
        self.fig.canvas.draw()

    def display_info(self, event):
        """On click, display node/conn information."""
        if type(event) is list:  # event triggered by key (next parallel conn)
            ind = event[0]
            self.mult_event = event[1:]
        else:  # event triggered by click
            ind = arr(event.artist.get_gid())[event.ind[0]]
            if 'conn' in ind:
                ind = self.parallel[ind][0]
                self.mult_event = self.parallel[ind][1:]  # remaining parallel conns
        if len(self.mult_event) > 0:
            parallel = True
        else:
            parallel = False
        if self.event_id == ind:
            self.annot.set_visible(False)
            self.event_id = ''
            self.fig.canvas.draw_idle()
            return
        else:
            self.event_id = ind
        if 'node' in ind:
            # FIXME: don't access arrays by numerical index, too error prone
            n = int(ind[4:])  # node index
            info = self.node_name_list[n] + '\n'
            for var in self.node_info_param:
                info += '\n%s: %s' % (var, str_sig(self.node_parameter_dict[var][n], self.significant_figures))
            info += self.node_info[n]
            x, y = self.x[n], self.y[n]
        elif 'conn' in ind:
            # FIXME: don't access arrays by numerical index, too error prone
            n = int(ind[4:])  # conn index
            info = self.conn_name_list[n] + '\n'
            if parallel:
                info += 'parallel conn, press "n" to see next\n'
            for var in self.conn_info_param:
                info += '\n%s: %s' % (var, str_sig(self.conn_parameter_dict[var][n], self.significant_figures))
            info += self.conn_info[n]
            xx = [self.x[self.from_node_index_arr[n]], self.x[self.to_node_index_arr[n]]]
            yy = [self.y[self.from_node_index_arr[n]], self.y[self.to_node_index_arr[n]]]
            x, y = np.mean(xx), np.mean(yy)
        self.annot.xy = (x, y)
        self.annot.set_position(self.annot_xy(x, y, info))
        self.annot.set_visible(True)
        self.annot.set_text(info)
        self.fig.canvas.draw_idle()

    def annot_xy(self, x, y, info):
        """Calculate xytext for annotation.
        (approximately good location, would be better with anchor)"""
        info_width = np.max([len(i) for i in info.split('\n')])
        info_lines = len(info.split('\n'))
        x1, x2 = self.ax.get_xlim()
        y1, y2 = self.ax.get_xlim()
        d = cdist(np.atleast_2d([x, y]), arr([[x1, y1], [x1, y2], [x2, y2], [x2, y1]]))
        loc = np.argmax(d[0])  # best placement of text
        xs, ys = 4.5, 8
        if loc == 0:
            xt = -info_width * xs - 20
            yt = -info_lines * ys - 20
        elif loc == 1:
            xt = -info_width * xs - 20
            yt = 20
        elif loc == 2:
            xt, yt = 20, 20
        elif loc == 3:
            xt = 20
            yt = -info_lines * ys - 20
        return xt, yt

    def onpick(self, event):
        """A node is selected in layout edit mode."""
        ind = event.artist.get_gid()[event.ind[0]]
        if 'node' in ind:
            self.node_cng = int(ind[4:])
            self.old_pos.append([self.node_cng, self.x[self.node_cng], self.y[self.node_cng]])

    def move(self, event):
        """Mouse move -> change node position (if a node was first selected)."""
        if self.node_cng is not None and event.xdata is not None:
            self.x[self.node_cng] = event.xdata
            self.y[self.node_cng] = event.ydata
            self.update_plot(self.node_cng, event.xdata, event.ydata)

    def release(self, event):
        """Mouse release."""
        self.node_cng = None

    def handle_close(self, event):
        """Save some stuff to parent when figure closed."""
        # fig_manager = plt.get_current_fig_manager()
        # geom = fig_manager.window.geometry()
        # self.parent.settings['fig_size'] = geom.getRect()
        self.settings['xy_type'] = 3  # default to use same layout next time...
        self.settings['x_coordinate'] = self.x
        self.settings['y_coordinate'] = self.y

    def keypress(self, event):
        """Actions on key press.
        Undo / redo last move if key z / y are pressed.
        Change between information and layout edit mode with key m"""
        if len(self.old_pos) > 0 and event.key == 'z' and self.mode == 'edit':
            old = self.old_pos.pop()
            self.new_pos.append([old[0], self.x[old[0]], self.y[old[0]]])
            self.x[old[0]] = old[1]
            self.y[old[0]] = old[2]
            self.update_plot(old[0], old[1], old[2])
        if len(self.new_pos) > 0 and event.key == 'y' and self.mode == 'edit':
            new = self.new_pos.pop()
            self.old_pos.append([new[0], self.x[new[0]], self.y[new[0]]])
            self.x[new[0]] = new[1]
            self.y[new[0]] = new[2]
            self.update_plot(new[0], new[1], new[2])
        if event.key == 'm':  # change between modes (information / layout editor)
            if self.interactive_info_display == 1:
                self.interactive_info_display = 2
                info = "\nLayout edit mode:\nDrag and drop nodes, press 'z' and 'y' to undo/redo\n" +\
                       "Press 'm' to switch back to information mode."
            for cid in self.mpl_id[1:]:
                    self.fig.canvas.mpl_disconnect(cid)
            if self.mode == 'info':
                if self.heatmap_drawn or self.arrows_drawn:
                    pass
                    # print('\nWarning: arrows and heatmap will not be updated on the fly.')
                self.mode = 'edit'
                self.annot.set_visible(False)
                self.event_id = ''
                self.fig.canvas.draw_idle()
                self.mpl_id.append(self.fig.canvas.mpl_connect('pick_event', onpick))
                self.mpl_id.append(self.fig.canvas.mpl_connect('motion_notify_event', move))
                self.mpl_id.append(self.fig.canvas.mpl_connect('button_release_event', release))
                self.mpl_id.append(self.fig.canvas.mpl_connect('key_press_event', keypress))
            else:
                self.mode = 'info'
                self.mpl_id.append(self.fig.canvas.mpl_connect('pick_event', display_info))
                self.mpl_id.append(self.fig.canvas.mpl_connect('key_press_event', keypress))
        if event.key == 'n' and self.mode == 'info':  # toggle between parallel conns
            if len(self.mult_event) > 0:
                display_info(self.mult_event)
        self.mpl_id = [self.fig.canvas.mpl_connect('close_event', handle_close)]
