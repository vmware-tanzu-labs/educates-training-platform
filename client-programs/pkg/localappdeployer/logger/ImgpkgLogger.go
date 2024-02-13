package logger

import (
	"fmt"

	imgpkgv1 "carvel.dev/imgpkg/pkg/imgpkg/v1"
)

type ImgpkgLoggerImpl struct{}

var _ imgpkgv1.Logger = &ImgpkgLoggerImpl{}

func NewImgpkgLogger() *ImgpkgLoggerImpl {
	return &ImgpkgLoggerImpl{}
}

/**
 * This is a local implementation of the imgpkgv1.Logger interface found at:
 * "carvel.dev/imgpkg/pkg/imgpkg/v1/pull.go"
 */
//type ImgpkgLogger struct{}

func (l *ImgpkgLoggerImpl) Debugf(format string, args ...interface{}) {
	fmt.Printf("[DEBUG] "+format+"\n", args...)
}

func (l *ImgpkgLoggerImpl) Tracef(format string, args ...interface{}) {
	fmt.Printf("[INFO] "+format+"\n", args...)
}

func (l *ImgpkgLoggerImpl) Warnf(format string, args ...interface{}) {
	fmt.Printf("[WARN] "+format+"\n", args...)
}

func (l *ImgpkgLoggerImpl) Errorf(format string, args ...interface{}) {
	fmt.Printf("[ERROR] "+format+"\n", args...)
}

func (l *ImgpkgLoggerImpl) Logf(format string, args ...interface{}) {
	fmt.Printf("[ERROR] "+format+"\n", args...)
}

type ImgpkgNoopLoggerImpl struct{}

var _ imgpkgv1.Logger = &ImgpkgNoopLoggerImpl{}

func NewImgpkgNoopLoggerImpl() *ImgpkgNoopLoggerImpl {
	return &ImgpkgNoopLoggerImpl{}
}

func (l *ImgpkgNoopLoggerImpl) Debugf(format string, args ...interface{}) {
}

func (l *ImgpkgNoopLoggerImpl) Tracef(format string, args ...interface{}) {
}

func (l *ImgpkgNoopLoggerImpl) Warnf(format string, args ...interface{}) {
}

func (l *ImgpkgNoopLoggerImpl) Errorf(format string, args ...interface{}) {
}

func (l *ImgpkgNoopLoggerImpl) Logf(format string, args ...interface{}) {
}
