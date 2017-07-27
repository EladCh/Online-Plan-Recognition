import os
import re
entries = os.listdir(os.getcwd())
count = 0
for entry in entries :
    if entry.endswith(".py"):
        print (entry)
        count += 1
print str(count)

# remove unnecessary files and move final report files to "results" folder
# os.chdir("../../")
path = os.getcwd()
remove_command = 'rm -rf *.log report.txt *.res *.csv *.res.* *.pddl *.dat prob-*-PR *.stats output output.sas *.groups temp_results'
os.system(remove_command)
