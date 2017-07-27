import os
import sys
import glob
import Output_to_online

#use -P for HSP none for LAMA
import prob_PR

ROOT_DIR = os.getcwd()

def greedy_offline(file_name):
    # greedy_command = "python prob_PR.py -e " + file_name + " -O -P"
    # os.system(greedy_command)
    options = [ROOT_DIR + '/prob_PR.py', '-e', file_name, '-O', '-P']
    prob_PR.run(options)



def optimal_online(file_name):
    # optimal_command = "python prob_PR.py -e " + file_name + " -O -P -n"
    # os.system(optimal_command)
    options = [ROOT_DIR + '/prob_PR.py', '-e', file_name, '-O', '-P', '-n']
    prob_PR.run(options)

def run(file_name):
    f = ROOT_DIR
    os.chdir(ROOT_DIR)
    # create temp results directory and extract results.tar to it
    if not os.path.exists("temp_results"):
        os.makedirs("temp_results", mode=0777)


    # create temp directory for greedy log files
    if not os.path.exists("temp_results/greedy_log_files"):
        os.makedirs("temp_results/greedy_log_files", mode=0777)

    path = os.getcwd() + "/temp_results/greedy_log_files"

    # run greedy
    greedy_offline(file_name)

    # extracting log files
    os.system("mv results.tar.bz2 " + path)
    os.chdir(path)
    os.system("tar -xf results.tar.bz2 --wildcards --no-anchored 'report.txt'")
    os.system("rm results.tar.bz2")
    os.chdir(ROOT_DIR)

    # run optimal
    optimal_online(file_name)

    # create output file to online algorithms
    Output_to_online.create_outputs()

    # # remove unnecessary files and move final report files to "results" folder
    # os.chdir("../../")
    path = os.getcwd()
    remove_command = 'rm -rf *.log report.txt *.res *.csv *.res.* *.pddl *.dat prob-*-PR *.stats output output.sas *.groups temp_results obs_prob-*-PR'
    os.system(remove_command)

    # moving all the files to results folder
    for text_file in glob.glob("*.txt"):
        if text_file != "CMakeLists.txt":
            os.system("mv " + path + "/" + text_file + " " + path + "/results")

    import csv_to_output
    # os.chdir("../../")
    os.chdir(ROOT_DIR + "/results")
    # creating statistical csv file of all result files
    entries = os.listdir(os.getcwd())
    for entry in entries :
        if "atoms" not in entry and "used_planner" not in entry and "statistical" not in entry and "processed" not in entry:
            if not os.path.isfile(entry):
                continue
            csv_to_output.run(entry)

    t = os.getcwd()
    # remove unnecessary files and move final report files to "results" folder
    os.chdir(ROOT_DIR)

# run("intrusion-detection_p10_hyp-8_30_1.tar.bz2")
# run("intrusion-detection_p10_hyp-4_10_1.tar.bz2")
run("intrusion-detection_p10_hyp-5_50_2.tar.bz2")
# run("intrusion-detection_p10_hyp-0_10_0.tar.bz2")




# entries = os.listdir(os.getcwd())
# for entry in entries:
#     if "intrusion-detection" in entry:
#         run(entry)



# run("kitchen_generic_hyp-0_30_0.tar.bz2") #duplicate activities
# run("bui-campus_generic_hyp-0_30_20.tar.bz") #duplicate activities
# run("easy-ipc-grid_p5-10-10_hyp-0_50_0.tar.bz2") #path mismatch
# run("intrusion-detection_p10_hyp-1_10_1.tar.bz2") #works fine
# run("logistics_p01_hyp-7_30_0.tar.bz2")
# run("block-words_p01_hyp-6_30_1.tar.bz2")
