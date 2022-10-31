// Copyright 2022 The Educates Authors.

package cmd

type ProjectInfo struct {
	Version string
}

func NewProjectInfo(version string) ProjectInfo {
	return ProjectInfo{Version: version}
}
