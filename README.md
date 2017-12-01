# openAWS

This script identifies any security groups that are open to the world (0.0.0.0/0).

By default it only checks security groups attached to running instances. The documentation on how to change this is in the comments in the script

## Prerequisites
```
pip install -r requirements.txt
```
* Ensure you have setup AWS config in `~/.aws/config` and `~/.aws/credentials`
** See http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

## To run
```
python openAWS.py
```

To do:
* take command line parameters
* implement in Lamda
** Keep a JSON list in S3 of known SGs open to the world
** Compare known list to the new list on lambda execution.
** If new SGs are found, send an alert to admin

