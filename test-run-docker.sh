docker build -t eduk8s-vscode-helper .
docker run --rm -p 10085:10085 -p 10011:10011 eduk8s-vscode-helper:latest