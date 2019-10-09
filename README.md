forge-bridge
============

1) Create a 'linux' subdir or symlink with a checked out linux source tree.

2) Adjust the parameters at the top of forge-bridge.py

3) Run forge-brigde.py. It will create branches with series from the mailing list applied
   to the specified tree, and push them to a remote of your choice. It will ping the API
   every few minutes to check for new ones.
