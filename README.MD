Starting a script to get the diff of two branches for a requirements repo created with doorstop.

The goal is to generate the requirements that were add, removed, or changed in the project branch and publish those as a set of requirements that can be pasted into a project requirements document or proposal.

When the project is completed the branch can be merged into the main requirements branch for a living document that is always up to speed.

The script will need to run a version of this git command to get the diff

    git diff --no-prefix -U100 master project/ProjA >diff.txt

The script should use the output of this command, which should be a listing of the yaml files that have changed.
The output will need to be broken up, formatted to remove the "+" and "-" indicators, and in some cases add additional HTML tags to indicate changes.
- looking to make the removed requirment in red color and/or strike-through, but still display it in the final published version

Would like to be able to run this from the git-bash prompt like other git or doorstop commands.

Should add a check that the project branch parameter is a fast forward from the "master" branch parameter.  
    - should it be up to the operator to do the rebase if it is not?  Or should this script attempt to do that automatically.  My first though is that a rebase has too many failure paths to do this automatically.

    