// Copyright 2020 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package logger

import (
	"fmt"
	"time"

	"github.com/cppforlife/go-cli-ui/ui"
)

const (
	loggerLevelError = "error"
	loggerLevelInfo  = "info"
	loggerLevelDebug = "debug"
)

type KctrlUILogger struct {
	prefix string
	ui     ui.UI
	debug  bool
}

var _ KctrlLogger = &KctrlUILogger{}

func NewUILogger(ui ui.UI) *KctrlUILogger { return &KctrlUILogger{"", ui, false} }

func (l *KctrlUILogger) SetDebug(debug bool) { l.debug = debug }

func (l *KctrlUILogger) Error(msg string, args ...interface{}) {
	l.ui.BeginLinef(l.msg(loggerLevelError, msg), args...)
}

func (l *KctrlUILogger) Info(msg string, args ...interface{}) {
	l.ui.BeginLinef(l.msg(loggerLevelInfo, msg), args...)
}

func (l *KctrlUILogger) Debug(msg string, args ...interface{}) {
	if l.debug {
		l.ui.BeginLinef(l.msg(loggerLevelDebug, msg), args...)
	}
}

func (l *KctrlUILogger) DebugFunc(name string) FuncLogger {
	funcLogger := &KctrlUIFuncLogger{name, time.Now(), l.NewPrefixed(name)}
	funcLogger.Start()
	return funcLogger
}

func (l *KctrlUILogger) NewPrefixed(name string) KctrlLogger {
	if len(l.prefix) > 0 {
		name = l.prefix + name
	}
	name += ": "
	return &KctrlUILogger{name, l.ui, l.debug}
}

func (l *KctrlUILogger) msg(level, msg string) string {
	ts := time.Now().Format("03:04:05PM")
	return fmt.Sprintf("%s: %s: %s%s\n", ts, level, l.prefix, msg)
}

type KctrlUIFuncLogger struct {
	name      string
	startTime time.Time
	logger    KctrlLogger
}

var _ FuncLogger = &KctrlUIFuncLogger{}

func (l *KctrlUIFuncLogger) Start()  { l.logger.Debug("start") }
func (l *KctrlUIFuncLogger) Finish() { l.logger.Debug("end (%s)", time.Now().Sub(l.startTime)) }
