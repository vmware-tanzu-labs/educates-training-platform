import React, { useEffect, useState } from "react";
import Button from "@mui/material/Button";
import { createDockerDesktopClient } from "@docker/extension-api-client";
import { Link, Stack, TextField, Typography } from "@mui/material";
import BottomIntroPane from "../components/BottomIntroPane/BottomIntroPane";
import { handleGoTo } from "../common/goto";
import { NullWorkshop, Workshop } from "../common/types";
import { isValidURL } from "../common/validations";

const sampleWorkshopURL =
  "https://raw.githubusercontent.com/vmware-tanzu-labs/lab-k8s-fundamentals/main/resources/workshop.yaml";

// Note: This line relies on Docker Desktop's presence as a host application.
// If you're running this React app in a browser, it won't work properly.
const client = createDockerDesktopClient();

function useDockerDesktopClient() {
  return client;
}

export function App() {
  const [workshop, setWorkshop] = React.useState<Workshop>(NullWorkshop);
  const [url, setUrl] = React.useState<string>("");
  const ddClient = useDockerDesktopClient();

  useEffect(() => {
    console.log(workshop);
  }, [workshop]);

  const start = async () => {
    if (isValidURL(url)) {
      console.log("start");
      // setWorkshopUrl("this is the url");
      ddClient.extension.vm?.service
        ?.get("/create?url=" + url)
        .then((result: any) => {
          setWorkshop(result);
        })
        .catch((err: any) => {
          console.log(err);
        });
    } else {
      alert("Url is not valid");
    }
  };
  const stop = async () => {
    console.log("stop");
    // setWorkshopUrl("");
    ddClient.extension.vm?.service
      ?.get("/destroy?name=" + workshop?.name)
      .then((result: any) => {
        setWorkshop(result);
      })
      .catch((err: any) => {
        console.log(err);
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
            label="Workshop definition raw url"
            sx={{ width: 400 }}
            variant="outlined"
            minRows={1}
            maxRows={1}
            value={url ?? ""}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setUrl(event.target.value);
            }}
          />
          {!workshop?.running && (
            <Button variant="contained" onClick={start}>
              Start
            </Button>
          )}
          {workshop.running && (
            <>
              <Button variant="contained" onClick={stop}>
                Stop
              </Button>
              <Button
                variant="contained"
                onClick={() => {
                  workshop?.workshopUrl !== undefined ? handleGoTo(workshop?.workshopUrl) : null;
                }}
              >
                Open
              </Button>
            </>
          )}
        </Stack>
        {workshop.running && (
          <>
            <Typography variant="body1">Workshop: {workshop.name}</Typography>
            <Typography variant="body1">
              Url: {"     "}
              <Link
                href="#"
                onClick={() => {
                  handleGoTo(workshop?.workshopUrl);
                }}
              >
                {workshop?.workshopUrl}
              </Link>
            </Typography>
          </>
        )}
      </Stack>
      <BottomIntroPane />
    </>
  );
}
