package logger

import (
	imgpkgv1 "carvel.dev/imgpkg/pkg/imgpkg/v1"
)

type NullLogger struct{}

var _ imgpkgv1.Logger = &NullLogger{}

func NewNullLogger() *NullLogger {
	return &NullLogger{}
}

/* From imgpkgv1.Logger */
func (l *NullLogger) Debugf(format string, args ...interface{}) {
	//fmt.Printf("[DEBUG] "+format+"\n", args...)
}

/* From imgpkgv1.Logger */
func (l *NullLogger) Tracef(format string, args ...interface{}) {
	//fmt.Printf("[INFO] "+format+"\n", args...)
}

/* From imgpkgv1.Logger */
func (l *NullLogger) Warnf(format string, args ...interface{}) {
	//fmt.Printf("[WARN] "+format+"\n", args...)
}

/* From imgpkgv1.Logger */
func (l *NullLogger) Errorf(format string, args ...interface{}) {
	//fmt.Printf("[ERROR] "+format+"\n", args...)
}

/* From imgpkgv1.Logger */
func (l *NullLogger) Logf(format string, args ...interface{}) {
	//fmt.Printf("[ERROR] "+format+"\n", args...)
}
