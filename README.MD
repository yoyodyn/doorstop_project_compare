TODO:
* DONE - Make branches to compare parameters, with master being one of the defaults
* Make the script an executable command from the bash prompt, should be able to work with virtual environments as well
* DONE - Add a check that the project branch would be a fast forward from the main branch.  Display a warning otherwise.
* Add a check that the project branch is currently checked out.  We need the _doorstop.yml files for the temp folders
* Add support for different publishers.  Currently using the doorstop publisher, but project requirements would be formatted differently, possibly the levels would not get published.
    - should we allow the publisher to be decided form the doorstop.yml file for each document type?  That would make it easier for the overview and table doc types we want to use to be configurable.

Starting a script to get the diff of two branches for a requirements repo created with doorstop.

The goal is to generate the requirements that were add, removed, or changed in the project branch and publish those as a set of requirements that can be pasted into a project requirements document or proposal.

When the project is completed the branch can be merged into the main requirements branch for a living document that is always up to speed.

The script will need to run a version of this git command to get the diff

    git diff --no-prefix -U100 master project/ProjA >diff.txt

The script should use the output of this command, which should be a listing of the yaml files that have changed.
The output will need to be broken up, formatted to remove the "+" and "-" indicators, and in some cases add additional HTML tags to indicate changes.
- looking to make the removed requirement in red color and/or strike-through, but still display it in the final published version
- added lines are currently getting decorated with blue.
- Only normative changes are causing the requirement to be added.
- Only the "text" field is getting decorated.

Would like to be able to run this from the git-bash prompt like other git or doorstop commands.

Should add a check that the project branch parameter is a fast forward from the "master" branch parameter.  
- should it be up to the operator to do the rebase if it is not?  Or should this script attempt to do that automatically.  My first though is that a rebase has too many failure paths to do this automatically.

    