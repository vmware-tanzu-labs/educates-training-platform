/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"fmt"
	"os/exec"
	"runtime"

	"github.com/spf13/cobra"
)

func NewDocsOpenCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "open",
		Short: "Open browser on package documentation",
		RunE: func(_ *cobra.Command, _ []string) error {
			var err error

			const url = "https://docs.educates.dev/"

			switch runtime.GOOS {
			case "linux":
				err = exec.Command("xdg-open", url).Start()
			case "windows":
				err = exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
			case "darwin":
				err = exec.Command("open", url).Start()
			default:
				err = fmt.Errorf("unsupported platform")
			}

			return err
		},
	}

	return c
}
