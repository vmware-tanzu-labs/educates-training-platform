package main

import (
	"flag"
	"net"
	"net/http"
	"os"

	"github.com/labstack/echo/middleware"

	"github.com/labstack/echo"
	"github.com/sirupsen/logrus"
)

var logger = logrus.New()

func main() {
	var socketPath string
	flag.StringVar(&socketPath, "socket", "/run/guest-services/backend.sock", "Unix domain socket to listen on")
	flag.Parse()

	_ = os.RemoveAll(socketPath)

	logger.SetOutput(os.Stdout)

	logMiddleware := middleware.LoggerWithConfig(middleware.LoggerConfig{
		Skipper: middleware.DefaultSkipper,
		Format: `{"time":"${time_rfc3339_nano}","id":"${id}",` +
			`"method":"${method}","uri":"${uri}",` +
			`"status":${status},"error":"${error}"` +
			`}` + "\n",
		CustomTimeFormat: "2006-01-02 15:04:05.00000",
		Output:           logger.Writer(),
	})

	logger.Infof("Starting listening on %s\n", socketPath)
	router := echo.New()
	router.HideBanner = true
	router.Use(logMiddleware)
	startURL := ""

	ln, err := listen(socketPath)
	if err != nil {
		logger.Fatal(err)
	}
	router.Listener = ln

	router.GET("/create", start)
	router.GET("/destroy", stop)

	logger.Fatal(router.Start(startURL))
}

func listen(path string) (net.Listener, error) {
	return net.Listen("unix", path)
}

func start(ctx echo.Context) error {
	url := ctx.QueryParam("url")
	w := &Workshop{
		WorkshopDefinitionUrl: url,
		Name:                  "lab-k8s-fundamentals",
		Running:               true,
		WorkshopUrl:           "http://workshop.127-0-0-1.nip.io:10081/dashboard/",
	}
	return ctx.JSON(http.StatusOK, w)
}

func stop(ctx echo.Context) error {
	name := ctx.QueryParam("name")
	w := &Workshop{
		WorkshopDefinitionUrl: "",
		Name:                  name,
		Running:               false,
		WorkshopUrl:           "",
	}
	return ctx.JSON(http.StatusOK, w)
}

type Workshop struct {
	WorkshopDefinitionUrl string `json:"workshopDefinitionUrl"`
	Name                  string `json:"name"`
	Running               bool   `json:"running"`
	WorkshopUrl           string `json:"workshopUrl"`
}
