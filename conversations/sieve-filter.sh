#! /bin/bash

url=${@#*\@}
key=${@%\@*}
curl ${url} -d key=${key} -d -
