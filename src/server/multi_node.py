"""
DUI's command simple stacked widgets

Author: Luis Fuentes-Montero (Luiso)
With strong help from DIALS and CCP4 teams

copyright (c) CCP4 - DLS
"""

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import subprocess, psutil
import os, sys
import glob, json

try:
    from shared_modules import format_utils

except ModuleNotFoundError:
    '''
    This trick to import the format_utils module can be
    removed once the project gets properly packaged
    '''
    comm_path = os.path.abspath(__file__)[0:-20] + "shared_modules"
    sys.path.insert(1, comm_path)
    import format_utils

from params_2_json import get_param_list


def fix_alias(short_in):
    pair_list = [
        ("d", "display"                                     ),
        ("dl", "display_log"                                ),
        ("gb", "get_bravais_sum"                            ),
        ("st", "stop"                                       ),
        ("fdp", "find_spots_params"                         ),
        ("idp", "index_params"                              ),
        ("rbp", "refine_bravais_settings_params"            ),
        ("rfp", "refine_params"                             ),
        ("itp", "integrate_params"                          ),
        ("smp", "symmetry_params"                           ),
        ("scp", "scale_params"                              ),
        ("cep", "combine_experiments_params"                ),
        ("x4", "/scratch/dui_tst/X4_wide/*.cbf"             ),
        ("x41", "/scratch/dui_tst/X4_wide_0_to_9/*.cbf"     ),
        ("x42", "/scratch/dui_tst/X4_wide_10_to_19/*.cbf"   ),
        ("x43", "/scratch/dui_tst/X4_wide_20_to_29/*.cbf"   ),
        ("ip", "dials.import"                               ),
        ("mg", "dials.modify_geometry"                      ),
        ("gm", "dials.generate_mask"                        ),
        ("am", "dials.apply_mask"                           ),
        ("fd", "dials.find_spots"                           ),
        ("id", "dials.index"                                ),
        ("rb", "dials.refine_bravais_settings"              ),
        ("ri", "dials.reindex"                              ),
        ("rf", "dials.refine"                               ),
        ("it", "dials.integrate"                            ),
        ("sm", "dials.symmetry"                             ),
        ("sc", "dials.scale"                                ),
        ("ce", "dials.combine_experiments"                  ),
    ]
    long_out = short_in
    for pair in pair_list:
        if pair[0] == short_in:
            print("replacing ", pair[0], " with ", pair[1])
            long_out = pair[1]

    return long_out


class CmdNode(object):
    def __init__(self, parent_lst_in = None):
        self.parent_node_lst = []
        try:
            for single_parent in parent_lst_in:
                self.parent_node_lst.append(single_parent.lin_num)

        except TypeError:
            self.parent_node_lst = []

        self._lst_expt = []
        self._lst_refl = []
        self.lst2run = []
        self.full_cmd_lst = []
        self._run_dir = ""
        self.log_line_lst = []

        self.status = "Ready"
        self.child_node_lst = []
        self.lin_num = 0


        try:
            for single_parent in parent_lst_in:
                self.set_base_dir(single_parent._base_dir)
                for expt_2_add in glob.glob(single_parent._run_dir + "/*.expt"):
                    self._lst_expt.append(expt_2_add)

                for refl_2_add in glob.glob(single_parent._run_dir + "/*.refl"):
                    self._lst_refl.append(refl_2_add)

                lst_json = glob.glob(single_parent._run_dir + "/*.json")
                for json_2_add in lst_json:
                    self._lst_expt.append(json_2_add)

                if len(self._lst_expt) < len(self._lst_refl):
                    self._lst_expt += single_parent._lst_expt

                if len(self._lst_refl) == 0:
                    self._lst_refl += single_parent._lst_refl

        except TypeError:
            print("parent_lst_in =", parent_lst_in, "tmp empty; ", end='')

    def __call__(self, lst_in, req_obj = None):
        print("\n lst_in =", lst_in)
        self.full_cmd_lst.append([lst_in[0]])
        self.set_in_fil_n_par(lst_in)
        self.set_base_dir(os.getcwd())
        self.set_run_dir(self.lin_num)
        self.nod_req = req_obj
        self.run_cmd(self.nod_req)

    def set_root(self, run_dir = "/tmp/tst/", lst_expt = "/tmp/tst/imported.expt"):
        base_dir = os.getcwd()
        self.set_base_dir(base_dir)
        self._run_dir = run_dir
        self._lst_expt = []
        self._lst_refl = []
        self.full_cmd_lst = [['Root']]
        self.status = "Succeeded"

    def set_base_dir(self, dir_in = None):
            self._base_dir = dir_in

    def set_run_dir(self, num = None):
        self._run_dir = self._base_dir + "/run" + str(num)

        print("new_dir: ", self._run_dir, "\n")
        try:
            os.mkdir(self._run_dir)

        except FileExistsError:
            print("assuming the command should run in same dir")

    def set_in_fil_n_par(self, lst_in):
        #print("\n\n self.full_cmd_lst =", self.full_cmd_lst, " \n\n")
        for inner_lst in self.full_cmd_lst:
            self.lst2run.append(list(inner_lst))

        if self.full_cmd_lst[-1][0] == "dials.reindex":
            try:
                try:
                    sol_num = int(lst_in[1])

                except(IndexError, ValueError):
                    print(" *** ERROR ***")
                    print(" wrong solution number, defaulting to 1")
                    sol_num = 1

                json_file_tmp = None
                for file_str in self._lst_expt:
                    if "bravais_summary" in file_str:
                        json_file_tmp = str(file_str)

                if json_file_tmp is not None:
                    with open(json_file_tmp) as summary_file:
                        j_obj = json.load(summary_file)

                    change_of_basis_op = j_obj[str(sol_num)]["cb_op"]
                    input_str = "change_of_basis_op=" + str(change_of_basis_op)
                    self.full_cmd_lst[-1].append(input_str)
                    str2comp = "bravais_setting_" + str(sol_num) + ".expt"
                    for file_str in self._lst_expt:
                        if str2comp in file_str:
                            self._lst_expt = [str(file_str)]

                    self.lst2run[-1].append(" " + str(sol_num))

            except KeyError:
                print("KeyError from attempting to reindex")

        else:
            for expt_2_add in self._lst_expt:
                self.full_cmd_lst[-1].append(expt_2_add)

        for refl_2_add in self._lst_refl:
            self.full_cmd_lst[-1].append(refl_2_add)

        if self.full_cmd_lst[-1][0] != "dials.reindex":
            for par in lst_in[1:]:
                self.full_cmd_lst[-1].append(par)
                self.lst2run[-1].append(par)

        #print("lst2run =", self.lst2run)

    def run_cmd(self, req_obj = None):
        self.nod_req = req_obj
        self.status = "Busy"
        try:
            inner_lst = self.full_cmd_lst[-1]
            print("\n Running:", inner_lst, "\n")
            self.my_proc = subprocess.Popen(
                inner_lst,
                shell = False,
                cwd = self._run_dir,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                universal_newlines = True
            )
            new_line = None
            self.log_line_lst = []
            n_Broken_Pipes = 0
            if self.nod_req is not None:
                try:
                    str_lin_num = "node.lin_num=" + str(self.lin_num) + "\n"
                    self.nod_req.wfile.write(bytes(str_lin_num , 'ascii'))

                except BrokenPipeError:
                    print("\n *** BrokenPipeError *** while sending lin_num \n")


            while self.my_proc.poll() is None or new_line != '':
                new_line = self.my_proc.stdout.readline()
                if self.nod_req is not None:
                    try:
                        self.nod_req.wfile.write(bytes(new_line , 'ascii'))

                    except BrokenPipeError:
                        n_Broken_Pipes += 1

                else:
                    print(new_line[:-1])

                self.log_line_lst.append(new_line[:-1])

            if n_Broken_Pipes > 0:
                print("\n *** BrokenPipeError *** while sending output \n")

            self.my_proc.stdout.close()
            if self.my_proc.poll() == 0:
                print("subprocess poll 0")

            else:
                print("\n  *** ERROR *** \n\n poll =", self.my_proc.poll())
                self.status = "Failed"

            if self.status != "Failed":
                self.status = "Succeeded"

        except BaseException as e:
            print("Failed to run subprocess \n ERR:", e)
            self.status = "Failed"

    def stop_me(self):
        print("node", self.lin_num, "status:", self.status)
        if self.status == "Busy":
            print("attempting to stop the execution of node", self.lin_num)
            try:
                self.nod_req.wfile.write(bytes("attempting to stop \n" , 'ascii'))
                pid_num = self.my_proc.pid
                parent_proc = psutil.Process(pid_num)
                for child in parent_proc.children(recursive=True):
                    child.kill()

                parent_proc.kill()

            except BrokenPipeError:
                print("Broken Pipe Error")

        else:
            print("node", self.lin_num, "not running, so not stopping it")

    def get_bravais_summ(self):
        brav_summ_path = str(self._run_dir + "/bravais_summary.json")
        print("brav_summ_path:", brav_summ_path)
        with open(brav_summ_path) as summary_file:
            j_obj = json.load(summary_file)

        return j_obj


class Runner(object):
    def __init__(self, recovery_data):
        self.tree_output = format_utils.TreeShow()
        if recovery_data == None:
            root_node = CmdNode()
            root_node.set_root()
            self.step_list = [root_node]
            self.bigger_lin = 0

        else:
            self._recover_state(recovery_data)

    def run_dict(self, cmd_dict, req_obj = None):
        tmp_parent_lst_in = []
        for lin2go in cmd_dict["nod_lst"]:
            for node in self.step_list:
                if node.lin_num == lin2go:
                    tmp_parent_lst_in.append(node)

        print("\n cmd_dict: ", cmd_dict, "\n")

        full_cmd_lst = []
        for inner_lst in cmd_dict["cmd_lst"]:
            unalias_inner_lst = []
            for elem in inner_lst:
                unalias_inner_lst.append(fix_alias(elem))

            full_cmd_lst.append(unalias_inner_lst)

        print("full_cmd_lst", full_cmd_lst)

        if(
            len(tmp_parent_lst_in) > 0 and
            ["display"] not in full_cmd_lst and
            ["display_log"] not in full_cmd_lst and
            ["get_bravais_sum"] not in full_cmd_lst and
            ["stop"] not in full_cmd_lst
        ):
            node2run = self._create_step(tmp_parent_lst_in)

        return_list = []
        for uni_cmd in full_cmd_lst:
            if uni_cmd == ["display"]:
                return_list = format_utils.get_lst2show(self)
                self.tree_output(return_list)
                self.tree_output.print_output()

            elif uni_cmd == ["display_log"]:
                for lin2go in cmd_dict["nod_lst"]:
                    try:
                        lst2add = self.step_list[lin2go].log_line_lst
                        return_list.append(lst2add)

                    except IndexError:
                        print("\n *** ERROR *** \n wrong line \n not logging")

            elif uni_cmd == ["get_bravais_sum"]:
                for lin2go in cmd_dict["nod_lst"]:
                    try:
                        lst2add = self.step_list[lin2go].get_bravais_summ()
                        return_list.append(lst2add)

                    except IndexError:
                        print("\n *** ERROR *** \n wrong line \n not logging")


            elif uni_cmd == ["stop"]:
                for lin2go in cmd_dict["nod_lst"]:
                    try:
                        stat2add = self.step_list[lin2go].status
                        return_list.append([stat2add])
                        self.step_list[lin2go].stop_me()

                    except IndexError:
                        print("\n *** ERROR *** \n wrong line \n not logging")

            elif uni_cmd[0][-7:] == "_params":
                return_list = get_param_list(uni_cmd[0])

            else:
                try:
                    node2run(uni_cmd, req_obj)

                except UnboundLocalError:
                    print("\n *** ERROR *** \n wrong line \n not running")

            self._save_state()

        return return_list

    def _create_step(self, prev_step_lst):
        new_step = CmdNode(parent_lst_in=prev_step_lst)

        tmp_big = 0
        for node in self.step_list:
            if node.lin_num > tmp_big:
                tmp_big = node.lin_num

        self.bigger_lin = tmp_big + 1

        new_step.lin_num = self.bigger_lin
        for prev_step in prev_step_lst:
            prev_step.child_node_lst.append(new_step.lin_num)

        self.step_list.append(new_step)

        return new_step

    def _save_state(self):
        lst_nod = []
        for uni in self.step_list:
            node = {
                        "_base_dir"            :uni._base_dir,
                        "full_cmd_lst"         :uni.full_cmd_lst,
                        "lst2run"              :uni.lst2run,
                        "_lst_expt"            :uni._lst_expt,
                        "_lst_refl"            :uni._lst_refl,
                        "_run_dir"             :uni._run_dir,
                        "log_line_lst"         :uni.log_line_lst,
                        "lin_num"              :uni.lin_num,
                        "status"               :uni.status,
                        "parent_node_lst"      :uni.parent_node_lst,
                        "child_node_lst"       :uni.child_node_lst
                    }

            lst_nod.append(node)

        all_dat = {
                "step_list"             :lst_nod,
                "bigger_lin"            :self.bigger_lin,
            }

        with open("run_data", "w") as fp:
            json.dump(all_dat, fp, indent=4)

    def _recover_state(self, recovery_data):
        self.step_list =    []
        self.bigger_lin =   recovery_data["bigger_lin"]

        lst_nod = recovery_data["step_list"]
        for uni_dic in lst_nod:
            new_node = CmdNode()
            new_node._base_dir       = uni_dic["_base_dir"]
            new_node.full_cmd_lst    = uni_dic["full_cmd_lst"]
            new_node.lst2run         = uni_dic["lst2run"]
            new_node._lst_expt       = uni_dic["_lst_expt"]
            new_node._lst_refl       = uni_dic["_lst_refl"]
            new_node._run_dir        = uni_dic["_run_dir"]
            new_node.log_line_lst    = uni_dic["log_line_lst"]
            new_node.lin_num         = uni_dic["lin_num"]
            new_node.status          = uni_dic["status"]
            new_node.child_node_lst  = uni_dic["child_node_lst"]
            new_node.parent_node_lst = uni_dic["parent_node_lst"]

            self.step_list.append(new_node)

def str2dic(cmd_str):
    print("cmd_str =", cmd_str, "\n")

    cmd_dict = {"nod_lst":[],
                "cmd_lst":[]}

    lstpar = cmd_str.split(" ")
    for single_param in lstpar:
        try:
            cmd_dict["nod_lst"].append(int(single_param))

        except ValueError:
            break

    if len(cmd_dict["nod_lst"]) > 0:
        print("nod_lst=", cmd_dict["nod_lst"])

        new_par_str = ""
        for single_param in lstpar[len(cmd_dict["nod_lst"]):]:
            new_par_str += single_param + " "

        tmp_cmd_lst = new_par_str[0:-1].split(";")
        par_n_cmd_lst = []
        for single_command in tmp_cmd_lst:
            inner_lst = single_command.split(" ")
            par_n_cmd_lst.append(inner_lst)

    else:
        print("assuming disconnected command")
        par_n_cmd_lst = [[cmd_str]]

    cmd_dict["cmd_lst"] = par_n_cmd_lst

    return cmd_dict


if __name__ == "__main__":

    try:
        with open("run_data") as json_file:
            runner_data = json.load(json_file)

    except FileNotFoundError:
        runner_data = None
        print("Nothing to recover")

    cmd_tree_runner = Runner(runner_data)
    cmd_dict = str2dic("display")
    cmd_tree_runner.run_dict(cmd_dict)
    cmd_str = ""

    while cmd_str.strip() != "exit" and cmd_str.strip() != "quit":
        try:
            inp_str = "]]]>>> "
            cmd_str = str(input(inp_str))
            print("\n")

        except EOFError:
            print("Caught << EOFError >> \n  ... interrupting")
            sys.exit(0)

        except:
            print("Caught << some error >> ... interrupting")
            sys.exit(1)

        cmd_dict = str2dic(cmd_str)
        cmd_tree_runner.run_dict(cmd_dict)

        cmd_dict = str2dic("display")
        cmd_tree_runner.run_dict(cmd_dict)

