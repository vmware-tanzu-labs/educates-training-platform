import { createDockerDesktopClient } from "@docker/extension-api-client";

const client = createDockerDesktopClient();

function useDockerDesktopClient() {
  return client;
}

export const handleGoTo = async (url: string) => {
  const ddClient = useDockerDesktopClient();
  console.log("Open external: " + url);
  ddClient.host.openExternal(url);
};
