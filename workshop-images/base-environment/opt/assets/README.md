This is a place holder directory for where workshop files are initially
downloaded before being moved into their final locations. This directory needs
to exist in the workshop image from the outset so it has correct permissions.
If it doesn't, and files are added under it via volume mounts, the directory
may not be created with any write access to the workshop user.
