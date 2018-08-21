#!/usr/bin/env python

from listrotate import *

from clr_matplot_graphs import *

import zmq, sys, time, inspect

# the class name should match with the module name
class graph_efficiency:
    def __init__(self, params, layout):
        self.npkgs = params['info']['npkgs']
	self.port = int(params['cfg']['port'])
	self.ip = str(params['cfg']['ip'])
        self.context = zmq.Context()
        self.package_idle_power_per_socket = 50.0 #A rough estimate based on empirical observations
	self.socket = self.context.socket(zmq.SUB)
	self.socket.connect(self.ip % self.port)
	self.socket.setsockopt(zmq.SUBSCRIBE, "PROGRESS")
        self.data_lr = {}
        self.data_lr['efficiency'] = [listrotate2D(length=params['lrlen']) for i in range(1)]
        self.ax = layout.getax()
        self.running_avg_list = []
	for i in range(10): self.running_avg_list.append(0.0)

        print "Progress Module is initialized with ip: ", self.ip % self.port
        
    def update(self, params, sample):
        t = sample['time'] - params['ts']
        params['cur'] = t # this is used in update()
	tot_progress = 0.0 #Use this to calculate average progress
        tot_received = 0
        tmppow = 0.0

	#Process a configurable number of updates for progress - this is done to smooth out irregularities to get "general" behavior
        for update_prog_val in range(params['cfg']['numzmqupdates']):
            try:
    		string = self.socket.recv(zmq.NOBLOCK)
		topic, messagedata = string.split()
		tot_progress += float(messagedata)
		#print "Received: ", topic, messagedata
                tot_received += 1
	    except:
		continue

	if tot_received == 0:
		avg_progress = 0.0
	else:
		avg_progress = tot_progress / tot_received
		self.running_avg_list.append(avg_progress)
		self.running_avg_list.pop(0)
		avg_progress = sum(self.running_avg_list)/len(self.running_avg_list)

        for pkgid in range(self.npkgs):
            tmppow += sample['power']['p%d'%pkgid]
            if tmppow < 0:
                print
                print 'WARNING: power is negative. Check %s' % (tmppow, params['cfg']['outputfn'])
                print
                return
            tmplim = sample['powercap']['p%d'%pkgid]


        dynamic_power = tmppow - self.npkgs*self.package_idle_power_per_socket
        efficiency = avg_progress / dynamic_power
        print "Calculated efficiency...", efficiency

        self.data_lr['efficiency'][0].add(t, efficiency)
        gxsec = params['gxsec']
        cfg = params['cfg']

        self.ax.cla()
        self.ax.axis([t-gxsec, t, cfg['effmin'], cfg['effmax']])

        for t in self.data_lr['efficiency']:
            x = t.getlistx()
            y = t.getlisty()
            self.ax.plot(x,y,color=params['prgcolors'][0], linestyle='--', label=cfg['appname'])

        self.ax.legend(loc='lower left', prop={'size':9})
        self.ax.set_xlabel('Time [s]')
        efficiency_definition = cfg['progressmetric'] + ' per watt'
        self.ax.set_ylabel(efficiency_definition)
        graph_title = "Efficiency for " + cfg['appname'] + " on (" + params['targetnode'] + ")"
        self.ax.set_title(graph_title)
