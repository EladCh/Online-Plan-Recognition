import glob
import os

path = os.getcwd()
# print path
data = ""
os.chdir(path + "/results")
for text_file in glob.glob("*.csv"):
    data = ""
    if "atoms" not in text_file:


        with open(text_file, "r+") as outstream:
            for i in range(3):
                l = outstream.readline()
                data += l
                if "Hyp=" in l:
                    num = int(l.split("=")[1])
            data += ("obs_num,hyp_num,")
            for i in range(num):
                data += ("hyp_test_failed,hyp_ideal_cost_o,hyp_greedy_cost_o,hyp_score,hyp_cost_not_O,hyp_prob_o,hyp_prob_not_O,hype_plan_time_O,hyp_plan_time_not_O,hyp_trans_time,hyp_plan_time,hyp_test_time,hyp_is_true,timeout,heap_restriction,")
            data += ("\n")

            lines = outstream.readlines()
            for line in lines:
                data += line

        with open(text_file, "w") as outstream:
            outstream.write(data)
