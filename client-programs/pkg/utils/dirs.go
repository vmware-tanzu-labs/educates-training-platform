package utils

import (
	"path"

	"github.com/adrg/xdg"
)

func GetEducatesHomeDir() string {
	return path.Join(xdg.DataHome, "educates")
}
