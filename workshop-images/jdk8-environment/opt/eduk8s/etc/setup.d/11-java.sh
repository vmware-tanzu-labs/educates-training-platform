#!/bin/sh

SETTINGS=$HOME/.local/share/code-server/User/settings.json

jq -M '. + {
    "java.configuration.checkProjectSettingsExclusions": false,
    "java.help.firstView": "overview",
    "java.semanticHighlighting.enabled": false,
    "files.exclude": {
        "**/.classpath": true,
        "**/.project": true,
        "**/.settings": true,
        "**/.factorypath": true
    }
}' $SETTINGS > $SETTINGS.$$

mv $SETTINGS.$$ $SETTINGS

