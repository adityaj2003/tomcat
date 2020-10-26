<<<<<<< HEAD
# Multiplayer setup instructions

Instructions of running TOMCAT misison with two or more players involved.

## Multiplayer configuration file

To build a connection between mission server and clients, it is necessary to specify
the ip addresses and the port numbers of the server and the clients. Thus, at the
very beginning, go to the configuration file `multiplayer_config.json` file under `/docs` folder
and specify them. Refer to the existed client object structure
inside and add the clients that will be connected, no more and no less. That's
because TOMCAT mission will start only when all the clients listed in this file are connected.

## Create mission instance on server side

Server agent does not participate in TOMCAT mission, but it is needed to create an
mission instance on server side. We will hide server agent later. Use this command:
`./external/malmo/Minecraft/launchClient.sh -port 10000`. Here, `-port`
specifies the port number for the server, which should be the same as the one in the
configuration file.

## Create mission instances on client side

To run mission on client machine, use this command:
`./external/malmo/Minecraft/launchClient.sh -port x`. Here, `-port` specifies
the port numbers for the clients. Those numbers need to be consistent with the
ones in the configuration file as well.

## Final step, start misison

After the server and all the client instances are ready, run this command on
server side to start your mission: `./build/bin/runExperiment --mission 1 --multiplayer`.
`--mission` flag specifies which tomcat mission will be running and `--multiplayer` flag
will treat the mission as a multiplayer mode and start the game.
=======
Multiplayer setup instructions
==============================

Instructions for running a ToMCAT mission with two or more players involved.

## Multiplayer configuration file

To build a connection between the mission server and clients, it is necessary
to specify their IP addresses and the port numbers in the
`conf/multiplayer_config.json` configuration file. Refer to the existing client
object structure inside and add the clients that will be connected, no more and
no less. That's because the ToMCAT mission will start only when all the clients
listed in this file are connected.

## Create mission instance on server side

The server agent does not actively participate in the mission, but it is needed
to create an instance of the mission on the server side. We will hide the
server agent later.  Use this command to launch the server-side mission
instance.

    ./external/malmo/Minecraft/launchClient.sh -port 10000

Here, `-port` specifies the port number for the server, which should be the
same as the one in the configuration file.

## Create mission instances on client side

To run the mission on a client machine, use this command:

    ./external/malmo/Minecraft/launchClient.sh -port x

Here, the `-port` option specifies the port numbers for the clients. Those
numbers need to be consistent with the ones in the configuration file as well.

## Starting the mission

After the server and all the client instances are ready, run this command on
the server side to start your mission:

    ./build/bin/runMission --mission 1 --multiplayer

The `--mission` flag specifies the mission to launch and the `--multiplayer`
flag will treat the mission as a multiplayer one.


##Updates on  2020/10/19:

When running client on laplace, we will use the X virtual framebuffer (before this, make sure you have a X server on your local), which enables us to run Minecraft without a display. Also, since there is no windows needed, we must skip setting a full screen, otherwise errors would occur. Use the following commands to run client:

Xvfb :1 -screen 0 1400x900x24 &
export DISPLAY=:1.0
export TOMCAT_FULL_SCREEN=${TOMCAT_FULL_SCREEN:0}
./external/malmo/Minecraft/launchClient.sh -port 10000

>>>>>>> master
