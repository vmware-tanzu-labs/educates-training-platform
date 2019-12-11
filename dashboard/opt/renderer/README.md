# Homeroom Renderer

This application renders content in asciidoc and markdown format in a Homeroom dashboard application.

## Run locally

If you want to run the renderer locally, you can just use a sample content.

```bash
git clone https://github.com/openshift-labs/workshop-dashboard.git
cd dashboard/renderer
npm install
node download.js /tmp/kk https://raw.githubusercontent.com/GrahamDumpleton/starter-guides/ocp-4.1-homeroom/workshop workshop-java.yaml
WORKSHOP_DIR=/tmp/workshop WORKSHOP_FILE=workshop.yaml npm start
```

Then, open your browser at http://localhost:8080
