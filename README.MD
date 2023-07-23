Python script to get the diff of two branches for a requirements repo created with doorstop.
Publish the differences as an html file with highlighting for what was removed and added.

The goal is to generate the requirements that were added, removed, or changed in the project branch and publish those as a set of requirements that can be pasted into a project requirements document or proposal.

When the project is completed the branch can be merged (no-ff) into the main requirements branch for a living document that is always up to speed.

The script runs a version of this git command to get the diff

```git diff --no-prefix -U100 master project/ProjA >diff.txt```

The project branch must be checked out, and for the results to make sense it should be a fast-forward from the current "main" branch

If the project branch has already been merged into the main branch, the diff will use the most recent common ancester as the compare point.

For plantuml or other code blocks in the text of the requirements, the entire code block will be evaluated and both a removed and added block will be published with blue and red border decorations

TODO:
* Add support for different publishers.  Currently hardcoded publisher for each document type.  Discussions on the doorstop github suggest that altering the publishing model to either allow more templating, or subclassing are in the works already.
    - should we allow the publisher to be decided form the .doorstop.yml file for each document type?  That would make it easier for the overview and table doc types we want to use to be configurable.
* Would like to be able to run this from the git-bash prompt like other git or doorstop commands.
* line decorations are still messing up some of the markdown formatting in the text of the requirement.  I suspect this could conflict with general html publishing requirments for header sizes, indenting, etc.
* Add flag to only publish the added/after requirements.  This would still publish the full requirment for files that were changed, but not publish any of the removed lines.  No decorations would be required in this mode.
