import csv
import numpy
import os


# compress csv file to one line
def csv_to_output_line(file_name, current_max_hyp=0):
    reader = csv.reader(open(file_name, "rb"), delimiter=",")
    x = list(reader)
    result = numpy.array(x, dtype=object)

    # random line for num of cols
    x = result[4]

    rows = result.shape[0]

    data = ""
    # Experiment name
    data += result[0][1].replace("\n","") + ","
    # hyps num
    h_num = result[1][1].replace("\n","")
    data += h_num  + ","

    hyps_num_int = int(h_num)

    cols = x.__len__() - int(h_num)
    line = []
    counter = 0
    title_line = 3
    true_hyp_col = -1
    t_hyp_counter = 0
    first_heap = True
    first_to = True
    for j in range(2, cols):
        if "hyp_test_failed" == result[title_line][j]:
            t_hyp_counter += 1
            test_failed = False
            for i in range(4, rows):
                if "True" == result[i][j]:
                    test_failed = True
            if test_failed:
                data += "True,"
            else:
                data += "False,"

        # split hyp cost O to obs and current
        elif "hype_plan_time_O" == result[title_line][j]:
            hype_plan_time_O = 0
            for i in range(4, rows):
                hype_plan_time_O += float(result[i][j])
            data += str(hype_plan_time_O) + ","

        elif "hyp_plan_time_not_O" == result[title_line][j]:
            hyp_plan_time_not_O = 0
            for i in range(4, rows):
                hyp_plan_time_not_O += float(result[i][j])
            data += str(hyp_plan_time_not_O) + ","

        elif "hyp_trans_time" == result[title_line][j]:
            hyp_trans_time = 0
            for i in range(4, rows):
                hyp_trans_time += float(result[i][j])
            data += str(hyp_trans_time) + ","

        elif "hyp_plan_time" == result[title_line][j]:
            hyp_plan_time = 0
            for i in range(4, rows):
                hyp_plan_time += float(result[i][j])
            data += str(hyp_plan_time) + ","

        elif "hyp_test_time" == result[title_line][j]:
            hyp_test_time = 0
            for i in range(4, rows):
                hyp_test_time += float(result[i][j])
            data += str(hyp_test_time) + ","

        elif "hyp_is_true" == result[title_line][j]:
            hyp_is_true = False
            for i in range(4, rows):
                if "True" == result[i][j]:
                    true_hyp_col = t_hyp_counter
                    hyp_is_true = True
            if hyp_is_true:
                data += "True,"
            else:
                data += "False,"

        elif "heap_restriction" == result[title_line][j] and first_heap:
            first_heap = False
            heap_rest = int(result[i][j])
            data += str(heap_rest) + ","

        elif "timeout" == result[title_line][j] and first_to:
            first_to = False
            timeout = int(result[i][j])
            data += str(timeout) + ","

    # creating the rank matrix
    # initialize
    ranking_matrix = [[2 for i in range(x.__len__()-cols)] for j in range(rows-4)]
    # set values based on the input file
    for i in range(4, rows):
        for j in range(cols,x.__len__()):
            ranking_matrix[i-4][j-cols] = result[i][j]

    # Convergence
    conv_array = []
    cou = 0
    num_of_obs = ranking_matrix.__len__()
    # reverse iterating the column
    for j in range(x.__len__() - cols):
        cou = 0
        con_value = float(1)
        con_index = 0
        # if the column didn't converge, insert 0 to the convergence array
        if float(ranking_matrix[num_of_obs-1][j]) < con_value:
            conv_array.append(0)
            continue
        # starting with the last cell, find how many cells are equal to 1
        else:
            inserted_flag = False
            for i in range(num_of_obs-1, -1, -1):
                current_value = ranking_matrix[i][j]
                if float(current_value) >= con_value:
                    cou +=1
                else:
                    conv_array.append(cou/float(num_of_obs))
                    inserted_flag = True
                    break
            if not inserted_flag:
                conv_array.append(cou / float(num_of_obs))

    # added only real hyp col
    data += str(conv_array[true_hyp_col-1]) + ","

    # ranked first, only for real hyp
    r_first_counter = 0
    # find the amount of times the real hyp had the highest rank
    for i in range(rows-4):
        m = max(ranking_matrix[i])
        real_hyp_rank = ranking_matrix[i][true_hyp_col-1]
        if float(real_hyp_rank) >= float(m):
            r_first_counter += 1
    first = float(r_first_counter)
    data += str(round(first/num_of_obs, 5))

    # write the collected data to statistical_data.csv
    with open("statistical_data.csv", "a") as outstream:
        outstream.write(data+"\n")

    if not os.path.exists("processed_results"):
        os.makedirs("processed_results", mode=0777)
    path = os.getcwd() + "/processed_results"

    # move the file to processed_results folder
    command = "mv " + file_name + " " + path
    os.system(command)

    if hyps_num_int>current_max_hyp:
        return hyps_num_int
    return current_max_hyp


def run(file_name):
    titles = "hyp_test_failed,hyp_is_true,hype_plan_time_O,hyp_plan_time_not_O,hyp_trans_time,hyp_plan_time,hyp_test_time,"
    title = "Experiment_name,hyps_num,hyp_test_failed,hyp_is_true,Timeout,Heap_restriction,hype_plan_time_O,hyp_plan_time_not_O,hyp_trans_time,hyp_plan_time,hyp_test_time,"
    max_hyp_num=0
    max_hyp_num=csv_to_output_line(file_name,max_hyp_num)

    path = os.getcwd() + "/processed_results"
    entries = os.listdir(os.getcwd())
    for entry in entries:
        if entry.endswith("atoms.csv"):
            command = "mv " + entry + " " + path
            os.system(command)
    for i in range(max_hyp_num-1):
        title += titles
    title += "convergence,ranked_first\n"

    # create the final statistical_result.csv file based on the previously created statistical_data file
    with open("statistical_data.csv", "r") as instream:
        with open("statistical_result.csv", "w") as outstream:
            outstream.write(title)
            for line in instream:
                outstream.write(line)

