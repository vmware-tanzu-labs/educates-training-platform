import { Box, Button, Link, Stack, Typography } from "@mui/material";
import { handleGoTo } from "../../common/goto";

export default function BottomIntroPane() {
  const docsURL = "https://docs.educates.dev",
    slackURL = "slack.com",
    demoURL = "https://docs.educates.dev/project-details/sample-screenshots",
    githubURL = "https://github.com/vmware-tanzu-labs/educates-training-platform";
  return (
    <Box
      position="absolute"
      bottom="50px"
      width="90%"
      sx={{ py: 2, px: 2, borderRadius: 4, boxShadow: 3, height: "20vh" }}
    >
      <Stack
        direction="row"
        sx={{
          display: "flex",
          justifyContent: "space-between",
          height: "100%",
        }}
      >
        <Stack direction="column">
          <Box>
            <Typography
              variant="h4"
              textAlign="left"
              sx={{
                px: 2,
              }}
            >
              New to Educates Training Platform?
            </Typography>
          </Box>
          <Box>
            <Typography
              variant="body1"
              textAlign="left"
              sx={{
                px: 2,
                width: "100%",
                height: "100%",
                textOverflow: "ellipsis",
                overflow: "hidden",
              }}
            >
              Not sure if Educates Training Platform is right for you? Check out the{" "}
              <Link
                href="#"
                onClick={() => {
                  handleGoTo(docsURL);
                }}
              >
                docs
              </Link>
              , join us on the{" "}
              <Link
                href="#"
                onClick={() => {
                  handleGoTo(slackURL);
                }}
              >
                Kubernetes slack
              </Link>{" "}
              or visit our{" "}
              <Link
                href="#"
                onClick={() => {
                  handleGoTo(githubURL);
                }}
              >
                GitHub page
              </Link>
            </Typography>
          </Box>
        </Stack>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            width: "20%",
            justifyContent: "center",
          }}
        >
          <Button
            variant="outlined"
            onClick={() => {
              handleGoTo(demoURL);
            }}
          >
            Watch demo
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
