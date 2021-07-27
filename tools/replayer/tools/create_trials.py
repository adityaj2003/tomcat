import os 
import re
import shutil

TRIALS = []
FILES = {}
REGEX = re.compile(".*Trial-(T000...).*")

for filename in os.listdir("./study2"): 
    match = REGEX.match(filename)
    trial = match.groups(1)[0]
    if trial not in TRIALS:
        FILES[trial] = []
        TRIALS.append(trial)
    
    FILES[trial].append(filename)
        
for trial in TRIALS:
    os.mkdir("trials/" + trial)
    
    files = FILES[trial]
    for f in files:
        shutil.copyfile("study2/" + f, "trials/" + trial + "/" + f)               
