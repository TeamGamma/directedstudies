#!/bin/bash

set -e

LOG_FOLDER=$(dirname $0)/../workloads/logs
#TSUNG_COMMAND=$(dirname $0)/fake_tsung
TSUNG_COMMAND=tsung
REMOTE_FOLDER="mustafa@doteight.com:~/tsung_real_logs"
TSUNG_CONFIGURATION=$1
NUM_RUNS=$2
LABEL=$3

if [ $# -lt 2 ]
then
  echo "Usage: `basename $0` {tsung.conf} {number of times to run} [optional label]"
  exit 1
fi

if ! [ -d $LOG_FOLDER ]; then
  echo "Log folder $LOG_FOLDER does not exist!"
  exit 1
fi

if ! [ -f $TSUNG_CONFIGURATION ]; then
  echo "Configuration file $TSUNG_CONFIGURATION does not exist!"
  exit 1
fi

OLDFILES=$(find $LOG_FOLDER -maxdepth 1 -name "${LABEL}*" -type d)
if [ $(echo $OLDFILES | wc -l) -gt 0 ]
then
  echo "Older runs with this label:"
  echo $OLDFILES | tr " " "\n"
  #read -p "Delete older runs? " -n 1
  #echo
  #if [[ $REPLY =~ ^[Yy]$ ]]
  #then
    #echo Deleting...
    #rm -rf $OLDFILES
  #else
    #echo Leaving old runs in $LOG_FOLDER.
  #fi
fi

for i in $(seq 1 $NUM_RUNS)
do
  TEST_NAME=${LABEL}${i}
  echo Running load test $TEST_NAME in 2, press ^C to cancel
  sleep 2

  echo "Restarting system..."
  fab update

  $TSUNG_COMMAND -l ${LOG_FOLDER}/${TEST_NAME}.log -f $TSUNG_CONFIGURATION -w 1 start

  OUTPUT_FILE=$(readlink -f $(ls -rt ${LOG_FOLDER}/*/${LABEL}*.log | tail -1))
  OUTPUT_FOLDER=$(dirname $OUTPUT_FILE)
  REPORT_FOLDER=${LOG_FOLDER}/$TEST_NAME-report
  echo Output file is $OUTPUT_FILE
  echo Output folder is $OUTPUT_FOLDER
  echo Report folder is $REPORT_FOLDER

  # Generate report
  mkdir -p $REPORT_FOLDER
  cd $REPORT_FOLDER
  /usr/lib/tsung/bin/tsung_stats.pl --stats $OUTPUT_FILE
  cd -

  # Move other log files to report directory and delete original
  mv $OUTPUT_FOLDER/* $REPORT_FOLDER/
  rm -r $OUTPUT_FOLDER

  echo "Finished ${TEST_NAME} at `date`"
done

echo "Saving to remote folder $REMOTE_FOLDER..."
rsync -avz $LOG_FOLDER/ $REMOTE_FOLDER

