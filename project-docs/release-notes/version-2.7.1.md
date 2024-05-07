Version 2.7.1
=============

Bugs Fixed
----------

* If a `SecretCopier` contained multiple rules and a namespace was matched by a
  rule which was in a terminating state, the attempt to create the secret in
  that namespace would fail but not be caught. This meant that any rules which
  followed that rule were not being applied on that pass and would only be
  applied some time later after the terminating namespace had finally been
  deleted. To reduce chance of this occuring, a namespace which is not in the
  active state will be skipped for matching. Also, any unexpected exception
  will be explicitly caught and logged rather than being propogated back to the
  caller.

* In the most recent Fedora base image used by workshop images the `nc` package
  was changed so as to refer to `ncat`, breaking workshops which were used to
  the `netcat` package variant being used. The `nc` alias has been reverted to
  use `netcat` by installing `netcat` package instead of `nc`. The `ncat`
  package is also installed if want newer variant of `nc`, but you will need to
  use the `ncat` command explicitly.

* If the cluster DNS server was slow to start resolving DNS names after a new
  node was started, the session manager could fail on startup and enter crash
  loop back off state. To remedy both session manager and secrets manager now
  ensure DNS is able to resolve cluster control plane DNS name before starting
  up. Startup probes have also been added to these two operators.
