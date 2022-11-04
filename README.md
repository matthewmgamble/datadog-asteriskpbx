Asterisk PBX Integration for Datadog
===================

Datadog Agent plugin for the Open Source Asterisk PBX based on the work of jwestbrook (https://github.com/jwestbrook/datadog-asteriskpbx).

This version has been updated to support DataDog agent v7 as well as being updated to support looking at PJSIP channels and endpoints rather than using the legacy SIP endpoints.  It is not as complete as the original module, but meets the requirements for the monitoring I needed to implement.  Patches welcome.


Prerequisites
-----------
- Datadog Agent v6 (6.3.1)
- pyst Library patched to support Asterisk > 14 [link to patch](https://github.com/jfernandz/pyst2/pull/47/commits/a74c3a66bd30c8ed45b5d1a9cd20da07305002e4)


Installation (Datadog Agent v6)
-----------

Install the Asterisk Manager Python library for datadog.

```
/opt/datadog-agent/embedded/bin/pip install pyst2
```

Patch /opt/datadog-agent/embedded/lib/python3.8/site-packages/asterisk/manager.py with the one line change from the patch above to handle the updated format of responses Asterisk 14 returns.

Get the module files for the datadog agent.

```
cd /usr/src/
git clone https://github.com/matthewmgamble/datadog-asteriskpbx.git
cd datadog-asteriskpbx/
```

Copy the module files to the datadog directories.

```
cp -R checks.d/asteriskpbx.py /etc/datadog-agent/checks.d/
cp -R conf.d/asteriskpbx.yaml /etc/datadog-agent/conf.d/
```

Edit the configuration file for the module.

```
nano /etc/datadog-agent/conf.d/asteriskpbx.yaml
```

Insert the AMI User and Password for the PBX.

```
init_config:
	instances:
		- host: localhost #defaults to localhost
		  port: 5038 #defaults to 5038
		  manager_user: user #required
		  manager_secret: secret #required
		  extension_length: 5 #Length of your internal extensions at the PBX
		  #this user needs to have the command write privilege
```

Restart  the Datadog service.

```
/etc/init.d/datadog-agent restart
```

Check the Datadog service status.

```
/etc/init.d/datadog-agent info
```

The output should be like the next text.

```
    asteriskpbx
    -----------
      - instance #0 [OK]
      - Collected 17 metrics, 0 events & 1 service check
```

Important notes
-----------
**SIP Trunks Metrics**

This version only supports PJSIP endpoints, not the clasic Asterisk SIP endpoints.  If you need support for chan_sip please look at the original module this was forked from.
