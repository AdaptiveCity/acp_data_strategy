#!/bin/bash

pg_dump -c -d acp_prod >db_backups/db_acp_prod_$(date +%Y-%m-%d).sql

