"""Script file as a starting point to get the diff from two branches in the requirements repo 
    and try to publish a set of project specifications."""

import subprocess
import os
import shutil
import io
import logging
import doorstop

from unidiff import PatchSet

logging.basicConfig(filename='startfile.log', filemode='w', level=1)

logger = logging.getLogger
log = logger(__name__)

PIPE = subprocess.PIPE
mainbranch = 'master'               # eventually the branch names should be parameters
projectbranch = 'project/ProjA'

# Printing the current working directory
log.info("The Current working directory is: {0}".format(os.getcwd()))

# should not have to change the working directory once deployed as this should be run 
# from the requirements repo folder
# Changing the current working directory
os.chdir('C:\\Projects\\QMSI\\RequirementsManagement\\req_test')

# Print the current working directory
log.info("The Current working directory now is: {0}".format(os.getcwd()))

# place to put the files for generating the alternate project requirement "documents"
# This could also be a passed in parameter with a default to the branch name
tempPath = projectbranch.replace('/', '_')

# first delete the temp path if it exists
if os.path.isdir(tempPath):
    shutil.rmtree(tempPath)
# create the temp folder
os.makedirs(tempPath)

# get the diff between the two branches.  Save the output.
# git diff --no-prefix -U100 master project/ProjA 
process = subprocess.Popen(['git', 'diff', '--no-prefix', '-U1000', mainbranch, projectbranch], 
                           stdout=PIPE, stderr=PIPE)
stdoutput, stderroutput = process.communicate()

# if 'fatal' in str:
#     # Handle error case
#     print("failed")
#     print(stderroutput)
#     exit()

# using PatchSet to parse the diff output easily
patch_set = PatchSet(io.BytesIO(stdoutput), encoding='utf-8')

# markup lines that have been removed
removedLine = "  <span style=\"color:red\"><del>{0}</del></span>"

for patched_file in patch_set:
    currentItem = []
    file_path = patched_file.path  # file name
    file_name = os.path.split(file_path)[1]
    log.info('file name :' + file_path)

    # check if we need to copy the .doorstop.yml file over to the temp location
    docPath = os.path.dirname(file_path)
    tempDocPath = os.path.join(tempPath, docPath)

    tempDocConfig = os.path.join(tempDocPath, ".doorstop.yml")

    if not os.path.exists(tempDocPath):
        os.makedirs(tempDocPath, exist_ok=True)
    if not os.path.isfile(tempDocConfig):
        shutil.copy(os.path.join(docPath, ".doorstop.yml"), tempDocConfig)

    intext = False

    for hunk in patched_file:
        for line in hunk:
            # going to accept context or added lines until we get to the "text"
            # yaml files depend on indentation.  So if the first character isn't blank, then we aren't in the "text" section anymore
            if not line.value.startswith(" "):
                intext = False

            # if we found the text section set the bool
            if line.value.startswith("text:"):
                intext = True

            if intext:
                #<span style="color:red"><del></del></span>
                if line.is_removed:
                    currentItem.append(removedLine.format(line.value.strip()))
                else:
                    currentItem.append(line.value)
                continue

            if line.is_added or line.is_context:
                currentItem.append(line.value)
        
    whatisThis = doorstop.common.load_yaml(''.join(currentItem), '')
    doorstop.common.write_lines(currentItem, os.path.join(tempDocPath, file_name), "")
    
document = doorstop.Document(os.path.join(os.path.abspath(tempPath), "req"), None)

# Create the output path only.
if os.path.isdir("public_Project"):
    shutil.rmtree("public_Project")
if not os.path.exists("public_Project"):
    os.makedirs("public_Project", exist_ok=True)

doorstop.publisher.publish(document, "public_Project/req.html", ".html", toc=False)
