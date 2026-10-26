#!/bin/bash
# Restores the DVD Rental sample database the first time the container starts.
set -e

if [ -f /data/dvdrental.tar ]; then
  echo ">>> Creating database dvdrental"
  createdb -U "$POSTGRES_USER" dvdrental
  echo ">>> Restoring dvdrental.tar"
  pg_restore -U "$POSTGRES_USER" -d dvdrental --no-owner /data/dvdrental.tar
  echo ">>> dvdrental restored"
else
  echo ">>> /data/dvdrental.tar not found. Put it in data/source/ and recreate the container."
fi
