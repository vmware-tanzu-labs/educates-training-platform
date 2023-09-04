import React, { useEffect, useState } from "react";
import Button from "@mui/material/Button";
import { createDockerDesktopClient } from "@docker/extension-api-client";
import { Box, CircularProgress, Link, Stack, TextField, Typography } from "@mui/material";
import BottomIntroPane from "../components/BottomIntroPane/BottomIntroPane";
import { handleGoTo } from "../common/goto";
import { NullWorkshop, Workshop } from "../common/types";
import { isValidURL } from "../common/validations";

const sampleWorkshopURL =
  "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml";

// Note: This line relies on Docker Desktop's presence as a host application.
// If you're running this React app in a browser, it won't work properly.
const client = createDockerDesktopClient();

function useDockerDesktopClient() {
  return client;
}

export function App() {
  const [workshop, setWorkshop] = React.useState<Workshop>(NullWorkshop);
  const [url, setUrl] = React.useState<string>("");
  const [queryingBackend, setQueryingBackend] = React.useState<boolean>(false);
  const [isUrlError, setIsUrlError] = React.useState<boolean>(false);
  const ddClient = useDockerDesktopClient();

  useEffect(() => {
    setIsUrlError(false);
  }, [url]);

  useEffect(() => {
    console.log(workshop);
  }, [workshop]);

  const start = async () => {
    if (isValidURL(url)) {
      console.log("start");
      setQueryingBackend(true);
      ddClient.extension.vm?.service
        ?.get("/workshop/deploy?url=" + encodeURIComponent(url) + "&port=10081")
        .then((result: any) => {
          setWorkshop(result);
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
  const stop = async () => {
    console.log("stop");
    setQueryingBackend(true);
    ddClient.extension.vm?.service
      ?.get("/workshop/delete?name=" + workshop?.session)
      .then((result: any) => {
        setWorkshop(result);
        setQueryingBackend(false);
        setUrl("");
      })
      .catch((err: any) => {
        console.log(err);
        setQueryingBackend(false);
        setUrl("");
      });
  };

  return (
    <>
      <Typography variant="h3">Educates Training Platform</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
        Run an Educates Training Platform workshop locally by providing the workshop definition raw
        URL (e.g.{" "}
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
      {/* <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
        Pressing the below button will trigger a request to the backend. Its response will appear in
        the textarea.
      </Typography> */}
      <Stack direction="column" alignItems="start" spacing={2} sx={{ mt: 6 }}>
        <Stack direction="row" alignItems="start" spacing={2} sx={{ mt: 6 }}>
          <TextField
            error={isUrlError}
            disabled={workshop?.status == "Running" ? true : false}
            helperText={isUrlError ? "Url is Invalid" : ""}
            label="Workshop definition raw url"
            sx={{ width: 700 }}
            variant="outlined"
            minRows={1}
            maxRows={1}
            value={url ?? ""}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setUrl(event.target.value);
            }}
          />
          {(!workshop?.status || workshop?.status == "Stopped") && (
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
          )}
          {(workshop?.status == "Running") && (
            <Box sx={{ m: 1, position: "relative" }}>
              <Button variant="contained" disabled={queryingBackend} onClick={stop}>
                Stop
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
          )}
        </Stack>
        {workshop?.status && workshop?.status != "Stopped" && (
          <>
            <Stack direction="row" alignItems="start" spacing={2} sx={{ mt: 2 }}>
              <Typography variant="body1">Workshop: {workshop.session}</Typography>
            </Stack>
            <Stack direction="row" alignItems="start" spacing={2} sx={{ mt: 6 }}>
              <Typography variant="body1">
                Url: {"     "}
                <Link
                  href="#"
                  onClick={() => {
                    handleGoTo(workshop?.url);
                  }}
                >
                  {workshop?.url}
                </Link>
              </Typography>
            </Stack>
          </>
        )}
      </Stack>
      <BottomIntroPane />
    </>
  );
}
