
import os, sys
import time, json
import requests

try:
    from shared_modules import format_utils

except ModuleNotFoundError:
    '''
    This trick to import the format_utils module can be
    removed once the project gets properly packaged
    '''
    comm_path = os.path.abspath(__file__)[0:-21] + "shared_modules"
    print("comm_path: ", comm_path)
    sys.path.insert(1, comm_path)
    import format_utils

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2 import QtUiTools
from PySide2.QtGui import *

from gui_utils import TreeDirScene, AdvancedParameters

from simpler_param_widgets import ImportTmpWidg as ImportWidget
from simpler_param_widgets import (
    FindspotsSimplerParameterTab, IndexSimplerParamTab,
    RefineBravaiSimplerParamTab, RefineSimplerParamTab,
    IntegrateSimplerParamTab, SymmetrySimplerParamTab,
    ScaleSimplerParamTab, CombineExperimentSimplerParamTab
)


def json_data_request(url, cmd):
    try:
        req_get = requests.get(url, stream = True, params = cmd)
        str_lst = []
        line_str = ''
        while True:
            tmp_dat = req_get.raw.read(1)
            single_char = str(tmp_dat.decode('utf-8'))
            line_str += single_char
            if single_char == '\n':
                str_lst.append(line_str[:-1])
                line_str = ''

            elif line_str[-7:] == '/*EOF*/':
                print('>>  /*EOF*/  <<')
                break

        json_out = json.loads(str_lst[1])

    except requests.exceptions.RequestException:
        print("\n requests.exceptions.RequestException \n")
        json_out = None

    return json_out


class Run_n_Output(QThread):
    line_out = Signal(str)
    def __init__(self, request):
        super(Run_n_Output, self).__init__()
        self.request = request

    def run(self):
        line_str = ''
        while True:
            tmp_dat = self.request.raw.read(1)
            single_char = str(tmp_dat.decode('utf-8'))
            line_str += single_char
            if single_char == '\n':
                #print(line_str[:-1])
                self.line_out.emit(line_str)
                line_str = ''

            elif line_str[-7:] == '/*EOF*/':
                print('>>  /*EOF*/  <<')
                self.line_out.emit(' \n /*EOF*/ \n')
                break



class MainObject(QObject):
    def __init__(self, parent = None):
        super(MainObject, self).__init__(parent)

        ui_path = os.path.dirname(os.path.abspath(__file__))
        ui_path += os.sep + "client.ui"
        self.window = QtUiTools.QUiLoader().load(ui_path)
        self.window.incoming_text.setFont(QFont("Monospace"))

        sys_font = QFont()
        self.font_point_size = sys_font.pointSize()


        self.tree_obj = format_utils.TreeShow()
        self.tree_scene = TreeDirScene(self)
        self.window.treeView.setScene(self.tree_scene)

        self.my_url = 'http://localhost:8080/'
        self.current_next_buttons = 0
        self.current_params_widget = 0

        self.param_widget_lst = []
        imp_widg = ImportWidget()
        imp_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.ImportScrollArea.setWidget(imp_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :imp_widg,
                "simple"    :None,
                "advanced"  :None
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["find_spots_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            fd_advanced_parameters = AdvancedParameters()
            fd_advanced_parameters.build_pars(par_def)
            fd_advanced_parameters.item_changed.connect(self.item_changed_f_advanced)
            self.window.FindspotsAdvancedScrollArea.setWidget(fd_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        find_simpl_widg = FindspotsSimplerParameterTab()
        find_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.FindspotsSimplerScrollArea.setWidget(find_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :find_simpl_widg,
                "advanced"  :fd_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["index_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            id_advanced_parameters = AdvancedParameters()
            id_advanced_parameters.build_pars(par_def)
            self.window.IndexAdvancedScrollArea.setWidget(id_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        index_simpl_widg = IndexSimplerParamTab()
        index_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.IndexSimplerScrollArea.setWidget(index_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :index_simpl_widg,
                "advanced"  :id_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["refine_bravais_settings_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            rb_advanced_parameters = AdvancedParameters()
            rb_advanced_parameters.build_pars(par_def)
            self.window.RefineBravaiAdvancedScrollArea.setWidget(rb_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        refi_brv_simpl_widg = RefineBravaiSimplerParamTab()
        refi_brv_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.RefineBravaiSimplerScrollArea.setWidget(refi_brv_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :refi_brv_simpl_widg,
                "advanced"  :rb_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["refine_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            rf_advanced_parameters = AdvancedParameters()
            rf_advanced_parameters.build_pars(par_def)
            self.window.RefineAdvancedScrollArea.setWidget(rf_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        ref_simpl_widg = RefineSimplerParamTab()
        ref_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.RefineSimplerScrollArea.setWidget(ref_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :ref_simpl_widg,
                "advanced"  :rf_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["integrate_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            it_advanced_parameters = AdvancedParameters()
            it_advanced_parameters.build_pars(par_def)
            self.window.IntegrateAdvancedScrollArea.setWidget(it_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        integr_simpl_widg = IntegrateSimplerParamTab()
        integr_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.IntegrateSimplerScrollArea.setWidget(integr_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :integr_simpl_widg,
                "advanced"  :it_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["symmetry_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            sm_advanced_parameters = AdvancedParameters()
            sm_advanced_parameters.build_pars(par_def)
            self.window.SymmetryAdvancedScrollArea.setWidget(sm_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        sym_simpl_widg = SymmetrySimplerParamTab()
        sym_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.SymmetrySimplerScrollArea.setWidget(sym_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :sym_simpl_widg,
                "advanced"  :sm_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["scale_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            sc_advanced_parameters = AdvancedParameters()
            sc_advanced_parameters.build_pars(par_def)
            self.window.ScaleAdvancedScrollArea.setWidget(sc_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        scale_simpl_widg = ScaleSimplerParamTab()
        scale_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.ScaleSimplerScrollArea.setWidget(scale_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :scale_simpl_widg,
                "advanced"  :sc_advanced_parameters
            }
        )
        cmd = {"nod_lst":"", "cmd_lst":["combine_experiments_params"]}
        lst_params = json_data_request(self.my_url, cmd)
        if lst_params is not None:
            lin_lst = format_utils.param_tree_2_lineal(lst_params)
            par_def = lin_lst()
            ce_advanced_parameters = AdvancedParameters()
            ce_advanced_parameters.build_pars(par_def)
            self.window.CombineAdvancedScrollArea.setWidget(ce_advanced_parameters)

        else:
            print("something went wrong with the list of parameters")

        comb_simpl_widg = CombineExperimentSimplerParamTab()
        comb_simpl_widg.item_changed.connect(self.item_changed_f_simple)
        self.window.CombineSimplerScrollArea.setWidget(comb_simpl_widg)
        self.param_widget_lst.append(
            {
                "only_one"  :None,
                "simple"    :comb_simpl_widg,
                "advanced"  :ce_advanced_parameters
            }
        )
        big_f_size = int(self.font_point_size * 1.6)
        big_font = QFont("OldEnglish", pointSize = big_f_size, italic=True)
        self.window.CurrentControlWidgetLabel.setFont(big_font)
        self.window.CurrentControlWidgetLabel.setText("The Quick Brown Fox Jumps Over The Lazy Dog")

        self.tree_scene.node_clicked.connect(self.on_node_click)
        self.window.CmdSend2server.clicked.connect(self.request_launch)
        self.window.LoadParsButton.clicked.connect(self.request_params)
        self.window.Reset2DefaultPushButton.clicked.connect(self.reset_param)
        self.tree_scene.draw_tree_graph([])
        self.window.show()

    def on_node_click(self, nod_num):
        print("clicked node number ", nod_num)
        prev_text = str(self.window.NumLinLst.text())
        self.window.NumLinLst.setText(
            str(prev_text + " " + str(nod_num))
        )

    def add_line(self, new_line):
        self.window.incoming_text.moveCursor(QTextCursor.End)
        self.window.incoming_text.insertPlainText(new_line)
        self.window.incoming_text.moveCursor(QTextCursor.End)

    def item_changed_f_simple(self, str_path, str_value):
        print("item_changed from Simple Param Widget")
        print("str_path, str_value: ", str_path, str_value)

    def item_changed_f_advanced(self, str_path, str_value):
        print("item_changed from Advanced Param Widget")
        print("str_path, str_value: ", str_path, str_value)

    def request_launch(self):
        cmd_str = str(self.window.CmdEdit.text())
        print("cmd_str", cmd_str)
        nod_str = str(self.window.NumLinLst.text())
        self.window.NumLinLst.clear()
        nod_lst = nod_str.split(" ")
        print("nod_lst", nod_lst)
        cmd = {"nod_lst":nod_lst, "cmd_lst":[cmd_str]}
        try:
            req_get = requests.get(self.my_url, stream = True, params = cmd)
            self.thrd = Run_n_Output(req_get)
            self.thrd.line_out.connect(self.add_line)
            self.thrd.finished.connect(self.request_display)
            self.thrd.start()

        except requests.exceptions.RequestException:
            print("something went wrong with the request launch")

    def request_display(self):
        cmd = {"nod_lst":"", "cmd_lst":["display"]}
        lst_nodes = json_data_request(self.my_url, cmd)
        if lst_nodes is not None:
            lst_str = self.tree_obj(lst_nod = lst_nodes)
            lst_2d_dat = self.tree_obj.get_tree_data()

            for tree_line in lst_str:
                self.add_line(tree_line + "\n")

            self.tree_scene.clear()
            self.tree_scene.draw_tree_graph(lst_2d_dat)
            self.tree_scene.update()

        else:
            print("something went wrong with the list of nodes")

    def reset_param(self):
        print("reset_param")
        try:
            self.param_widget_lst[self.current_params_widget]["only_one"].reset_pars()

        except AttributeError:
            self.param_widget_lst[self.current_params_widget]["advanced"].reset_pars()
            self.param_widget_lst[self.current_params_widget]["simple"].reset_pars()

    def request_params(self):
        self.current_params_widget += 1
        if self.current_params_widget >= self.window.StackedParamsWidget.count():
            self.current_params_widget = 0

        self.window.StackedParamsWidget.setCurrentIndex(
            self.current_params_widget
        )

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    m_obj = MainObject()
    sys.exit(app.exec_())

