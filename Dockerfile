FROM node:current
RUN mkdir /work
WORKDIR /work
RUN curl https://codeload.github.com/kdvolder/eduk8s-vscode-helper/zip/master > extension.zip
RUN unzip extension.zip 
RUN rm extension.zip
RUN cd eduk8s-vscode-helper-master && npm install && npm run vsce-package && ls -la *.vsix
#RUN npm run vsce-package
