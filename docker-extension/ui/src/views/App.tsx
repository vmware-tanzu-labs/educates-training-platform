import React, { useEffect, useState } from "react";
import Button from "@mui/material/Button";
import { createDockerDesktopClient } from "@docker/extension-api-client";
import { Box, Grid, CircularProgress, Link, Stack, TextField, Typography } from "@mui/material";
import BottomIntroPane from "../components/BottomIntroPane/BottomIntroPane";
import WorkshopsTable from "../components/WorkshopsTable/WorkshopsTable";
import { handleGoTo } from "../common/goto";
import { NullWorkshop, Workshop } from "../common/types";
import { isValidURL } from "../common/validations";

const sampleWorkshopURL =
  "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml";
const workshopUrlPrefix = "http://workshop.127-0-0-1.nip.io:";

// Note: This line relies on Docker Desktop's presence as a host application.
// If you're running this React app in a browser, it won't work properly.
const client = createDockerDesktopClient();

function useDockerDesktopClient() {
  return client;
}

const firstPossiblePort = 10081;
const lastPossiblePort = 10181;

function firstAvailablePort(workshops: Workshop[]): string {
  for (var i = firstPossiblePort; i < lastPossiblePort; i++) {
    if (workshops.filter(workshop => workshop.url === workshopUrlPrefix + i).length == 0) {
      return "" + i;
    }
  }
  return "" + lastPossiblePort;
}

export function App() {
  const [url, setUrl] = React.useState<string>("");
  const [port, setPort] = React.useState<string>("" + firstPossiblePort);
  const [queryingBackend, setQueryingBackend] = React.useState<boolean>(false);
  const [isUrlError, setIsUrlError] = React.useState<boolean>(false);
  const ddClient = useDockerDesktopClient();
  const [workshops, setWorkshops] = React.useState<Workshop[]>([]);

  useEffect(() => {
    setIsUrlError(false);
  }, [url]);

  useEffect(() => {
    setPort(firstAvailablePort(workshops));
  }, [workshops]);

  useEffect(() => {
    let interval: any = null;
    if (interval != undefined) clearInterval(interval);
    if (interval == undefined) {
      interval = setInterval(() => {
        list();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, []);

  const list = async () => {
    console.log("list");
    ddClient.extension.vm?.service
      ?.get("/workshop/list")
      .then((result: any) => {
        setWorkshops(result);
      })
      .catch((err: any) => {
        console.log(err);
      });
  };

  const start = async () => {
    if (isValidURL(url)) {
      console.log("start");
      setQueryingBackend(true);
      ddClient.extension.vm?.service
        ?.get("/workshop/deploy?url=" + encodeURIComponent(url) + "&port=" + port)
        .then((result: any) => {
          setQueryingBackend(false);
        })
        .catch((err: any) => {
          console.log(err);
          setQueryingBackend(false);
        });
    } else {
      setIsUrlError(true);
    }
  };

  const stop = async (name: string) => {
    console.log("stop: " + name);
    // let index = workshops.findIndex(workshop => workshop.name == name);
    // workshops[index].status = "Stopping";
    ddClient.extension.vm?.service
      ?.get("/workshop/delete?name=" + name)
      .then((result: any) => {
        console.log("OK");
      })
      .catch((err: any) => {
        console.log(err);
      });
  };

  return (
    <>
      {/* <Stack direction="column" alignItems="start" spacing={3} sx={{ mt: 1 }}> */}
      <Grid container rowSpacing={1} columnSpacing={{ xs: 2 }}>
        <Grid item xs={12} sx={{ maxHeight: "15vh" }}>
          <Typography variant="h3">Educates Training Platform</Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            //  sx={{ mt: 2 }}
          >
            Run an Educates Training Platform workshop locally by providing the workshop definition
            raw URL (e.g.{" "}
            <Link
              href="#"
              onClick={() => {
                handleGoTo(sampleWorkshopURL);
              }}
            >
              example workshop
            </Link>
            {"   "}
            <Link
              href="#"
              onClick={() => {
                setUrl(sampleWorkshopURL);
              }}
            >
              (Try it out)
            </Link>
            )
          </Typography>
        </Grid>
        <Grid container alignItems="center" margin={2} sx={{ maxHeight: "10vh" }}>
          <Grid item xs={9}>
            <TextField
              error={isUrlError}
              // disabled={workshop?.status == "Running" ? true : false}
              helperText={isUrlError ? "Url is Invalid" : ""}
              label="Workshop definition raw url"
              sx={{ width: "100%" }}
              variant="outlined"
              value={url ?? ""}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setUrl(event.target.value);
              }}
            />
          </Grid>
          <Grid item xs={1}>
            <TextField
              label="port"
              sx={{ width: "100%" }}
              variant="outlined"
              value={port ?? ""}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setPort(event.target.value);
              }}
            />
          </Grid>
          <Grid item xs={2}>
            <Box sx={{ m: 1, position: "relative" }}>
              <Button variant="contained" disabled={queryingBackend} onClick={start}>
                Start
              </Button>
              {queryingBackend && (
                <CircularProgress
                  size={24}
                  sx={{
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    marginTop: "-12px",
                    marginLeft: "-12px",
                  }}
                />
              )}
            </Box>
          </Grid>
        </Grid>
        <Grid item xs={12}>
          <WorkshopsTable rows={workshops} onStop={stop} />
        </Grid>
      </Grid>
      <BottomIntroPane />
    </>
  );
}
