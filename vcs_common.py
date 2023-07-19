"""Common routines related to VCS (git)"""
import subprocess
import sys
import io

from unidiff import PatchSet
from common import logger, PIPE

log = logger(__name__)

def _check_branch_fastforward(main_branch, project_branch):
    # check if the branch being checked can a fast-forward merge.  Log a warning if not.
    # git merge-base --is-ancestor <commit> <commit>
    with subprocess.Popen(['git', 'merge-base', '--is-ancestor', main_branch,
                           project_branch]) as process:
        process.communicate()
        if process.returncode:
            log.warning("Branch %s can not be fast-forwarded to %s " +
                    "comparison may not be accurate until rebased.", main_branch, project_branch)
            return False
    return True

def _check_active_branch(project_branch):
    # git symbolic-ref --short -q HEAD
    with subprocess.Popen(['git', 'symbolic-ref', '--short', '-q', 'HEAD'],
                            stdout=PIPE, stderr=PIPE) as process:
        stdoutput, stderroutput = process.communicate()
        if 'fatal' in stderroutput.decode():
            # Handle error case
            log.fatal("Error getting active branch %s", stderroutput)
            sys.exit()
        if project_branch not in stdoutput.decode():
            log.fatal("Must check out the branch to check %s", project_branch)
            log.fatal("Active branch is %s", stdoutput.decode())
            sys.exit()

def _read_branch_diff(main_branch, project_branch):
    """ this finds the newest common ancester of both branches to base the diff on
        this is done so that even after project install and the project branch is 
        merged into master/production, the original branch can be left in place
        and this method can still be used to find what was changed.  Note that this
        will only work if a merge is done with a --no-ff option so that the branch
        is left as a spur in the history graph
    """
    base_commit = main_branch
    # git merge-base project/ProjA master
    with subprocess.Popen(['git', 'merge-base', project_branch, main_branch],
                          stdout=PIPE, stderr=PIPE) as process:
        stdoutput, stderroutput = process.communicate()
        if 'fatal' in stderroutput.decode():
            # Handle error case
            log.fatal("Error process merge-base: %s", stderroutput)
            sys.exit()
        base_commit = stdoutput.decode().strip()

    # get the diff between the two branches.  Save the output.
    # git diff --no-prefix -U100 master project/ProjA
    with subprocess.Popen(['git', 'diff', '--no-prefix', '-U10000', base_commit, project_branch],
                            stdout=PIPE, stderr=PIPE) as process:
        stdoutput, stderroutput = process.communicate()
        if 'fatal' in stderroutput.decode():
            # Handle error case
            log.fatal("Error process diff: %s", stderroutput)
            sys.exit()

        # using PatchSet to parse the diff output easily
        patch_set = PatchSet(io.BytesIO(stdoutput), encoding='utf-8')

        return patch_set
