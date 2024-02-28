package logger

import (
	"fmt"
	"time"

	kapp "github.com/vmware-tanzu/carvel-kapp/pkg/kapp/logger"
)

const (
	loggerLevelError = "error"
	loggerLevelInfo  = "info"
	loggerLevelDebug = "debug"
)

type KappLogger struct {
	prefix string
	debug  bool
}

var _ kapp.Logger = &KappLogger{}

func NewKappLogger() *KappLogger { return &KappLogger{"", false} }

// Debug implements logger.Logger.
func (k *KappLogger) Debug(msg string, args ...interface{}) {
	if k.debug {
		k.msg(loggerLevelDebug, msg)
	}
}

// DebugFunc implements logger.Logger.
func (k *KappLogger) DebugFunc(name string) kapp.FuncLogger {
	funcLogger := &KappFuncLogger{name, time.Now(), k.NewPrefixed(name)}
	funcLogger.Start()
	return funcLogger
}

// Error implements logger.Logger.
func (k *KappLogger) Error(msg string, args ...interface{}) {
	k.msg(loggerLevelError, msg)
}

// Info implements logger.Logger.
func (k *KappLogger) Info(msg string, args ...interface{}) {
	k.msg(loggerLevelInfo, msg)
}

// NewPrefixed implements logger.Logger.
func (k *KappLogger) NewPrefixed(name string) kapp.Logger {
	if len(k.prefix) > 0 {
		name = k.prefix + name
	}
	name += ": "
	return &KappLogger{name, k.debug}
}

func (k *KappLogger) msg(level, msg string) string {
	ts := time.Now().Format("03:04:05PM")
	return fmt.Sprintf("%s: %s: %s%s\n", ts, level, k.prefix, msg)
}

type KappFuncLogger struct {
	name      string
	startTime time.Time
	logger    kapp.Logger
}

var _ kapp.FuncLogger = &KappFuncLogger{}

func (l *KappFuncLogger) Start()  { l.logger.Debug("start") }
func (l *KappFuncLogger) Finish() { l.logger.Debug("end (%s)", time.Since(l.startTime)) }
