#!/usr/bin/env python

from listrotate import *

from clr_matplot_graphs import *

import zmq, sys, time, inspect

# the class name should match with the module name
class graph_progress:
    def __init__(self, params, layout):
	self.port = int(params['cfg']['port'])
	self.ip = str(params['cfg']['ip'])
        self.context = zmq.Context()
	self.socket = self.context.socket(zmq.SUB)
	self.socket.connect(self.ip % self.port)
	self.socket.setsockopt(zmq.SUBSCRIBE, "PROGRESS")
        self.data_lr = {}
        self.data_lr['progress'] = [listrotate2D(length=params['lrlen']) for i in range(1)]
        self.ax = layout.getax()
        print "Progress Module is initialized with ip: ", self.ip % self.port
        
    def update(self, params, sample):
        t = sample['time'] - params['ts']
        params['cur'] = t # this is used in update()
	tot_progress = 0.0 #Use this to calculate average progress
        tot_received = 0

	#Process a configurable number of updates
        for update_prog_val in range(params['cfg']['numzmqupdates']):
            try:
    		string = self.socket.recv(zmq.NOBLOCK)
		topic, messagedata = string.split()
		tot_progress += float(messagedata)
		print "Received: ", topic, messagedata
                tot_received += 1
	    except:
		continue

	if tot_received == 0:
		avg_progress = 0.0
	else:
		avg_progress = tot_progress / tot_received

        self.data_lr['progress'][0].add(t, avg_progress)
        gxsec = params['gxsec']
        cfg = params['cfg']

        self.ax.cla()
        self.ax.axis([t-gxsec, t, cfg['prgmin'], cfg['prgmax']])

        for t in self.data_lr['progress']:
            x = t.getlistx()
            y = t.getlisty()
            self.ax.plot(x,y,color=params['prgcolors'][0], linestyle='--', label=cfg['appname'])

        self.ax.legend(loc='lower left', prop={'size':9})
        self.ax.set_xlabel('Time [s]')
        self.ax.set_ylabel(cfg['progressmetric'])
        graph_title = "Progress for " + cfg['appname'] + " on (" + params['targetnode'] + ")"
        self.ax.set_title(graph_title)
