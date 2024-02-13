// Copyright 2020 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package logger

import "fmt"

type KctrlStdoutLogger struct{}

var _ KctrlLogger = KctrlStdoutLogger{}

func NewKctrlStdoutLogger() KctrlStdoutLogger { return KctrlStdoutLogger{} }

func (l KctrlStdoutLogger) Error(msg string, args ...interface{}) {
	fmt.Printf("[INFO] "+msg+"\n", args...)
}
func (l KctrlStdoutLogger) Info(msg string, args ...interface{}) {
	fmt.Printf("[INFO] "+msg+"\n", args...)
}
func (l KctrlStdoutLogger) Debug(msg string, args ...interface{}) {
	fmt.Printf("[INFO] "+msg+"\n", args...)

}
func (l KctrlStdoutLogger) DebugFunc(name string) FuncLogger    { return NoopFuncLogger{} }
func (l KctrlStdoutLogger) NewPrefixed(name string) KctrlLogger { return l }

type NoopFuncLogger struct{}

var _ FuncLogger = NoopFuncLogger{}

func (l NoopFuncLogger) Finish() {}
