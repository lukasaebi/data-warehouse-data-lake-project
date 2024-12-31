#!/bin/bash

set -e # Exit immediately if a command fails

rm -f ~/.aws/credentials

echo "Enter AWS credentials (including [default] and all the credential keys), followed by Enter + Ctrl-D when done:"

aws_credentials=$(</dev/stdin)

printf "%s\n" "$aws_credentials" > ~/.aws/credentials

echo "AWS credentials file created successfully."