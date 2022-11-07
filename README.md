# AwesomeSDFS

Awesome SDFS is a Simple Distributed File System that handles large data sets and provides a CLI interface to PUT/GET/DELETE/UPDATE and LIST files in the system. SDFS is built with a SWIM like failure detector with configurable failure detection parameters and can handle 4 failures at a time by replicating each file at 4 nodes and supports re-replication when it detects 3 node failures making it highly fault-tolerant. The SDFs arranges nodes in a virtual ring and maintains full membership list and configures its topology on 3 failures and uses consistant hashing to find the node to store a file. The SDFS uses a leader node to cordinate all the file based operations and has a basic leader election protocol running in the background to elect a new leader on failure. SDFS also uses a DNS process to allow new nodes to know about current leader.

## Usage

### STEP-1

Edit the `config.py` file in `introduce process` and `awesomeSDFS` with the information about all the available nodes and the GLOBAL_RING_TOPOLOGY for all the nodes.

Enter the `hostname` or `IP` and `Port` for the node tobe monitor.

```python

H1: final = Node('127.0.0.1', 8001, 'H1')
H2: final = Node('127.0.0.1', 8002, 'H2')
H3: final = Node('127.0.0.1', 8003, 'H3')
H4: final = Node('127.0.0.1', 8004, 'H4')
H5: final = Node('127.0.0.1', 8005, 'H5')
H6: final = Node('127.0.0.1', 8006, 'H6')
H7: final = Node('127.0.0.1', 8007, 'H7')
H8: final = Node('127.0.0.1', 8008, 'H8')
H9: final = Node('127.0.0.1', 8009, 'H9')
H10: final = Node('127.0.0.1', 8010, 'H10')

GLOBAL_RING_TOPOLOGY: dict = {

    H1: [H2, H10, H5],

    H2: [H3, H1, H6],

    H3: [H4, H2, H7],

    H4: [H5, H3, H8],

    H5: [H6, H4, H9],

    H6: [H7, H5, H10],

    H7: [H8, H6, H1],

    H8: [H9, H7, H2],

    H9: [H10, H8, H3],

    H10: [H1, H9, H4]

}
```

The above example configure the failure detector to monitor 10 process running on 10 different ports locally.

To configure the Completness and Accuracy of the failure detector follow below steps.

Edit the following fields in `config.py`:

1. `M`: Parameter to configure the completness of the system. configues the system to handle max number of simultanious failures.

2. `PING_TIMEOOUT`: The time to wait for the ACK from the node.

3. `PING_DURATION`: Parameter to configure frequency of PINGs.

4. `CLEANUP_TIME`: The time out to mark a suspected node as failure and remove from membership list.

The below configuration allows the failure detector to handle upto 3 failures and still maintain the 100% completeness. The M value can be changes to any number depending on the requirement. The PING_TIMEOUT can be adjusted such a way to improve the accuracy of failure detection and it depends on the network latency. The PING_DURATION lets users control the number of bytes flowing in the network, this parameter depends on the network capability. The CLEANUP_TIME gives a suspected node some additional time to make available online, this parameter depends on the network congestion and intermitent network issues in the system.

```python

M: final = 3

PING_TIMEOOUT: final = 2

PING_DURATION: final = 2.5

CLEANUP_TIME: final = 10

```

### STEP-2

Start the introducer process.

```console
$ cd ~/awesomesdfs/introduce\ process/
$ python3 main.py'
```

The introduces will run on port 8888.

### STEP-3

Once the nodes and global ring topology is updated. RUN the below command.

The `main.py` has the starter code to initialize and star the failure detector.

To run the application following options has to be passed.

`--hostname=`   : The current hostname or IP of the node.
`--port=`       : The current Port of the node.
`-t`            : Which allows application to run in test mode.

> **_NOTE:_** Introducer node should be up and running before starting other nodes.

```console
$ cd ~/awesomesdfs/
$ python3.9 main.py --hostname="127.0.0.1" --port=8000
```

### STEP-4

Once the application is stated the `awesomesdfs` provides a console to interact with the running application with following options and commands.

Option 1: Prints the membership list in the current node along with the nodes its pinging

Option 2: Prints the ID of the current node as `<hostname>:<port>`

Option 3: Join the current node by started sending PINGs and ACKs to other nodes.

Option 4: Leaves the node by stop sending PINGs and ACKs to other nodes.

Option 5: Print current Bytes per seconds.

Option 6: Print current False positive rate.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>
 1
2022-11-06 23:05:25,047: [INFO] local membership list: 6 
fa22-cs425-6901.cs.illinois.edu:8000 : (1667797524.9331925, 1)
fa22-cs425-6906.cs.illinois.edu:8000 : (1667797524.9343975, 1)
fa22-cs425-6907.cs.illinois.edu:8000 : (1667797521.7628677, 1)
fa22-cs425-6908.cs.illinois.edu:8000 : (1667797521.4346967, 1)
fa22-cs425-6909.cs.illinois.edu:8000 : (1667797519.9328763, 1)
fa22-cs425-6910.cs.illinois.edu:8000 : (1667797522.6475646, 1)

2022-11-06 23:05:25,047: [INFO] current ping nodes: 
fa22-cs425-6907.cs.illinois.edu:8000
fa22-cs425-6901.cs.illinois.edu:8000
fa22-cs425-6910.cs.illinois.edu:8000

choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>
 2
fa22-cs425-6906.cs.illinois.edu:8000
```

commands:

* `put <localfilename> <sdfsfilename>`: Uploads a file available at `<localfilename>` to SDFS and stored as `<sdfsfilename>`. If uploaded a file which is already present in SDFS it will be stored as new version.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

put /home/bachina3/MP3/awesomesdfs/testfiles/3 3
Leader successfully received PUT request for file 3. waiting for nodes to download the file...
2022-11-06 23:09:59,285: [INFO] Opening SSH connection to 172.22.158.230, port 22
2022-11-06 23:09:59,287: [INFO] [conn=0] Connected to SSH server at 172.22.158.230, port 22
2022-11-06 23:09:59,287: [INFO] [conn=0]   Local address: 172.22.158.230, port 58740
2022-11-06 23:09:59,287: [INFO] [conn=0]   Peer address: 172.22.158.230, port 22
2022-11-06 23:09:59,361: [INFO] [conn=0] Beginning auth for user bachina3
2022-11-06 23:10:00,821: [INFO] [conn=0] Auth for user bachina3 succeeded
2022-11-06 23:10:00,821: [INFO] [conn=0] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/testfiles/3
2022-11-06 23:10:00,822: [INFO] [conn=0, chan=0] Requesting new SSH session
2022-11-06 23:10:01,898: [INFO] [conn=0, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/testfiles/3
2022-11-06 23:10:01,999: [INFO] [conn=0, chan=0]   Receiving file /home/bachina3/MP3/awesomesdfs/sdfs/3_version1, size 5242880
2022-11-06 23:10:02,598: [INFO] [conn=0, chan=0] Received exit status 0
2022-11-06 23:10:02,598: [INFO] [conn=0, chan=0] Received channel close
2022-11-06 23:10:02,599: [INFO] [conn=0, chan=0] Stopping remote SCP
2022-11-06 23:10:02,599: [INFO] [conn=0, chan=0] Closing channel
2022-11-06 23:10:02,599: [INFO] [conn=0, chan=0] Channel closed
2022-11-06 23:10:02,599: [INFO] [conn=0] Closing connection
2022-11-06 23:10:02,599: [INFO] [conn=0] Sending disconnect: Disconnected by application (11)
2022-11-06 23:10:02,600: [INFO] [conn=0] Connection closed
2022-11-06 23:10:02,600: [INFO] successfully downloaded file /home/bachina3/MP3/awesomesdfs/testfiles/3 from 172.22.158.230 requested by fa22-cs425-6901.cs.illinois.edu:8000
FILE 3 SUCCESSFULLY STORED
PUT runtime: 3.3441507816314697 seconds

choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

put /home/bachina3/MP3/awesomesdfs/testfiles/3 3
Leader successfully received PUT request for file 3. waiting for nodes to download the file...
2022-11-06 23:11:38,018: [INFO] Opening SSH connection to 172.22.158.230, port 22
2022-11-06 23:11:38,019: [INFO] [conn=1] Connected to SSH server at 172.22.158.230, port 22
2022-11-06 23:11:38,019: [INFO] [conn=1]   Local address: 172.22.158.230, port 37660
2022-11-06 23:11:38,019: [INFO] [conn=1]   Peer address: 172.22.158.230, port 22
2022-11-06 23:11:38,091: [INFO] [conn=1] Beginning auth for user bachina3
2022-11-06 23:11:46,182: [INFO] [conn=1] Auth for user bachina3 succeeded
2022-11-06 23:11:46,183: [INFO] [conn=1] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/testfiles/3
2022-11-06 23:11:46,183: [INFO] [conn=1, chan=0] Requesting new SSH session
2022-11-06 23:11:46,708: [INFO] [conn=1, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/testfiles/3
2022-11-06 23:11:46,819: [INFO] [conn=1, chan=0]   Receiving file /home/bachina3/MP3/awesomesdfs/sdfs/3_version2, size 5242880
2022-11-06 23:11:47,953: [INFO] [conn=1, chan=0] Received exit status 0
2022-11-06 23:11:47,954: [INFO] [conn=1, chan=0] Received channel close
2022-11-06 23:11:47,954: [INFO] [conn=1, chan=0] Stopping remote SCP
2022-11-06 23:11:47,954: [INFO] [conn=1, chan=0] Closing channel
2022-11-06 23:11:47,955: [INFO] [conn=1, chan=0] Channel closed
2022-11-06 23:11:47,955: [INFO] [conn=1] Closing connection
2022-11-06 23:11:47,955: [INFO] [conn=1] Sending disconnect: Disconnected by application (11)
2022-11-06 23:11:47,955: [INFO] [conn=1] Connection closed
2022-11-06 23:11:47,955: [INFO] successfully downloaded file /home/bachina3/MP3/awesomesdfs/testfiles/3 from 172.22.158.230 requested by fa22-cs425-6901.cs.illinois.edu:8000
FILE 3 SUCCESSFULLY STORED
PUT runtime: 9.960254430770874 seconds
```

* `get <sdfsfilename> <localfilename>`: Will download latest version of file `<sdfsfilename>` to `<localfilename>`.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

get 3 /home/bachina3/MP3/ 
2022-11-06 23:14:52,351: [INFO] fetching machine details where the 3 is stored from Leader.
2022-11-06 23:14:52,356: [INFO] Opening SSH connection to fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:14:52,359: [INFO] [conn=0] Connected to SSH server at fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:14:52,359: [INFO] [conn=0]   Local address: 172.22.94.230, port 42516
2022-11-06 23:14:52,360: [INFO] [conn=0]   Peer address: 172.22.94.228, port 22
2022-11-06 23:14:52,387: [INFO] [conn=0] Beginning auth for user bachina3
2022-11-06 23:14:52,977: [INFO] [conn=0] Auth for user bachina3 succeeded
2022-11-06 23:14:52,977: [INFO] [conn=0] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/sdfs/3_version2
2022-11-06 23:14:52,977: [INFO] [conn=0, chan=0] Requesting new SSH session
2022-11-06 23:14:53,500: [INFO] [conn=0, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/sdfs/3_version2
2022-11-06 23:14:53,548: [INFO] [conn=0, chan=0]   Receiving file /home/bachina3/MP3/3_version2, size 5242880
2022-11-06 23:14:53,802: [INFO] [conn=0, chan=0] Received exit status 0
2022-11-06 23:14:53,802: [INFO] [conn=0, chan=0] Received channel close
2022-11-06 23:14:53,803: [INFO] [conn=0, chan=0] Stopping remote SCP
2022-11-06 23:14:53,803: [INFO] [conn=0, chan=0] Closing channel
2022-11-06 23:14:53,803: [INFO] [conn=0, chan=0] Channel closed
2022-11-06 23:14:53,803: [INFO] [conn=0] Closing connection
2022-11-06 23:14:53,803: [INFO] [conn=0] Sending disconnect: Disconnected by application (11)
2022-11-06 23:14:53,804: [INFO] [conn=0] Connection closed
GET file 3 success: copied to /home/bachina3/MP3/
GET runtime: 1.4528722763061523 seconds
```

* `delete <sdfsfilename>`: Will remove the file `<sdfsfilename>` from SDFS.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

delete 3
Leader successfully received DELETE request for file 3. waiting for nodes to delete the file...
FILE 3 SUCCESSFULLY DELETED
DELETE runtime: 0.00704646110534668 seconds
```

* `ls <sdfsfilename>`: Will list the host details where the `<sdfsfilename>` file is currenlty stored.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

ls 2
File 2 found in 4 machines:
fa22-cs425-6901.cs.illinois.edu:8000
fa22-cs425-6910.cs.illinois.edu:8000
fa22-cs425-6909.cs.illinois.edu:8000
fa22-cs425-6907.cs.illinois.edu:8000
```

* `store`: Will list current files stored in the SDFS.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

store
2022-11-06 23:23:29,978: [INFO] files stored locally: 
filename: [versions]
2: ['2_version1', '2_version2', '2_version3', '2_version4'](4)
```

* `get-versions <sdfsfilename> <numversions> <localfilename>`: Get versions will let you dowload `sdfsfilename` file along with its old versions to directory `localfilename`.

```console
$ python3 main.py --hostname='fa22-cs425-6906.cs.illinois.edu' --port=8000 -t
choose one of the following options or type commands:
options:
 1. list the membership list.
 2. list self id.
 3. join the group.
 4. leave the group.
commands:
 * put <localfilename> <sdfsfilename>
 * get <sdfsfilename> <localfilename>
 * delete <sdfsfilename>
 * ls <sdfsfilename>
 * store
 * get-versions <sdfsfilename> <numversions> <localfilename>

get-versions 2 5 /home/bachina3/MP3/
2022-11-06 23:26:10,628: [INFO] fetching machine details where the 2 is stored from Leader.
2022-11-06 23:26:10,632: [INFO] Opening SSH connection to fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:10,634: [INFO] [conn=2] Connected to SSH server at fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:10,634: [INFO] [conn=2]   Local address: 172.22.158.230, port 51828
2022-11-06 23:26:10,634: [INFO] [conn=2]   Peer address: 172.22.94.228, port 22
2022-11-06 23:26:10,660: [INFO] [conn=2] Beginning auth for user bachina3
2022-11-06 23:26:11,311: [INFO] [conn=2] Auth for user bachina3 succeeded
2022-11-06 23:26:11,312: [INFO] [conn=2] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version4
2022-11-06 23:26:11,312: [INFO] [conn=2, chan=0] Requesting new SSH session
2022-11-06 23:26:12,115: [INFO] [conn=2, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version4
2022-11-06 23:26:12,155: [INFO] [conn=2, chan=0]   Receiving file /home/bachina3/MP3/_version0, size 5242880
2022-11-06 23:26:12,377: [INFO] [conn=2, chan=0] Received exit status 0
2022-11-06 23:26:12,378: [INFO] [conn=2, chan=0] Received channel close
2022-11-06 23:26:12,379: [INFO] [conn=2, chan=0] Stopping remote SCP
2022-11-06 23:26:12,379: [INFO] [conn=2, chan=0] Closing channel
2022-11-06 23:26:12,379: [INFO] [conn=2, chan=0] Channel closed
2022-11-06 23:26:12,379: [INFO] [conn=2] Closing connection
2022-11-06 23:26:12,379: [INFO] [conn=2] Sending disconnect: Disconnected by application (11)
2022-11-06 23:26:12,380: [INFO] [conn=2] Connection closed
2022-11-06 23:26:12,381: [INFO] Opening SSH connection to fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:12,382: [INFO] [conn=3] Connected to SSH server at fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:12,383: [INFO] [conn=3]   Local address: 172.22.158.230, port 51836
2022-11-06 23:26:12,383: [INFO] [conn=3]   Peer address: 172.22.94.228, port 22
2022-11-06 23:26:12,410: [INFO] [conn=3] Beginning auth for user bachina3
2022-11-06 23:26:13,356: [INFO] [conn=3] Auth for user bachina3 succeeded
2022-11-06 23:26:13,357: [INFO] [conn=3] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version3
2022-11-06 23:26:13,357: [INFO] [conn=3, chan=0] Requesting new SSH session
2022-11-06 23:26:13,952: [INFO] [conn=3, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version3
2022-11-06 23:26:13,984: [INFO] [conn=3, chan=0]   Receiving file /home/bachina3/MP3/_version1, size 5242880
2022-11-06 23:26:14,217: [INFO] [conn=3, chan=0] Received exit status 0
2022-11-06 23:26:14,218: [INFO] [conn=3, chan=0] Received channel close
2022-11-06 23:26:14,218: [INFO] [conn=3, chan=0] Stopping remote SCP
2022-11-06 23:26:14,219: [INFO] [conn=3, chan=0] Closing channel
2022-11-06 23:26:14,219: [INFO] [conn=3, chan=0] Channel closed
2022-11-06 23:26:14,219: [INFO] [conn=3] Closing connection
2022-11-06 23:26:14,219: [INFO] [conn=3] Sending disconnect: Disconnected by application (11)
2022-11-06 23:26:14,219: [INFO] [conn=3] Connection closed
2022-11-06 23:26:14,220: [INFO] Opening SSH connection to fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:14,222: [INFO] [conn=4] Connected to SSH server at fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:14,222: [INFO] [conn=4]   Local address: 172.22.158.230, port 51852
2022-11-06 23:26:14,222: [INFO] [conn=4]   Peer address: 172.22.94.228, port 22
2022-11-06 23:26:14,248: [INFO] [conn=4] Beginning auth for user bachina3
2022-11-06 23:26:15,199: [INFO] [conn=4] Auth for user bachina3 succeeded
2022-11-06 23:26:15,199: [INFO] [conn=4] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version2
2022-11-06 23:26:15,200: [INFO] [conn=4, chan=0] Requesting new SSH session
2022-11-06 23:26:15,800: [INFO] [conn=4, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version2
2022-11-06 23:26:15,828: [INFO] [conn=4, chan=0]   Receiving file /home/bachina3/MP3/_version2, size 5242880
2022-11-06 23:26:16,060: [INFO] [conn=4, chan=0] Received exit status 0
2022-11-06 23:26:16,061: [INFO] [conn=4, chan=0] Received channel close
2022-11-06 23:26:16,061: [INFO] [conn=4, chan=0] Stopping remote SCP
2022-11-06 23:26:16,061: [INFO] [conn=4, chan=0] Closing channel
2022-11-06 23:26:16,061: [INFO] [conn=4, chan=0] Channel closed
2022-11-06 23:26:16,062: [INFO] [conn=4] Closing connection
2022-11-06 23:26:16,062: [INFO] [conn=4] Sending disconnect: Disconnected by application (11)
2022-11-06 23:26:16,062: [INFO] [conn=4] Connection closed
2022-11-06 23:26:16,063: [INFO] Opening SSH connection to fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:16,065: [INFO] [conn=5] Connected to SSH server at fa22-cs425-6901.cs.illinois.edu, port 22
2022-11-06 23:26:16,065: [INFO] [conn=5]   Local address: 172.22.158.230, port 41600
2022-11-06 23:26:16,065: [INFO] [conn=5]   Peer address: 172.22.94.228, port 22
2022-11-06 23:26:16,090: [INFO] [conn=5] Beginning auth for user bachina3
2022-11-06 23:26:17,115: [INFO] [conn=5] Auth for user bachina3 succeeded
2022-11-06 23:26:17,116: [INFO] [conn=5] Starting remote SCP, args: -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version1
2022-11-06 23:26:17,116: [INFO] [conn=5, chan=0] Requesting new SSH session
2022-11-06 23:26:17,721: [INFO] [conn=5, chan=0]   Command: scp -f /home/bachina3/MP3/awesomesdfs/sdfs/2_version1
2022-11-06 23:26:17,749: [INFO] [conn=5, chan=0]   Receiving file /home/bachina3/MP3/_version3, size 5242880
2022-11-06 23:26:17,984: [INFO] [conn=5, chan=0] Received exit status 0
2022-11-06 23:26:17,985: [INFO] [conn=5, chan=0] Received channel close
2022-11-06 23:26:17,985: [INFO] [conn=5, chan=0] Stopping remote SCP
2022-11-06 23:26:17,985: [INFO] [conn=5, chan=0] Closing channel
2022-11-06 23:26:17,985: [INFO] [conn=5, chan=0] Channel closed
2022-11-06 23:26:17,986: [INFO] [conn=5] Closing connection
2022-11-06 23:26:17,986: [INFO] [conn=5] Sending disconnect: Disconnected by application (11)
2022-11-06 23:26:17,986: [INFO] [conn=5] Connection closed
GET file 2 success: copied to /home/bachina3/MP3/
GET-VERSIONS runtime: 7.35864520072937 seconds
```
