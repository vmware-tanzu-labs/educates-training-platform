// Copyright 2022 The Educates Authors.

package cmd

/*
Project information.
*/
type ProjectInfo struct {
	Version string
}

/*
Populate project information.

NOTE: This is expected to be provided with values corresponding to any defaults
but where they could have been overridden at compile time as part of a release
of the Educates CLI.
*/
func NewProjectInfo(version string) ProjectInfo {
	return ProjectInfo{Version: version}
}
