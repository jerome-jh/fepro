#!/bin/bash

cat urls.txt | xargs -l -- wget -nc
