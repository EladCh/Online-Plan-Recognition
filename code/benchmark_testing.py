import os
import Main
ROOT = os.getcwd()
path = ROOT + "/test_benchmarks"
os.chdir(path)
o = os.getcwd()

# Main.run("intrusion-detection_p20_hyp-1_10_1.tar.bz2")

# # # iterating all problems files and running them one by one
entries = os.listdir(path)
run_command = ""
for entry in entries:
    os.chdir(path)
    os.system("cp " + entry + " " + ROOT+"/"+entry)
    os.chdir(ROOT)
    Main.run(entry)
    os.system("rm " + entry)
    # os.chdir(path)
path = os.getcwd() + "/results"
os.chdir(path)
command = "rm statistical_data.csv"
os.system(command)

print "\n\nDone!  \\,,,/ (-.-) \\,,,/"
