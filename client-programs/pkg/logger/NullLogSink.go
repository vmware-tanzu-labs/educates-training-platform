package logger

import (
	"github.com/go-logr/logr"
)

// NullLogSink is a logr.Logger that does nothing.
type NullLogSink struct{}

var _ logr.LogSink = NullLogSink{}

// Init implements logr.LogSink.
func (log NullLogSink) Init(logr.RuntimeInfo) {
}

// Info implements logr.InfoLogger.
func (NullLogSink) Info(_ int, _ string, _ ...interface{}) {
	// Do nothing.
}

// Enabled implements logr.InfoLogger.
func (NullLogSink) Enabled(level int) bool {
	return false
}

// Error implements logr.Logger.
func (NullLogSink) Error(_ error, _ string, _ ...interface{}) {
	// Do nothing.
}

// WithName implements logr.Logger.
func (log NullLogSink) WithName(_ string) logr.LogSink {
	return log
}

// WithValues implements logr.Logger.
func (log NullLogSink) WithValues(_ ...interface{}) logr.LogSink {
	return log
}
