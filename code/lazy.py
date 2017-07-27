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


t = " bla ooo "

q = re.sub(" [a-z]* [a-z]* ", " [a-z]*_[a-z]* ", t)
q = t.replace(" . . ", " ._. ")

# q = re.sub(" [a-z]* [a-z]* ", " [a-z]*_[a-z]* ", t)

l = [1,5,3,5,8,6,9,-5,7,0,8]
l2 = [1,5,5,4,0,9,0,1,0,8]

nf = [x for x in l if x in l2]
# s = set(l)
num_of_obs = 2
for i in range(num_of_obs-1, -1, -1):
    print i

print num_of_obs
print nf