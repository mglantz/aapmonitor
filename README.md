# aapmonitor
Ansible Automation Platform monitor script, developed on RHEL 8 for AAP 1.x (Tower 3.8.4+) but should work on AAP 2.x as well.

# Howto
1. Install configparser
```
pip3 install configparser
```
2. Install the AAP CLI tool: https://docs.ansible.com/ansible-tower/latest/html/towercli/

3. Create a token to authenticate with: https://docs.ansible.com/ansible-tower/latest/html/administration/oauth2_token_auth.html#application-token-functions

4. Edit the config file to set your configured token and to set monitoring alarm limits

5. Run aapmonitor.py

![alt text](aapmonitor.png)
