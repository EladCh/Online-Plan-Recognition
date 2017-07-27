import os
import time
ROOT_DIR = os.getcwd()


# unpack relevant files from results tar files
def unpack():
    # create temp results directory
    if not os.path.exists("temp_results/ideal_temp_files"):
        os.makedirs("temp_results/ideal_temp_files", mode=0777)

    path = os.getcwd()

    # unpack log, report and .soln files into corresponding folders
    entries = os.listdir(path)
    for entry in entries:
        if "results_" in entry:
            folder_name = path + "/temp_results/ideal_temp_files/" + entry
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, mode=0777)
            os.system("mv " + path + "/" + entry + " " + folder_name)
            os.chdir(folder_name)
            cmd = "tar -xf " + entry + " --wildcards --no-anchored '*[0-9]-O.log' 'report.txt' 'pr-problem.soln'"
            os.system(cmd)
            # erase tar file after done unpacking
            os.system("rm " + entry)
            os.chdir("../../")


# create report file for an online run
def create_report():
    path = os.getcwd()
    if not "/temp_results" in path:
        path += "/temp_results"
    path += "/ideal_temp_files"
    # insert all result tars into a sorted list
    entries = os.listdir(path)
    entries.sort()
    os.chdir("../")

    # set report file name (planner and current time)
    name_instream = open(ROOT_DIR + "/results/used_planner.txt", "r")
    file_name = name_instream.readline() + '_' + time.strftime("%c").replace(" ","_") + ".csv"
    name_instream.close()

    #collecting ideal costs from offline
    with open(ROOT_DIR + "/temp_results/greedy_log_files/report.txt", "r") as instream:
        report=[]
        offline_ideal_costs=[]
        report = instream.readlines()
        for line in report:
            if "Ideal_Cost" in line:
                offline_ideal_costs.append(line.split("=")[1].replace("\n",""))

    # create atoms.csv file for each csv file
    atoms_file_name = file_name.replace(".csv", "_atoms.csv")
    atom_path = ROOT_DIR + "/results/" + atoms_file_name
    atoms = open(atom_path, "w")

    # create final-report file based on the gathered data
    first = True
    with open(ROOT_DIR + "/results/" + file_name, "w") as outstream:
        for entry in entries:
            counter_flag = True
            offline_count = 0
            ranks = []
            read_lines_before = False
            file = path + "/" + entry
            os.chdir(file)
            # read data from report.txt file
            with open(file+"/report.txt", "r") as instream:
                if first:
                    for i in range(3):
                        line = instream.readline().split("=")
                        name = line[0]
                        value = line[1]

                        if "Num_Hyp" in line:
                            num_hyp = value
                        elif "Num_Obs" in line:
                            num_obs = value
                        outstream.write(name + "," + value)
                        atoms.write(name + "," + value)
                    outstream.write("obs_num,hyp_num,")
                    # add titles
                    for i in range(int(num_hyp)):
                        outstream.write("hyp_index,hyp_test_failed,hyp_is_true,timeout,"
                                        "heap_restriction,obs_cost,current_cost,ideal_cost,hyp_GR_rank,hyp_VK_rank,"
                                        "hyp_cost_not_O,hyp_prob_O,hyp_prob_not_O,hype_plan_time_O,hyp_plan_time_not_O,"
                                        "hyp_trans_time,hyp_plan_time,hyp_test_time,")
                    outstream.write("\n")
                    first = False
                    read_lines_before = True
                if not read_lines_before:
                    for i in range(3):
                        instream.readline()
                outstream.write(entry.replace('results_',"").replace('.tar.bz2',","))
                outstream.write(num_hyp.replace("\n", ","))

                hyp_counter = 1
                # add the relevant lines from report.txt
                for line in instream:
                    if "Hyp_VK_rank" in line:
                        ranks.append(line.split("=")[1].replace("\n", ""))
                        outstream.write(line.split("=")[1].replace("\n", ","))
                    elif "Hyp_Atoms_" in line:
                        atoms.write(line.split("=")[1])
                    elif "Ideal_Cost" in line:
                        if offline_ideal_costs[offline_count] == str(-1):
                            outstream.write(line.split("=")[1].replace("\n", ","))
                        else:
                            outstream.write(offline_ideal_costs[offline_count] +",")
                        offline_count += 1
                    elif "Hyp_Test_Failed" in line:
                        outstream.write(str(hyp_counter) + ",")
                        hyp_counter += 1
                        outstream.write(line.split("=")[1].replace("\n", ","))
                    else:
                        outstream.write(line.split("=")[1].replace("\n", ","))
                # add the rank values
                for rank in ranks:
                    outstream.write(rank + ",")
            outstream.seek(-1, os.SEEK_END)
            outstream.truncate()
            outstream.write("\n")

        os.chdir(ROOT_DIR)
    atoms.close()


def create_outputs():
    unpack()
    create_report()

