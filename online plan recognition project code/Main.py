import os
import sys
import glob
import Output_to_online

#use -P for HSP none for LAMA
import prob_PR

ROOT_DIR = os.getcwd()

# run prob_PR in offline mode
def greedy_offline(file_name):
    options = [ROOT_DIR + '/prob_PR.py', '-e', file_name, '-O', '-P']
    prob_PR.run(options)


# run prob_PR in online mode
def optimal_online(file_name):
    options = [ROOT_DIR + '/prob_PR.py', '-e', file_name, '-O', '-P', '-n']
    prob_PR.run(options)


def run(file_name):
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

    # remove unnecessary files and move final report files to "results" folder
    path = os.getcwd()
    remove_command = 'rm -rf *.log report.txt *.res *.csv *.res.* *.pddl *.dat prob-*-PR *.stats output output.sas *.groups temp_results obs_prob-*-PR'
    os.system(remove_command)

    # moving all the files to results folder
    for text_file in glob.glob("*.txt"):
        if text_file != "CMakeLists.txt":
            os.system("mv " + path + "/" + text_file + " " + path + "/results")

    # creating statistical csv file of all result files
    import csv_to_output
    os.chdir(ROOT_DIR + "/results")
    entries = os.listdir(os.getcwd())
    for entry in entries :
        if "atoms" not in entry and "used_planner" not in entry and "statistical" not in entry and "processed" not in entry:
            if not os.path.isfile(entry):
                continue
            csv_to_output.run(entry)

    os.chdir(ROOT_DIR)

# in order to run a benchmark uncomment the line below and update the benchmark
# run("intrusion-detection_p20_hyp-11_50_0.tar.bz2")

