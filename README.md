Algorand Node Setup Steps
Ubuntu:
Package Manager Installation:
sudo apt-get update
sudo apt-get install -y gnupg2 curl software-properties-common
	/etc/apt/trusted.gpg.d/algorand.asc
sudo add-apt-repository "deb [arch=amd64] https://releases.algorand.com/deb/ stable main"
sudo apt-get update
	# To get both algorand and the devtools:
	sudo apt-get install -y algorand-devtools
These commands will install and configure algod as a service and place the algorand binaries in the /usr/bin directory. These binaries will be in the path so the algod and goal commands can be executed from anywhere. Additionally, every node has a data directory, in this case, it will be set to /var/lib/algorand. This install defaults to the Algorand MainNet network.
Since the data directory /var/lib/algorand is owned by the user algorand and the daemon algod is run as the user algorand, some operations such as the ones related to wallets and accounts keys (goal account ... and goal wallet ...) need to be run as the user algorand. For example, to list participation keys, use 
sudo -u algorand -E goal account listpartkeys
(assuming the environment variable $ALGORAND_DATA is set to /var/lib/algorand)
!!! Never run goal as root (e.g., do not run sudo goal account listpartkeys). Running goal as root can compromise the permissions of files in /var/lib/algorand. !!!

Setting the environment variable permanently (Ubuntu, Debian, Fedora, CentOS) 
For Bash:
	nano ~/.bashrc
Add this line at the end of the file:
export ALGORAND_DATA=/var/lib/algorand
Save the file (in nano: Ctrl+O, then Enter, then Ctrl+X)
Apply the changes: 
	source ~/.bashrc
You can verify the environment variable is set by running:
	echo $ALGORAND_DATA
This should display /var/lib/algorand if set correctly.
Start Node
Starting and stopping a node should be done using systemctl commands:
	sudo systemctl start algorand
	sudo systemctl stop algorand
The status of the node can be checked by running:
	goal node status -d /var/lib/algorand
Updates
Check for and install the latest updates by running 
./update.sh -d ~/node/data 
at any time from within your node directory. Note that the -d argument has to be specified when updating. It will query S3 for available builds and see if there are newer builds than the currently installed version. To force an update, run 
	./update.sh -i -c stable -d ~/node/data.
Setting up a schedule to automatically check for and install updates can be done with CRON.
crontab -e
Add a line that looks like this (run update.sh every hour, on the half-hour, of every day), where ‘user’ is the name of the account used to install / run the node:
	30 * * * * /home/user/node/update.sh -d /home/<user>/node/data >/home/<user>/node/update.log 2>&1

Telemetry can also be provided without providing a hostname:
diagcfg telemetry enable
After enabling (or disabling) telemetry, the node needs to be restarted.
Do not run diagcfg as the root user: it would only enable telemetry for nodes run as the root user (and nodes should usually not be run as the root user). In particular, do not run sudo diagcfg ....
Telemetry can be disabled at any time by using (as the user running algod):
diagcfg telemetry disable
Running the diagcfg commands will create and update the logging configuration settings stored in ~/.algorand/logging.config
To check if telemetry is enabled, run (as the user running algod):
	diagcfg telemetry
Sync Node with Network¶
When a node first starts, it will need to sync with the network. This process can take a while as the node is loading up the current ledger and catching up to the rest of the network. See the section below a Fast Catchup option. The status can be checked by running the following goal command:
goal node status
The goal node status command will return information about the node and what block number it is currently processing. When the node is caught up with the rest of the network, the "Sync Time" will be 0.0
Sync Node Network using Fast Catchup
URL MAINNET: https://algorand-catchpoints.s3.us-east-2.amazonaws.com/channel/mainnet/latest.catchpoint
Output is a string in this format:
	45210000#DBHFRZSF37ADOOMPMYOEBEAIL4Z5UKQLFGULFN3UNBJQSQ2IO4SQ
Do NOT use fast catchup on an archival or relay node. If you ever do it, you need to reset your node and start from scratch.
Fast catchup requires trust in the entity providing the catchpoint. An attacker controlling enough relays and proposing a malicious catchpoint can in theory allow a node to sync to an incorrect state of the blockchain. For full decentralization and no trust requirement, either use a catchpoint generated by one of your archival node (you can read the catchpoint using goal node status) or catch up from scratch without fast catchup.
Use the sync point captured above and paste into the catchup option
	goal node catchup 4420000......
Only the first 3 status (Catchpoint, total accounts, accounts processed) will show right after catchup begins. Status on total blocks and downloaded blocks will only show after catchup processes the total number of accounts, which takes several minutes.
A new option can facilitate a status watch, -w which takes a parameter of time, in milliseconds, between two successive status updates. This will eliminate the need to repeatedly issue a status manually. Press ^c to exit the watch.
goal node status -w 1000
Notice that the 5 Catchpoint status lines will disappear when completed, and then only a few more minutes are needed to sync from that point to the current block. **Once there is a Sync Time of 0, the node is synced and if fully usable.
Do not forget to restart algod after any change to the configuration.

To check if your node's DNS access is correct, run the following commands in the terminal:
	dig -t SRV _algobootstrap._tcp.mainnet.algorand.network +dnssec
	dig -t SRV _algobootstrap._tcp.mainnet.algorand.network @8.8.8.8 +dnssec
While there are relays all over the world, some regions may have a few number of relays which may slow down catching up. Check latency to the best relays using algonode.io scripts (in the folder utils of https://snap.algonode.cloud/ --- copied below for completeness):
#!/bin/bash
# needs dig from dnsutils
N=$(dig +short srv _algobootstrap._tcp.mainnet.algorand.network @1.1.1.1 |wc -l)
echo "Querying $N nodes, be patient..."
echo "" > report.txt
for relay in $(dig +short srv _algobootstrap._tcp.mainnet.algorand.network @1.1.1.1|awk '{print $4 ":" $3}');
do
  echo -n .
  curl -s -o /dev/null --max-time 1 "http://$relay/v1/urtho/ledger/0"
  echo -ne '\bo'
  curl -s -o /dev/null --max-time 1 "http://$relay/v1/urtho/ledger/0" -w %{time_total} >> report.txt
  echo -ne '\b+'
  echo "s;$relay" >> report.txt
done
echo "Top 20 nodes"
sort -n report.txt | head -20
Latency above 100ms to the top 20 relays may most likely cause issues. 5. Check that $ALGORAND_DATA/config.json is either absent or only contain the non-default parameters you actually need to change. Only change parameters if you understand the consequences, some parameter changes may significantly slow down syncing.
