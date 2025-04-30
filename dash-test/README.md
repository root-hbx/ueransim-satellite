# Dash.js Application

## Script for Tests

```
./index.html
```

## Commands

How to Run:

(1) Live Server

Recommended when you wanna test for functionality


(2) Python HTTP.Server

```
python3 -m http.server 8080
```

Recommended when you wanna test in python scripts

When you use the command `python3 -m http.server 8080`, it actually starts the built-in HTTP server module of Python instead of calling any specific script.

When a user visits `http://localhost:8080/`, the server automatically provides the `index.html` file as the default page

## Steps

### Start Open5gs-2

Open5GS-2 VM:

```
opensat sysinit
opensat psup
```

### Create `uesimtun0`

windows 1:

```
build/nr-gnb -c config/open5gs2-gnb.yaml
```

windows 2:

```
sudo build/nr-ue -c config/open5gs2-ue.yaml
```

### Set Default Network Interface

See the dafault network interfaces:

```
ip route show
```

```
ueransim@ueransim:~/ueransim-satellite/dash-test$ ip route show
default dev uesimtun0 scope link 
10.42.0.0/24 dev uesimtun0 proto kernel scope link src 10.42.0.4 
172.16.122.0/24 dev ens34 proto kernel scope link src 172.16.122.133 
172.16.162.0/24 dev ens33 proto kernel scope link src 172.16.162.134 metric 100 
172.16.162.2 dev ens33 proto dhcp scope link src 172.16.162.134 metric 100 
```

Remove the default data interfaces:

```
sudo pkill dhclient
sudo ip route del default dev ens33
```

Set `uesimtun0` as dafault:

```
sudo ip route add default dev uesimtun0
```

```
ueransim@ueransim:~/ueransim-satellite/dash-test$ ip route show default
default dev uesimtun0 scope link 
```

## Script for Experiments

```
../satellite-flow/samples/dash-if-reference-player/index.html
```

How to Run:

```
cd ../satellite-flow/
python3 -m http.server 8080
```

Then, in your web browser, input:

```
http://localhost:8000/samples/dash-if-reference-player/
```

Now we are all good :))
