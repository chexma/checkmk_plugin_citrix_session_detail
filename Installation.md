# Installation Guide

## Step 1: Install the Plugin

Copy the MKP file to your Checkmk server and switch to the site user:

```bash
scp citrix_session_detail-X.Y.Z.mkp user@checkmk-server:/tmp/
ssh user@checkmk-server
sudo su - <sitename>
```

Install and enable it:

```bash
mkp add /tmp/citrix_session_detail-X.Y.Z.mkp
mkp enable citrix_session_detail X.Y.Z
omd restart apache
```

## Step 2: Deploy the Agent Plugin to the Delivery Controller

Copy `citrix_session_detail.ps1` into the `plugins` directory of the Windows
agent on the Citrix Delivery Controller (`C:\ProgramData\checkmk\agent\plugins\`).

Optional: limit the number of queried sessions with
`C:\ProgramData\checkmk\agent\config\citrix_session_detail.cfg`:

```text
max_record_count = 500
```

## Step 3: Set Up the Piggyback Hosts

The Delivery Controller sends the session data of each Citrix server as
piggyback data for the server's short host name. Create a host in Checkmk for
each Citrix server with exactly that name (or use an existing one) and set its
data source to piggyback.

## Step 4: Run Service Discovery

Run service discovery on the Delivery Controller and on the Citrix servers.
Each Citrix server gets a `Citrix Sessions` service. Thresholds are set under
**Setup > Services > Service monitoring rules > Citrix Session Count**.

## Upgrading

```bash
mkp add citrix_session_detail-X.Y.Z.mkp
mkp enable citrix_session_detail X.Y.Z
omd restart apache
cmk -R
```
