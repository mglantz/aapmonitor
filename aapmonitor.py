#!/usr/bin/python3
"""
Monitoring for Ansible Automation Platform 1.x, should work on 2.x as well but not tested.
Author: Magnus Glantz, sudo@redhat.com, 2022
"""
import os
import sys
import subprocess
import json
import configparser

def config_section_map(section, config):
    """ Deal with different sections in config file """
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print("skip: ", option)
        except KeyError:
            print("exception on", option)
            dict1[option] = None
    return dict1

def api_connect(token):
    """ Connect to API and fetch info """
    # Define the awx cli command to run
    command = ("/usr/bin/awx -k metrics --conf.token "+token)

    # Run awx cli command and fetch output
    with subprocess.Popen([command], stdout=subprocess.PIPE, shell=True) as the_process:
        output, err = the_process.communicate(b"input data")
        return_code = the_process.returncode

    # Check return code, if OK, fetch output otherwise exit
    if return_code == 0:
        ascii_output = output.decode('utf-8')
        output_string = ''.join(ascii_output)
    else:
        print("Error fetching metrics data")
        print("Error message: ", err)
        sys.exit(1)

    # Convert json to python dictionary, makes it easier to manage
    dict1 = json.loads(output_string)
    return dict1

def check_jobs_running(config, dict1):
    """ check number of running jobs """
    jobs_running = int(config_section_map("monitoring", config)['jobs_pending'])
    current_jobs_running = int(dict1['awx_running_jobs_total']['samples'][0]['value'])

    # Compare what should be and what is
    if current_jobs_running < jobs_running:
        print("OK: Current jobs running: ", current_jobs_running)
        warning=0
    else:
        print("Warning: Current jobs running: ", current_jobs_running)
        warning=1
    return warning

def check_jobs_pending(config, dict1):
    """ check number of pending jobs """
    jobs_pending = int(config_section_map("monitoring", config)['jobs_pending'])
    current_jobs_pending = int(dict1['awx_pending_jobs_total']['samples'][0]['value'])

    if current_jobs_pending < jobs_pending:
        print("OK: Current jobs pending: ", current_jobs_pending)
        warning = 0
    else:
        print("Warning: Current jobs pending: ", current_jobs_pending)
        warning = 1
    return warning

def check_jobs_failed(config, dict1):
    """ check number of recently failed jobs """
    jobs_failed_limit = int(config_section_map("monitoring", config)['jobs_failed_limit'])
    current_jobs_failed = int(dict1['awx_status_total']['samples'][0]['value'])
    tmpfile="/tmp/last_failed_jobs"

    # Save last result of number of failed jobs to a tmpfile so we can
    # find out how many failed since last run
    # In case this is the first time running the script
    # create file and set last result to current result
    if os.path.exists(tmpfile):
        with open(tmpfile, "r", encoding="utf8") as the_file:
            last_jobs_failed = int(the_file.read())
        with open(tmpfile, "w", encoding="utf8") as the_file:
            payload = str(current_jobs_failed)
            the_file.write(payload)
    else:
        with open(tmpfile, "w", encoding="utf8") as the_file:
            payload=str(current_jobs_failed)
            the_file.write(payload)
        last_jobs_failed = current_jobs_failed

    new_jobs_failed = current_jobs_failed - last_jobs_failed

    if new_jobs_failed < jobs_failed_limit:
        print("OK: New jobs failed: ", new_jobs_failed)
        warning=0
    else:
        print("Warning: New jobs failed: ", new_jobs_failed)
        warning=1
    return warning

def check_forks_remaining(config, dict1):
    """ check number of forks remaining """
    forks_remaining = int(config_section_map("monitoring", config)['forks_remaining'])
    current_forks_remaining = int(dict1['awx_instance_remaining_capacity']['samples'][0]['value'])

    if current_forks_remaining > forks_remaining:
        print("OK: Current forks remaining: ", current_forks_remaining)
        warning = 0
    else:
        print("Warning: Current forks remaining: ", current_forks_remaining)
        warning = 1
    return warning

def check_subs_remaining(config, dict1):
    """ check number of subscriptions remaining """
    subs_remaining = int(config_section_map("monitoring", config)['subs_remaining'])
    current_subs_remaining = int(dict1['awx_license_instance_free']['samples'][0]['value'])

    if current_subs_remaining > subs_remaining:
        print("OK: Current subscriptions remaining: ", current_subs_remaining)
        warning = 0
    else:
        print("Warning: Current subscriptions remaining: ", current_subs_remaining)
        warning = 1
    return warning

def check_inventories(config, dict1):
    """ check number of inventories """
    inventories_limit = int(config_section_map("monitoring", config)['inventories_limit'])
    current_inventories = int(dict1['awx_inventories_total']['samples'][0]['value'])

    if current_inventories >= inventories_limit:
        print("OK: Current inventories: ", current_inventories)
        warning = 0
    else:
        print("Warning: Only", current_inventories, "inventories found")
        warning = 1
    return warning

def check_projects(config, dict1):
    """ check number of projects """
    projects_limit = int(config_section_map("monitoring", config)['projects_limit'])
    current_projects = int(dict1['awx_projects_total']['samples'][0]['value'])

    if current_projects >= projects_limit:
        print("OK: Current projects: ", current_projects)
        warning = 0
    else:
        print("Warning: Only", current_projects, "projects found")
        warning = 1
    return warning

def main():
    """ Main function, load config, make api call and check results """
    # Fetch config from config file
    config = configparser.ConfigParser()
    try:
        with open("/etc/aapmonitor.cfg", "r", encoding="utf8") as the_file:
            if len(the_file.read()) != 0:
                config.read("/etc/aapmonitor.cfg")
            else:
                print("Error: /etc/aapmonitor.cfg is empty")
                sys.exit(1)
    except IOError:
        print("Error: failed to open /etc/aapmonitor.cfg")
        sys.exit(1)

    # Fetch token from config
    token = config_section_map("general", config)['token']

    dict1 = api_connect(token)

    warning = 0

    result = check_jobs_running(config, dict1)
    if result == 1:
        warning = 1

    result = check_jobs_pending(config, dict1)
    if result == 1:
        warning = 1

    result = check_jobs_failed(config, dict1)
    if result == 1:
        warning = 1

    result = check_forks_remaining(config, dict1)
    if result == 1:
        warning = 1

    result = check_subs_remaining(config, dict1)
    if result == 1:
        warning = 1

    result = check_inventories(config, dict1)
    if result == 1:
        warning = 1

    result = check_projects(config, dict1)
    if result == 1:
        warning = 1

    if warning == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
