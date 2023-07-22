TODO:
* DONE - Let the linked OVR document type have special meaning and put the contents at the top of the main published page.
* DONE - Make branches to compare parameters, with master being one of the defaults
* Make the script an executable command from the bash prompt, should be able to work with virtual environments as well
* DONE - Add a check that the project branch would be a fast forward from the main branch.  Display a warning otherwise.
* DONE - Add a check that the project branch is currently checked out.  We need the _doorstop.yml files for the temp folders
* Add support for different publishers.  Currently using the doorstop publisher, but project requirements would be formatted differently, possibly the levels would not get published.
    - should we allow the publisher to be decided form the .doorstop.yml file for each document type?  That would make it easier for the overview and table doc types we want to use to be configurable.

Starting a script to get the diff of two branches for a requirements repo created with doorstop.

The goal is to generate the requirements that were add, removed, or changed in the project branch and publish those as a set of requirements that can be pasted into a project requirements document or proposal.

When the project is completed the branch can be merged (no-ff) into the main requirements branch for a living document that is always up to speed.

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

Should we compare to the master branch, or the most recent common ancester of both branches?
- if we use the master branch, then it would show the current changes/differences, but that could backpedal some changes
- if we use the common ancester then it should work for both current and historyical usage.
  - as long as "current" the project branch is a FF from master.

Had to remove the color coding for now, which makes telling what was added/removed near impossible.
The formatting was getting added during the evaluation stage and was messing up the MD formatting, so the ending html was not correct.
There is a lot of posibilities for formatting in the requirement files using markdown, latex, and graphs.

Think we are going to have to parse for the plantuml start and end, so we can not try to color that.  But still color all the other lines.  Will need to only check for added or context lines, and ignore removed lines for the plantuml start/stop.

The "```" start and end for a code block.  Maybe we should treat the code blocks as a unit.  Can we have the added and removed parsed separately and show both?  First need to determine if there was anything added or removed inside the code block.  If not, then we don't have to change anything.  If the entire code block was added then there is no "before" to include.  If the entire code block was removed, then there is no "after" to include.  If there was code added and removed, then we need to include a complete before and after in separate code blocks.  Or should we only worry about this if there was a plantuml in the code block?

Will need to keep track as we go through adding context/removed lines to "A", and context/added lines to "B".  Then we can either keep a flag to indicated lines were different, or compare the strings at the end to see if they are the same.
